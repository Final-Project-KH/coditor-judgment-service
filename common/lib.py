import datetime
import uuid
from typing import Optional
import requests
import flask
import pytz
from flask import Response
import random
import string
import json

# -------------------------------------------------
# 헬퍼 함수 목록
# -------------------------------------------------

def validate_required_fields(json_data: dict, endpoint: str) -> bool:
    """
    요청 JSON 데이터에 필수 필드가 모두 존재하는지 검증합니다.
    :param
        json_data: 요청 JSON 데이터
        url: 요청 URL
    :return: 필수 필드가 모두 존재하면 True, 아니면 False
    """
    required_fields = {
        "/job/create": ["code", "codeLanguage", "questionId", "userId"],
        "/job/execute": ["userId", "jobId"],
        "/job/delete": ["userId", "jobId"],
        "/job/cancel": ["userId", "jobId"],
    }

    if not json_data:
        return False

    missing_fields = [field for field in required_fields[endpoint] if json_data.get(field) is None]
    return not missing_fields


def error_response(message: str, http_status: int) -> flask.Response:
    print(f"[DEBUG] {message}")
    response_data = {
        "success": False,
        "error": message
    }
    return _convert_data_to_json_content_type_response(response_data, http_status)


def success_response(data: Optional[dict] = None, http_status: int = 200) -> flask.Response:
    response_data = {"success": True}
    if data:
        response_data.update(data)
    return _convert_data_to_json_content_type_response(response_data, http_status)


def _convert_data_to_json_content_type_response(data: dict, code: int) -> flask.Response:
    response_json = json.dumps(data, ensure_ascii=False)
    response = Response(response_json, status=code, content_type="application/json")
    return response


def is_valid_json_request(request: flask.request) -> bool:
    if not request.is_json:
        return False

    # json 파싱 테스트 (silent=True는 예외 대신 None 반환)
    json_data = request.get_json(silent=True)
    if json_data is None or not isinstance(json_data, dict):
        return False
    return True


def get_random_string(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def create_job(
    question_id: str,
    code_language: str,
    code: str,
    num_of_testcase: int,
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

    job = {
        "jobId": str(uuid.uuid4()),
        "jobInfo": {
            "questionId": question_id,
            "codeLanguage": code_language,
            "code": code
        },
        "numOfTestcase": str(num_of_testcase),
        "lastTestcaseIndex": "0",
        "status": "ready",
        "stopFlag": str(False).lower(),
        "createdAt": now_in_seoul.strftime('%Y-%m-%dT%H:%M:%S'),
        "results": []
    }
    return job


def send_request(url: str, json_payload: dict) -> int:
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=json_payload, headers=headers, timeout=10)

        # HTTP 관련 에러 발생 시 예외 raise
        response.raise_for_status()

        return response.status_code
    except requests.exceptions.RequestException as e:
        return e.response.status_code
