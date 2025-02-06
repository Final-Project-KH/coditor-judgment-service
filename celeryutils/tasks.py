# celeryutils/tasks.py
from celery import Celery
import os
from dotenv import load_dotenv
import json
import base64
import subprocess

from redisutils.repository import job_repository, JOB_NOT_FOUND, UNEXPECTED_ERROR
from common.lib import send_request, get_random_string
from constant.testcases import TESTCASE_DICT, TESTCASE_TIMEOUT_LIMIT


# .env 파일 로드
load_dotenv()
REDIS_URL = f'redis://:{os.getenv("REDIS_PASSWORD")}@{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/{os.getenv("REDIS_DB")}'
EXECUTE_JOB_CALLBACK_ENDPOINT = os.getenv("EXECUTE_JOB_CALLBACK_ENDPOINT")

# Celery APP 인스턴스 생성
app = Celery(
    'sasuke', # 실행 할 celeryutils 앱의 이름 설정
    broker=REDIS_URL,
    backend=REDIS_URL
)
app.conf.broker_connection_retry_on_startup = True

# task에 매개변수를 전달하는 경우, 콜백 함수는 self를 인자로 받아야 한다.
@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def execute_code(self, user_id: str, job: dict):
    """
    Celery 작업: 코드를 실행하고 상태를 업데이트합니다.

    Args:
        user_id (str): 회원 ID (PK)
        job (dict): 실행할 작업 정보
    """
    try:
        job_id = job['jobId']
        question_id = job['jobInfo']['questionId']
        code_language = job['jobInfo']['codeLanguage']
        code = job['jobInfo']['code']
        created_at = job['createdAt']

        testcases = TESTCASE_DICT[question_id]
        timeout = TESTCASE_TIMEOUT_LIMIT[question_id]

        curr_testcase_index = 1
        test_results = []

        print(f"[Starting job {job_id}...]")
        for tc in testcases:
            latest_job = job_repository.find_by_user_id_and_job_id(user_id, job_id)
            if not latest_job:
                pass
            if latest_job['stopFlag'] == 'true':
                print(f'[Stop flag raised for job {job_id}...]')
                job_repository.delete(user_id, job_id)
                send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                             {"success": True, "jobId": job_id, "detail": f"작업이 성공적으로 중단되었습니다."})
                return

            test_result_dict = execute_with_docker(code_language, code, tc, timeout)
            if test_result_dict.get("error") and "예상치 못한 에러 발생" in test_result_dict.get("error"):
                print(f'[Unexpected error occurred in docker container. Task will die soon for job {job_id}...]')
                job_repository.delete(user_id, job_id)
                send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                             {"success": False, "jobId": job_id,
                              "error": "코드 실행 과정에서 예상치 못한 오류가 발생했습니다. 관리자에게 문의 바랍니다."})
                return

            test_result_dict['testcaseIndex'] = curr_testcase_index
            test_results.append(test_result_dict)

            update_res = job_repository.update(user_id, job_id,
                                               last_testcase_index=curr_testcase_index,
                                               results=test_results,
                                               status='complete' if curr_testcase_index == len(
                                                   testcases) else 'inProgress')

            if update_res == JOB_NOT_FOUND:
                print(f'[Job {job_id} no longer exists. Task will die soon...]')
                send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                             {"success": False, "jobId": job_id,
                              "error": "코드 실행 작업이 만료되었습니다. 다시 시도해주세요. 이 경고가 반복될 경우 관리자에게 문의 바랍니다."})
                return

            elif update_res == UNEXPECTED_ERROR:
                print(f'[Unexpected error occurred during update job {job_id}. Task will die soon...]')
                job_repository.delete(user_id, job_id)
                send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                             {"success": False, "jobId": job_id,
                              "error": "코드 실행 결과를 업데이트 하는 과정에서 예상치 못한 오류가 발생했습니다. 다시 시도해주세요. 이 경고가 반복될 경우 관리자에게 문의 바랍니다."})
                return

            test_result_dict['jobId'] = job_id
            test_result_dict['userId'] = user_id

            print(f"[Testcase {curr_testcase_index} for job {job_id} successfully executed]")
            callback_response_code = send_request(EXECUTE_JOB_CALLBACK_ENDPOINT, test_result_dict)
            if callback_response_code != 200:
                print(
                    f"[No one can receive this result. Task will die soon for job {job_id}. Status code: {callback_response_code}]")
                job_repository.delete(user_id, job_id)
                return

            curr_testcase_index += 1

        print(f"[Job {job_id} complete successfully...]")
        success_all = True
        running_time_avg = 0
        memory_usage_avg = 0
        for result in test_results:
            if not result['success']:
                success_all = False
            running_time_avg += int(result['runningTime'])
            memory_usage_avg += float(result['memoryUsage'])

        running_time_avg /= len(test_results)
        memory_usage_avg /= len(test_results)

        callback_response_code = send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                                              {"success": success_all, "userId": user_id, "jobId": job_id,
                                               "questionId": question_id, "code": code, "codeLanguage": code_language,
                                               "codeSize": test_result_dict['codeSize'], "createdAt": created_at, "detail": "complete",
                                               "memoryUsage": round(memory_usage_avg, 2), "runningTime": round(running_time_avg)})
        if callback_response_code != 200:
            print(
                f"[No one can receive this result. Task will die soon for job {job_id}. Status code: {callback_response_code}]")
            job_repository.delete(user_id, job_id)
            return
    except Exception as e:
        print(e)
        job_repository.delete(user_id, job_id)
        send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                     {"success": False, "jobId": job_id,
                      "error": "코드 실행 과정에서 예상치 못한 오류가 발생했습니다. 관리자에게 문의 바랍니다."})


