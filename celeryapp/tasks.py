# celeryapp/tasks.py
from celery import Celery
import os
from dotenv import load_dotenv

from redisutils.repository import job_repository, JOB_NOT_FOUND, UNEXPECTED_ERROR
from common.lib import send_request
import coditor


# .env 파일 로드
load_dotenv()
REDIS_URL = f'redis://:{os.getenv("REDIS_PASSWORD")}@{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/{os.getenv("REDIS_DB")}'
EXECUTE_JOB_CALLBACK_ENDPOINT = os.getenv("EXECUTE_JOB_CALLBACK_ENDPOINT")

# Celery APP 인스턴스 생성
app = Celery(
    'sasuke', # 실행 할 celery 앱의 이름 설정
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

        testcases = coditor.TESTCASE_DICT[question_id]
        timeout = coditor.TESTCASE_TIMEOUT_LIMIT[question_id]

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

            test_result_dict = coditor.execute_with_docker(code_language, code, tc, timeout)
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

