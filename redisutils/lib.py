# redisutils/lib.py
import uuid
import datetime
import pytz
import json
import time
import redis
import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv


MAX_ACTIVE_JOB_COUNT_EXCEEDED = -1
RETRIES_EXCEEDED = -2
REDIS_CLIENT_IS_NOT_INITIALIZED = -3

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


def get_redis_client() -> Optional[redis.client.Redis]:
    # read-only인 경우 global 키워드 필요 없음
    return _redis_client


def create_job(
    question_id: str,
    code_language: str,
    code: str,
    num_of_testcase: int
) -> Optional[dict]:
    """
    새로운 job 딕셔너리를 생성합니다.

    Args:
        question_id (str): 코딩 테스트 문제 ID
        code_language (str): 코드 언어
        code (str): 코드 본문
        num_of_testcase (int): 총 테스트 케이스 수

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

    new_job = {
        "jobId": str(uuid.uuid4()),
        "jobInfo": {
            "questionId": question_id,
            "codeLanguage": code_language,
            "code": code
        },
        "totalTestcases": str(num_of_testcase),
        "currentTestcase": str(0),
        "status": "ready",
        "stopFlag": str(False),
        "createdAt": now_in_seoul.isoformat(),
        "results": []
    }
    return new_job


def find_by_member_id(
    member_id: str,
    max_retries: int = 5
) -> Tuple[bool, List[dict]]:
    """
    member_id와 관련된 모든 job 데이터를 조회합니다.

    Args:
        member_id (str): 회원 ID (PK)
        max_retries (int): 최대 재시도 횟수 (기본 값: 5)

    Returns:
        (bool, List[dict]): (성공 여부, job 리스트)
    """
    if _redis_client is None:
        print("Fetching data failed cause Redis client is not initialized.")
        return False, []

    # member_id에 해당하는 key 패턴
    pattern = f"{member_id}:*"

    for attempt in range(1, max_retries + 1):
        try:
            # pattern에 해당하는 키 검색
            keys = list(_redis_client.scan_iter(pattern))
            jobs = []
            for key in keys:
                job_data = _redis_client.get(key)
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


def save(
    member_id: str,
    job: dict,
    timeout: int,
    max_active_jobs: int = 2,
    max_retries: int = 5
) -> Tuple[bool, int]:
    """
    job 데이터를 저장합니다.
    지정된 member_id로 이미 일정 개수 이상의 job이 등록되어 있으면 저장을 제한합니다.

    Args:
        member_id (str): 회원 ID (PK)
        job (dict): 작업 정보를 담고 있는 dict
        timeout (int): TTL (단위: 초)
        max_active_jobs (int): 한 명의 member가 동시에 등록할 수 있는 최대 job 수
        max_retries (int): 최대 재시도 횟수 (기본 값: 5)

    Returns:
        (bool, code): 성공 여부, 반환 코드
    """
    if _redis_client is None:
        return False, REDIS_CLIENT_IS_NOT_INITIALIZED

    # Redis 키 생성, 검색의 편의를 위해 member_id를 접두사로 사용
    key = f"{member_id}:{job['jobId']}"

    for attempt in range(1, max_retries + 1):
        try:
            success, active_jobs = find_by_member_id(member_id)
            if not success:
                print(f"[Attempt {attempt}/{max_retries}] Could not retrieve existing jobs for member={member_id}.")
                time.sleep(1)
                continue

            if len(active_jobs) >= max_active_jobs:
                print(f"Member ID {member_id} already has {max_active_jobs} or more active jobs.")
                return False, MAX_ACTIVE_JOB_COUNT_EXCEEDED

            # string 타입으로 저장 및 ttl 설정
            _redis_client.setex(key, timeout, json.dumps(job))
            print(f"Successfully saved.\njobId={job['jobId']}")
            return True, 0

        except Exception as e:
            # 기타 예상치 못한 예외 -> 재시도
            print(f"[Attempt {attempt}/{max_retries}] Unexpected error: {e}")
            _redis_client.delete(key)
            time.sleep(1)

    # 최대 재시도 초과 시 실패 처리
    print(f"Failed to complete set and expire operations for member_id: {member_id} after {max_retries} attempts.")
    return False, RETRIES_EXCEEDED
