# redisutils/lib.py
import math
import uuid
import datetime
import pytz
import json
import time
import redis
import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv

import coditor

MAX_ACTIVE_JOB_COUNT_EXCEEDED = -1
RETRIES_EXCEEDED = -2
REDIS_CLIENT_IS_NOT_INITIALIZED = -3
JOB_NOT_FOUND = -4
JOB_NO_LONGER_EXISTS = -5

_redis_client:Optional[redis.client.Redis] = None


def init_redis_client() -> bool:
    """
    Redis 클라이언트를 초기화하고 연결을 확인합니다.

    Returns:
        bool: True면 초기화 성공, False면 실패
    """
    global _redis_client
    if _redis_client is not None: return True

    # .env 파일 로드
    load_dotenv()

    # Redis 설정 로드
    redis_host = os.getenv("REDIS_HOST")
    redis_port = os.getenv("REDIS_PORT")
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_db = os.getenv("REDIS_DB")

    if not (redis_host and redis_port and redis_password and redis_db):
        print("Unable to get redis config value")
        return False

    try:
        # Redis 클라이언트 생성
        redis_client = redis.StrictRedis(
            host=redis_host,
            port=int(redis_port),
            password=redis_password,
            db=int(redis_db),
        )

        # 연결 테스트, Redis 관련 예외 발생 체크
        redis_client.ping()

        print("Successfully connected to Redis!")
        _redis_client = redis_client
        return True

    except redis.exceptions.AuthenticationError as e:
        print(f"Redis authentication failed: Invalid password: {e}")
        return False
    except redis.exceptions.RedisError as e:
        print(f"Failed to connect to Redis: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during Redis initialization: {e}")
        return False


class RedisConnectionError(Exception):
    """Redis 연결 실패에 대한 사용자 정의 예외"""
    pass


def get_redis_client() -> redis.client.Redis:
    if _redis_client is None:
        if not init_redis_client():
            raise RedisConnectionError("Redis 연결 실패. Redis 서버 상태를 확인해주세요.")
    return _redis_client


def create_job(
    question_id: str,
    code_language: str,
    code: str,
    num_of_testcase: int,
    last_testcase_idx: int = 0,
    status: str = 'ready',
    results: Optional[List[Optional[dict]]] = None
) -> Optional[dict]:
    """
    새로운 job 딕셔너리를 생성합니다.

    Args:
        question_id (str): 코딩 테스트 문제 ID
        code_language (str): 코드 언어
        code (str): 코드 본문
        num_of_testcase (int): 총 테스트 케이스 수
        last_testcase_idx (int): 이전에 실행된 테스트 케이스 번호
        status (str):
            - 'ready': job이 새로 등록되고 실행 요청을 기다리는 상태
            - 'inProgress': job이 Celery API를 통해 jobQueue에 등록되고 Celery Worker에 의해 실행이 시작된 상태
            - 'complete'/'stopped'/'internalServerError': 테스트 케이스 실행 완료/중단/에러발생 으로 리소스가 정리되어
                                                          해당 정보를 client에 전달하기 위해 대기 중인 상태
                                                          전달 후 job 목록에서 제거됨
        results (Optional[List[Optional[dict]]]): 테스트 케이스 별 실행 결과 dict가 담긴 list

    Returns:
        dict or None: 생성된 job 정보를 담은 딕셔너리 또는 유효하지 않은 매개변수인 경우 None
    """
    if not (question_id and code_language and code):
        print("Invalid job parameters (question_id/code_language/code).")
        return None

    if num_of_testcase <= 0:
        print("Invalid testcase count.")
        return None

    seoul_tz = pytz.timezone('Asia/Seoul')
    now_in_seoul = datetime.datetime.now(seoul_tz)

    job = {
        "jobId": str(uuid.uuid4()),
        "jobInfo": {
            "questionId": question_id,
            "codeLanguage": code_language,
            "code": code
        },
        "numOfTestcase": str(num_of_testcase),
        "lastTestcaseIdx": str(last_testcase_idx),
        "status": status,
        "stopFlag": str(False),
        "createdAt": now_in_seoul.isoformat(),
        "results": results if results is not None else []
    }
    return job


