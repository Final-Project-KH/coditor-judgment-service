# redisutils/connection.py
import redis
import time
from typing import Any, Callable

from .config import load_redis_config

MAX_RETRIES = 3
RETRIES_EXCEEDED = -159

class RedisConnectionError(Exception):
    """Redis 연결 실패에 대한 사용자 정의 예외."""
    pass

class RedisConnection:
    """
    Redis와의 연결을 관리하고,
    재시도(retry) 로직을 캡슐화하여 제공하는 래퍼(Wrapper) 클래스.
    """
    def __init__(self):
        # Redis Client 초기화를 위한 설정 값 load
        self._config = load_redis_config()

        # Redis API를 제공하는 Redis Client 객체
        self._client = None
        self._connect()

    def _connect(self):
        """실제 redis.StrictRedis 객체 생성 & ping 테스트."""
        try:
            client = redis.StrictRedis(
                host=self._config.host,
                port=self._config.port,
                password=self._config.password,
                db=self._config.db
            )
            # 연결 테스트
            client.ping()

            print("[INFO] Successfully connected to Redis!")
            self._client = client

        except redis.exceptions.AuthenticationError as e:
            raise RedisConnectionError(f"Redis authentication failed: {e}")
        except redis.exceptions.RedisError as e:
            raise RedisConnectionError(f"Failed to connect to Redis: {e}")
        except Exception as e:
            raise RedisConnectionError(f"Unexpected error during Redis initialization: {e}")

    @property
    def client(self) -> redis.StrictRedis:
        """
        외부에서 'redis_conn.client' 로 접근 시,
        내부적으로 connect()가 보장된 후 실제 클라이언트를 반환.
        """
        if self._client is None:
            self._connect()
        return self._client

    # kwargs는 args와 같이 쓸 경우, args 뒤에 와야함
    # args는 연속된 변수를 tuple에 순서대로 담고
    # kwargs는 keyword=value와 같이 주어진 값을 하나의 dict로 변환 묶어 다루도록 해줌
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        실제 Redis I/O 작업을 재시도하며 실행하는 메서드.
        - func: 실행할 함수 (예: self.client.get, self.client.setex 등)
        - args, kwargs: 함수에 전달될 인자
        """

        # 재시도 간격 (단위: 초)
        retry_interval = 0.5
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"[execute_with_retry][Attempt {attempt}/{MAX_RETRIES}] Unexpected error: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(retry_interval)
                    retry_interval *= 2
                else:
                    raise  # 최종 실패 시 func에서 발생한 예외를 그대로 throw -> 상위에서 처리
