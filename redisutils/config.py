# redisutils/config.py
import os
from dotenv import load_dotenv

class RedisConfig:
    def __init__(self, host: str, port: int, password: str, db: int):
        self.host = host
        self.port =port
        self.password = password
        self.db = db

def load_redis_config() -> RedisConfig:
    load_dotenv() # .env 로드

    redis_host = os.getenv("REDIS_HOST")
    redis_port = os.getenv("REDIS_PORT")
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_db = os.getenv("REDIS_DB")

    if not (redis_host and redis_port and redis_password and redis_db):
        raise ValueError("Unable to load Redis config from environment variables.")

    return RedisConfig(
        host=redis_host,
        port=int(redis_port),
        password=redis_password,
        db=int(redis_db),
    )