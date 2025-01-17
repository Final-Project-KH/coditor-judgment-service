# celeryapp/tasks.py
from celery import Celery
import os
from dotenv import load_dotenv
import coditor
import redisutils


# .env 파일 로드
load_dotenv()

# Redis URL 설정
redis_url = os.getenv('REDIS_URL', f'redis://:{os.getenv("REDIS_PASSWORD")}@{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/{os.getenv("REDIS_DB")}')

app = Celery(
    'sasuke', # 실행 할 celery 앱의 이름 설정
    broker=redis_url,
    backend=redis_url
)

app.conf.broker_connection_retry_on_startup = True


# task에 매개변수를 전달하는 경우, 콜백 함수는 self를 인자로 받아야 한다.
@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def execute_code(self, member_id, job):
    """
    Celery 작업: 코드를 실행하고 상태를 업데이트합니다.

    Args:
        member_id (str): 회원 ID (PK)
        job (dict): 실행할 작업 정보
    """
    print(job)
    job_id = job['jobId']
    question_id = job['jobInfo']['questionId']
    code_language = job['jobInfo']['codeLanguage']
    code = job['jobInfo']['code']
    testcases = coditor.TESTCASE_DICT[question_id]
    curr_testcase_idx = 1

    print(f"Starting job {job_id}...")
    redisutils.update_job(redisutils.get_redis_client(), member_id, job_id, curr_testcase_idx, 'inProgress')

    success, updated_job, return_code = redisutils.find_by_member_id_and_job_id(redisutils.get_redis_client(), member_id, job_id)
    print(updated_job)