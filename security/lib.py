import hmac
import hashlib
import base64
import os
from typing import Optional


def generate_hmac_key(_client_id: str) -> Optional[str]:
    """
    HMAC-SHA256 기반으로 API 키를 생성합니다.

    Args:
        _client_id (str): 사전에 합의된 클라이언트 식별자

    Returns:
        Optional[str]: 생성된 API 키, 실패 시 None
    """
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        print("Unable to get secret key from env file")
        return None

    try:
        message = _client_id.encode('utf-8')
        secret_key = secret_key.encode('utf-8')
        hashed = hmac.new(secret_key, message, hashlib.sha256)
        api_key = base64.urlsafe_b64encode(hashed.digest()).decode('utf-8')
    except Exception as e:
        print(e)
        return None

    return api_key


def validate_hmac_key(received_key: str, received_client_id: str) -> bool:
    """
    요청에 포함된 HMAC 키의 유효성을 검증합니다.

    Args:
        received_key (str): 요청 헤더에서 받은 API 키
        received_client_id (str): 요청 헤더에서 받은 클라이언트 식별자

    Returns:
        bool: 키가 유효하면 True, 아니면 False
    """
    expected_key = generate_hmac_key(received_client_id)
    return hmac.compare_digest(expected_key, received_key)
