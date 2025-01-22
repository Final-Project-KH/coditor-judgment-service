# celeryapp/tasks.py
from celery import Celery
import os
from dotenv import load_dotenv

from redisutils.connection import RedisConnectionError
from redisutils.repository import JobRepository, JOB_NO_LONGER_EXISTS, UNEXPECTED_ERROR
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

# JobRepository 로드
try:
    job_repository = JobRepository()
except RedisConnectionError as e:
    print(e)
    exit(1)

# task에 매개변수를 전달하는 경우, 콜백 함수는 self를 인자로 받아야 한다.
@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def execute_code(self, member_id: str, job: dict):
    """
    Celery 작업: 코드를 실행하고 상태를 업데이트합니다.

    Args:
        member_id (str): 회원 ID (PK)
        job (dict): 실행할 작업 정보
    """
    job_id = job['jobId']
    question_id = job['jobInfo']['questionId']
    code_language = job['jobInfo']['codeLanguage']
    code = job['jobInfo']['code']

    testcases = coditor.TESTCASE_DICT[question_id]
    timeout = coditor.TESTCASE_TIMEOUT_LIMIT[question_id]

    curr_testcase_index = 1
    test_results = []

    print(f"Starting job {job_id}...")
    for tc in testcases:
        latest_job = job_repository.find_by_member_id_and_job_id(member_id, job_id)
        if not latest_job:
            pass
        if latest_job['stopFlag'] == 'true':
            print('[INFO] Stop flag raised')
            job_repository.delete(member_id, job_id)
            send_request(EXECUTE_JOB_CALLBACK_ENDPOINT, {"success": False, "error": f"작업이 성공적으로 중단되었습니다."})
            return

        test_result_dict = coditor.execute_with_docker(code_language, code, tc, timeout)
        if test_result_dict.get("error") and test_result_dict.get("error").contains("예상치 못한 에러 발생"):
            print('[INFO] Unexpected error occurred in docker container. Task will die soon.')
            send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                         {"success": False, "error": "코드 실행 중 예상치 못한 오류가 발생했습니다. 관리자에게 문의 바랍니다."})
            job_repository.delete(member_id, job_id)
            return


        test_result_dict['testcaseIndex'] = curr_testcase_index
        test_results.append(test_result_dict)

        update_res = job_repository.update(member_id, job_id,
                              last_testcase_index=curr_testcase_index,
                              results=test_results,
                              status='complete' if curr_testcase_index == len(testcases) else 'inProgress')

        if update_res == JOB_NO_LONGER_EXISTS :
            send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                         {"success": False, "error": "작업이 만료되었습니다. 다시 시도해주세요. 이 경고가 반복될 경우 관리자에게 문의 바랍니다."})
            return

        elif update_res == UNEXPECTED_ERROR:
            callback_response_code = send_request(EXECUTE_JOB_CALLBACK_ENDPOINT,
                         {"success": False, "error": "실행 결과를 업데이트 하는 과정에서 예상치 못한 오류가 발생했습니다. 다시 시도해주세요. 이 경고가 반복될 경우 관리자에게 문의 바랍니다."})
            if callback_response_code != 200:
                print(f"[INFO] No one can receive this result. Task will die soon. Status code: {callback_response_code}")
                job_repository.delete(member_id, job_id)
            return

        test_result_dict['jobId'] = job_id
        test_result_dict['memberId'] = member_id

        callback_response_code = send_request(EXECUTE_JOB_CALLBACK_ENDPOINT, test_result_dict)
        if callback_response_code != 200:
            print(f"[INFO] No one can receive this result. Task will die soon. Status code: {callback_response_code}")
            job_repository.delete(member_id, job_id)
            return

        curr_testcase_index += 1

    print(f"Job {job_id} complete successfully...")