def find_by_member_id(
    redis_client: redis.client.Redis,
    member_id: str,
    max_retries: int = 3
) -> Tuple[bool, List[dict]]:
    """
    member_id와 관련된 모든 job 데이터를 조회합니다.

    Args:
        redis_client (redis.client.Redis): Redis 통신을 위한 클라이언트 객체
        member_id (str): 회원 ID (PK)
        max_retries (int): 최대 재시도 횟수 (기본 값: 3)

    Returns:
        (bool, List[dict]): (성공 여부, job 리스트)
    """
    if redis_client is None:
        print("Fetching data failed cause Redis client is not initialized.")
        return False, []

    # member_id에 해당하는 key 패턴
    pattern = f"{member_id}:*"

    for attempt in range(1, max_retries + 1):
        try:
            # pattern에 해당하는 키 검색
            keys = list(redis_client.scan_iter(pattern))
            jobs = []
            for key in keys:
                job_data = redis_client.get(key)
                if job_data:
                    jobs.append(json.loads(job_data.decode("utf-8")))
            return True, jobs

        except Exception as e:
            print(f"[Attempt {attempt}/{max_retries}] Unexpected error: {e}")
            # 재시도 간 대기
            time.sleep(1)

    # 최대 재시도 초과 시 실패 처리
    print(f"Failed to fetch data for member_id: {member_id} after {max_retries} attempts.")
    return False, []


def find_by_member_id_and_job_id(
    redis_client: redis.client.Redis,
    member_id: str,
    job_id: str,
    max_retries: int = 3
) -> Tuple[bool, Optional[dict], int]:
    """
    member_id와 job_id를 이용해 Redis에 저장된 job을 조회합니다

    Args:
        redis_client (redis.client.Redis): Redis 통신을 위한 클라이언트 객체
        member_id (str): 회원 ID (PK)
        job_id (str): 조회할 job의 ID
        max_retries (int): 최대 재시도 횟수 (기본 값: 3)

    Returns:
        (bool, dict or None, int):
            - (True, jobInfo dict, 0): 조회 성공 및 해당 job 반환
            - (False, None, failure_error_code): 조회 실패 또는 job이 존재하지 않음
    """
    if redis_client is None:
        print("Fetching data failed cause Redis client is not initialized.")
        return False, None, REDIS_CLIENT_IS_NOT_INITIALIZED

    key = f"{member_id}:{job_id}"

    for attempt in range(1, max_retries + 1):
        try:
            job_data = redis_client.get(key)
            if not job_data:
                print(f"Job not found for member_id={member_id} with job_id={job_id}")
                return False, None, JOB_NOT_FOUND

            job_dict = json.loads(job_data.decode("utf-8"))
            return True, job_dict, 0

        except Exception as e:
            print(f"[Attempt {attempt}/{max_retries}] Unexpected error: {e}")
            time.sleep(1)

    print(f"Failed to fetch job info for member_id={member_id} with job_id={job_id} after {max_retries} attempts.")
    return False, None, RETRIES_EXCEEDED


