from flask import Blueprint, request
import math
import json
import common
import validation
import redisutils
import coditor
import celeryapp


job_bp = Blueprint('job_bp', __name__)


@job_bp.before_request
def validate_request():
    api_key = request.headers.get("X-Api-Key")
    client_id = request.headers.get("X-Client-Id")

    # 1) 키 검증
    if not (api_key and client_id) or not validation.validate_hmac_key(api_key, client_id):
        return "<h1>Forbidden</h1>", 403

    # 2) JSON 형식 검증 (모든 request에서 JSON 본문이 아니면 400)
    #    만약 GET/DELETE 등의 메서드에서는 본문을 강제하지 않는다면, request.method 체크 후 분기하면 됨
    if not request.is_json:
        return json.dumps({
            "success": False,
            "error": "Content-Type must be application/json"
        }, ensure_ascii=False), 400

    # Flask가 body를 JSON으로 파싱해보기 (silent=True는 예외 대신 None 반환)
    json_data = request.get_json(silent=True)

    # json_data가 None이면 파싱 자체가 실패했거나 Body가 비었음
    # json_data가 숫자(345345)나 문자열("hello")처럼 dict가 아니면 에러 처리
    if json_data is None or not isinstance(json_data, dict):
        return json.dumps({
            "success": False,
            "error": "Request body must be a valid JSON object"
        }, ensure_ascii=False), 400

    # 3) 엔드포인트 검증
    if request.path == '/job/create' and request.method == 'POST':
        request_body = request.get_json()
        if not request_body or not common.validate_required_fields(request_body, '/job/create'):
            return json.dumps({"success": False, "error": "Request body must be a valid JSON and contain the following required fields: 'code', 'codeLanguage', 'questionId', and 'memberId'"}, ensure_ascii=False).encode('utf-8'), 400

        testcases = coditor.TESTCASE_DICT.get(request_body["questionId"])
        if not testcases:
            return json.dumps({"success": False, "error": "Provided value for 'questionId' does not exist"}, ensure_ascii=False).encode('utf-8'), 400

    if request.path == '/job/execute' and request.method == 'POST':
        request_body = request.get_json()
        if not request_body or not common.validate_required_fields(request_body, '/job/execute'):
            return json.dumps({"success": False, "error": "Request body must be a valid JSON and contain the following required fields: 'memberId' and 'jobId'"}, ensure_ascii=False).encode('utf-8'), 400

    # 없는 route는 자동으로 404 처리됨
    pass


@job_bp.route('/create', methods=['POST'])
def register_job() :
    request_data = request.get_json()
    question_id = request_data['questionId']
    code_language = request_data['codeLanguage']
    code = request_data['code']
    testcases = coditor.TESTCASE_DICT.get(question_id)

    new_job = redisutils.create_job(question_id, code_language, code, len(testcases))
    new_job_timeout = math.floor(len(testcases) * coditor.TESTCASE_TIMEOUT_LIMIT.get(question_id) * 2) # int, 초 단위로 처리

    # redis에 데이터를 저장, ttl 설정
    member_id = request_data['memberId']
    is_saved, code = redisutils.save(redisutils.get_redis_client(), member_id, new_job, new_job_timeout)

    if is_saved:
        return json.dumps({
            "success": True,
            "jobId": f"{new_job['jobId']}"
        }, ensure_ascii=False).encode('utf-8'), 201

    elif code == redisutils.MAX_ACTIVE_JOB_COUNT_EXCEEDED:
        return json.dumps({
            "success": False,
            "error": f"Max job count exceeded for memberId = {member_id}"
        }, ensure_ascii=False).encode('utf-8'), 422

    elif code == redisutils.REDIS_CLIENT_IS_NOT_INITIALIZED:
        return json.dumps({
            "success": False,
            "error": f"Unexpected server state: Redis client is not initialized, but the server is still running."
        }, ensure_ascii=False).encode('utf-8'), 500

    elif code == redisutils.RETRIES_EXCEEDED:
        return json.dumps({
            "success": False,
            "error": f"Unknown server error occurred."
        }, ensure_ascii=False).encode('utf-8'), 500

    else:
        return "Unknown state", 500


@job_bp.route('/execute', methods=['POST'])
def execute_job():
    request_data = request.get_json()
    member_id = request_data['memberId']
    job_id = request_data['jobId']
    success, job, code = redisutils.find_by_member_id_and_job_id(redisutils.get_redis_client(), member_id, job_id)

    if success:
        celeryapp.execute_code.delay(member_id, job)
        return json.dumps(job, ensure_ascii=False).encode('utf-8'), 200

    elif code == redisutils.REDIS_CLIENT_IS_NOT_INITIALIZED:
        return json.dumps({
            "success": False,
            "error": f"Unexpected server state: Redis client is not initialized, but the server is still running."
        }, ensure_ascii=False).encode('utf-8'), 500

    elif code == redisutils.JOB_NOT_FOUND:
        return json.dumps({
            "success": False,
            "error": f"Job not found for member_id={member_id} with job_id={job_id}"
        }, ensure_ascii=False).encode('utf-8'), 400

    elif code == redisutils.RETRIES_EXCEEDED:
        return json.dumps({
            "success": False,
            "error": f"Unknown server error occurred."
        }, ensure_ascii=False).encode('utf-8'), 500

    else:
        return "Unknown state", 500