def execute_with_docker(
    code_language: str,
    code: str,
    testcase: tuple,
    timeout: int,
    memory_limit: int = 128,
    cpu_core_limit: float = 0.5,
):
    # 컨테이너 내부적으로 쓰기 가능한 마운트 경로(파일 쓰기 가능한 경로) 설정
    mount_path = f"/tmp/{get_random_string(16)}"

    # 테스트 케이스에서 입력 값만 JSON→Base64 인코딩
    testcase_input_json = json.dumps({"input": testcase[0]}, ensure_ascii=False)
    testcase_input_encoded = base64.b64encode(testcase_input_json.encode("utf-8")).decode("utf-8")

    cmd = [
        "docker", "run", "--rm",  # --rm: 컨테이너가 종료될 때 컨테이너와 관련된 리소스(파일 시스템, 볼륨) 제거
        "--network", "none",  # 네트워크 차단
        "--mount", f"type=tmpfs,destination={mount_path}",  # 쓰기 가능한 tmpfs 지정
        "--read-only",  # 파일 시스템은 기본적으로 읽기 전용
        "--memory", f"{memory_limit}m",
        # 64MB 정도면 간단한 알고리즘 문제는 대부분 해결 가능 => 문자열 조작, 단순 수학 계산, 재귀 깊이가 낮은 문제 등. 128MB ~ 256MB 정도로 잡으면, 조금 더 복잡한 자료구조나, BFS/DFS 같은 탐색 문제도 커버 가능.
        "--cpus", f"{cpu_core_limit}",  # CPU 코어 수 제한
        "--pids-limit", "30",  # 생성 가능한 프로세스 상한, 10 ~ 50 정도면 일반적인 자바/파이썬 코드(예: GC 스레드나 내부 스레드 생성)도 무리 없이 실행 가능
        "java-code-runner:v0.0.1",  # docker image 이름

        # container 실행 시 사용할 명령어 커맨드와 전달할 값
        # docker file의 초기 명령어 설정은 아래 명령어로 overwrite 됨
        "python", "/src/app.py",
        code,
        mount_path,
        testcase_input_encoded
    ]

    response = {}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        response["success"] = False
        response["error"] = f"실행 시간 {timeout}s 초과"
        return response

    # 컴파일 에러나 런타임 에러일 경우, stdout에서 에러 메시지 return
    if proc.returncode != 0:
        response["success"] = False
        if "Compile" in proc.stdout:
            response["error"] = f"컴파일 실패"
            response["detail"] = proc.stdout[proc.stdout.find("\n") + 1:]
        elif "Runtime" in proc.stdout:
            response["error"] = f"런타임 에러"
            response["detail"] = proc.stdout[proc.stdout.find("\n") + 1:]
        else:
            response["error"] = "예상치 못한 에러 발생"
            print(f'In Docker.. 반환 코드: {proc.returncode}')
            print(f'In Docker.. stdout: {proc.stdout}')
            print(f'In Docker.. stderr: {proc.stderr}')
        return response

    # 정상 종료
    outputs = proc.stdout.split('\n')
    # outputs[0]: 결과 라인 수
    # outputs[1]~outputs[int(outputs[0])]: 실제 실행 결과
    # outputs[int(outputs[0]) + 1]: memoryUsage
    # outputs[int(outputs[0]) + 2]: runningTime
    # outputs[int(outputs[0]) + 3]: codeSize

    if len(outputs) > 1:
        result = '\n'.join(outputs[1:int(outputs[0]) + 1])  # 첫 번째 라인 이후의 결과들
        response["result"] = result

        if testcase[1] == result:
            response["success"] = True
        else:
            response["success"] = False

    if len(outputs) > int(outputs[0]) + 1:
        response["memoryUsage"] = outputs[int(outputs[0]) + 1]

    if len(outputs) > int(outputs[0]) + 2:
        response["runningTime"] = outputs[int(outputs[0]) + 2]

    if len(outputs) > int(outputs[0]) + 3:
        response["codeSize"] = outputs[int(outputs[0]) + 3]

    print(response)
    return response