def save(
    redis_client: redis.client.Redis,
    member_id: str,
    job: dict,
    timeout: int,
    max_active_jobs: int = 2,
    max_retries: int = 3
) -> Tuple[bool, int]:
    """
    job 데이터를 저장합니다.
    지정된 member_id로 이미 일정 개수 이상의 job이 등록되어 있으면 저장을 제한합니다.

    Args:
        redis_client (redis.client.Redis): Redis 통신을 위한 클라이언트 객체
        member_id (str): 회원 ID (PK)
        job (dict): 작업 정보를 담고 있는 dict
        timeout (int): TTL (단위: 초)
        max_active_jobs (int): 한 명의 member가 동시에 등록할 수 있는 최대 job 수
        max_retries (int): 최대 재시도 횟수 (기본 값: 3)

    Returns:
        (bool, code): 성공 여부, 반환 코드
    """
    if redis_client is None:
        return False, REDIS_CLIENT_IS_NOT_INITIALIZED

    # Redis 키 생성, 검색의 편의를 위해 member_id를 접두사로 사용
    key = f"{member_id}:{job['jobId']}"

    for attempt in range(1, max_retries + 1):
        try:
            success, active_jobs = find_by_member_id(redis_client, member_id)
            if not success:
                print(f"[Attempt {attempt}/{max_retries}] Could not retrieve existing jobs for member={member_id}.")
                time.sleep(1)
                continue

            if len(active_jobs) >= max_active_jobs:
                print(f"Member ID {member_id} already has {max_active_jobs} or more active jobs.")
                return False, MAX_ACTIVE_JOB_COUNT_EXCEEDED

            # string 타입으로 저장 및 ttl 설정
            redis_client.setex(key, timeout, json.dumps(job))
            print(f"Successfully saved.\njobId={job['jobId']}")
            return True, 0

        except Exception as e:
            # 기타 예상치 못한 예외 -> 재시도
            print(f"[Attempt {attempt}/{max_retries}] Unexpected error: {e}")
            redis_client.delete(key)
            time.sleep(1)

    # 최대 재시도 초과 시 실패 처리
    print(f"Failed to complete set and expire operations for member_id: {member_id} after {max_retries} attempts.")
    return False, RETRIES_EXCEEDED


def update_job(
    redis_client: redis.client.Redis,
    member_id: str,
    job_id: str,
    last_testcase_idx: Optional[int] = None,
    status: Optional[str] = None,
    results: Optional[List[Optional[dict]]] = None,
    max_retries: int = 3
) -> Tuple[bool, int]:
    success, job, code = find_by_member_id_and_job_id(redis_client, member_id, job_id)

    if not success:
        return False, code

    # 필요한 항목만 업데이트
    if last_testcase_idx is not None:
        job['lastTestcaseIdx'] = str(last_testcase_idx)

    if status is not None:
        job['status'] = status

    if results is not None:
        job['results'] = results

    key = f"{member_id}:{job['jobId']}"
    job_str = json.dumps(job)

    for attempt in range(1, max_retries + 1):
        try:
            # 기존 키의 TTL 조회
            # 0 이상 양수면 해당 초만큼 남음
            # -1 이면 TTL 없음 (expire가 설정되지 않음)
            # -2 이면 키가 존재하지 않음
            ttl_value = redis_client.ttl(key)
            if ttl_value == -2:
                # 업데이트 중에 키가 만료되었거나 Redis 장애 발생 -> 즉시 종료
                print(f"[update_job] Job={key} no longer exists")
                return False, JOB_NO_LONGER_EXISTS

            if ttl_value > 0:
                redis_client.setex(key, ttl_value, job_str)
            else:
                # ttl_value == -1 -> TTL이 없는 경우, 새로 할당
                question_timeout = coditor.TESTCASE_TIMEOUT_LIMIT.get(job['jobInfo']['questionId'])
                testcase_count = int(job['numOfTestcase'])
                remaining_testcase_count = testcase_count - int(job['lastTestcaseIdx'])
                timeout = math.floor(remaining_testcase_count * question_timeout * 2)
                redis_client.setex(key, timeout, job_str)

            print(f"[update_job] Successfully updated job: {job_id}")
            return True, 0

        except Exception as e:
            print(f"[update_job][Attempt {attempt}/{max_retries}] Unexpected error: {e}")
            # 재시도 전 잠깐 대기
            time.sleep(1)

    print(f"[update_job] Failed to update job for member_id={member_id}, job_id={job_id} after {max_retries} attempts.")
    return False, RETRIES_EXCEEDED
