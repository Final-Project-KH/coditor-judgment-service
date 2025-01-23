# redisutils/repository
import json
from typing import List, Optional, Union, Dict

from .connection import RedisConnection, RedisConnectionError

# 전역 설정 값
MAX_ACTIVE_JOBS_PER_MEMBER = 2

# 에러 코드 정의
UNEXPECTED_ERROR = -1
JOB_MAX_COUNT_EXCEEDED   = -2
JOB_NO_LONGER_EXISTS = -3


class JobRepository:
    """
    Job 도메인과 관련된 Redis CRUD/조회/갱신 로직을 담당하는 클래스.
    """

    def __init__(self):
        self._redis_conn = RedisConnection()

    def find_by_user_id(self, user_id: str) -> List[Optional[Dict]]:
        key_pattern = f"{user_id}:*"
        try:
            # 기본적으로 str 반환, decode 관련 설정을 만지면 bytes 반환 가능
            keys: List[Union[str, bytes]] = list(self._redis_conn.execute_with_retry(
                self._redis_conn.client.scan_iter, key_pattern
            ))
            jobs = []
            for key in keys:
                # 기본적으로 str 반환, 관련 설정을 만지면 bytes 반환 가능, 값이 존재하지 않으면 None
                job_data: Union[str, bytes, None] = self._redis_conn.execute_with_retry(
                    self._redis_conn.client.get, key
                )
                if job_data:
                    if isinstance(job_data, bytes):
                        job_data = job_data.decode("utf-8")
                    jobs.append(json.loads(job_data))
            return jobs

        except Exception as e:
            print(f"[find_by_user_id] Unexpected error: {e}")
            return []

    def find_by_user_id_and_job_id(self, user_id: str, job_id: str) -> Optional[Dict]:
        key = f"{user_id}:{job_id}"
        try:
            # 기본적으로 str 반환, 관련 설정을 만지면 bytes 반환 가능, 값이 존재하지 않으면 None
            job: [str, bytes, None] = self._redis_conn.execute_with_retry(
                self._redis_conn.client.get, key
            )
            if job:
                if isinstance(job, bytes):
                    job = job.decode("utf-8")
                job = json.loads(job)
            return job

        except Exception as e:
            print(f"[find_by_user_id_and_job_id] Unexpected error: {e}")
            return None

    def save(self, user_id: str, job: dict, timeout: int) -> int:
        key = f"{user_id}:{job['jobId']}"
        try:
            if self._is_job_max_count_exceed(user_id):
                return JOB_MAX_COUNT_EXCEEDED

            self._redis_conn.execute_with_retry(
                self._redis_conn.client.setex, key, timeout, json.dumps(job)
            )
            # 코드 흐름에서 1개만 저장되므로
            return 1

        except Exception as e:
            print(f"[save] Unexpected error: {e}")
            return UNEXPECTED_ERROR

    def update(self,
        user_id: str,
        job_id: str,
        stop_flag: Optional[bool] = None,
        last_testcase_index: Optional[int] = None,
        status: Optional[str] = None,
        results: Optional[List] = None
    ) -> int:
        key = f"{user_id}:{job_id}"
        try:
            job = self.find_by_user_id_and_job_id(user_id, job_id)
            if not job:
                return JOB_NO_LONGER_EXISTS

            # 기존 키의 TTL 조회
            ttl_value = self._redis_conn.execute_with_retry(
                self._redis_conn.client.ttl, key
            )

            # ttl_value가 -2이면 키가 존재하지 않음
            if ttl_value == -2:
                return JOB_NO_LONGER_EXISTS

            # 필요한 항목만 업데이트
            if stop_flag is not None:
                job['stopFlag'] = str(stop_flag).lower()

            if last_testcase_index is not None:
                job['lastTestcaseIndex'] = str(last_testcase_index)

            if status is not None:
                job['status'] = status

            if results is not None:
                job['results'] = results

            # ttl_value가 양수이면, 초(sec)를 의미
            if ttl_value > 0:
                self._redis_conn.execute_with_retry(
                    self._redis_conn.client.setex, key, ttl_value, json.dumps(job)
                )
                # 코드 흐름에서 1개만 업데이트 되므로
                return 1

            # ttl_value가 -1이면 ttl 설정되지 않은 상태 -> 로직상에서는 존재 할 수 없음
            # 그 외에는 알 수 없는 상태
            else:
                print(f"[update] Unknown job state. job={job}")
                self.delete(user_id, job_id)
                return UNEXPECTED_ERROR

        except Exception as e:
            print(f"[update] Unexpected error: {e}")
            return UNEXPECTED_ERROR

    def delete(self, user_id: str, job_id: str) -> int:
        key = f"{user_id}:{job_id}"
        try:
            result = self._redis_conn.execute_with_retry(
                self._redis_conn.client.delete, key
            )
            return result

        except Exception as e:
            print(f"[save] Unexpected error: {e}")
            return UNEXPECTED_ERROR

    def _is_job_max_count_exceed(self, user_id: str) -> bool:
        active_jobs = self.find_by_user_id(user_id)
        return len(active_jobs) >= MAX_ACTIVE_JOBS_PER_MEMBER

try:
    job_repository = JobRepository()
except RedisConnectionError as e:
    print(e)
    exit(1)