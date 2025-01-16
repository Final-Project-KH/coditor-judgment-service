# key_issuer.py
import os
from validation import lib
from dotenv import load_dotenv


# API 키 발급용 유틸
if __name__ == "__main__":
    # .env 파일 로드
    load_dotenv()

    # 환경 변수에서 Secret Key 로드
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set in the environment variables.")

    # CLIENT_ID 로드
    CLIENT_ID = os.getenv("CLIENT_ID_TEST")
    if not CLIENT_ID:
        raise RuntimeError("CLIENT_ID is not set in the environment variables.")

    # HMAC Key 생성
    generated_key = lib.generate_hmac_key(SECRET_KEY, CLIENT_ID)
    print(f"Generated Key for host_id '{CLIENT_ID}': {generated_key}")

    # 생성된 Key가 유효한지 확인
    is_valid = lib.validate_hmac_key(generated_key, CLIENT_ID, SECRET_KEY)
    print(f"Is the generated key valid? {is_valid}")
