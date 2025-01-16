from flask import Blueprint, request
import math
import json
import common
import validation
import redisutils
import coditor


job_bp = Blueprint('job_bp', __name__)


@job_bp.before_request
def validate_request():
    if request.path == '/create' and request.method == 'POST':
        api_key = request.headers.get("X-Api-Key")
        client_id = request.headers.get("X-Client-Id")

        if not validation.validate_hmac_key(api_key, client_id):
            return json.dumps({"success": False, "error": "Forbidden"}, ensure_ascii=False).encode('utf-8'), 403

        request_body = request.get_json()
        if not request_body or not common.validate_required_fields(request_body):
            return json.dumps({"success": False, "error": "Request body must be a valid JSON and contain the following required fields: 'code', 'codeLanguage', 'questionId', and 'memberId'"}, ensure_ascii=False).encode('utf-8'), 400

        testcases = coditor.TESTCASE_DICT.get(request_body["questionId"])
        if not testcases:
            return json.dumps({"success": False, "error": "Provided value for 'questionId' does not exist"}, ensure_ascii=False).encode('utf-8'), 400


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
    is_saved, code = redisutils.save(member_id, new_job, new_job_timeout)

    if is_saved:
        return json.dumps({"success": True, "jobId": f"{new_job['jobId']}"}, ensure_ascii=False).encode('utf-8'), 201
    elif code == redisutils.MAX_ACTIVE_JOB_COUNT_EXCEEDED:
        return json.dumps({"success": False, "error": f"Max job count exceeded for memberId = {member_id}"}, ensure_ascii=False).encode('utf-8'), 422
    elif code == redisutils.RETRIES_EXCEEDED:
        return json.dumps({"success": False, "error": f"Unknown server error occurred."}, ensure_ascii=False).encode('utf-8'), 500
