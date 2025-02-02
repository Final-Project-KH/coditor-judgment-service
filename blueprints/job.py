from flask import Blueprint, request
import math

import common
from common import error_response, success_response
import security
from redisutils.repository import job_repository, JOB_MAX_COUNT_EXCEEDED, UNEXPECTED_ERROR, JOB_NOT_FOUND
import coditor
import celeryapp

job_bp = Blueprint('job_bp', __name__)

# -------------------------------------------------
# Before Request Hook
# -------------------------------------------------

@job_bp.before_request
def validate_request():
    # -------------------------------------------------
    # EndPoint 전역 검증
    # -------------------------------------------------

    # 1) 키 검증
    api_key = request.headers.get("X-Api-Key")
    client_id = request.headers.get("X-Client-Id")
    if not (api_key and client_id) or not security.validate_hmac_key(api_key, client_id):
        return error_response("Forbidden", 403)

    # 2) JSON 형식 및 구조 검증 (모든 request에서 JSON 본문이 아니면 400)
    if request.method not in "GET":
        if not common.is_valid_json_request(request):
            return error_response("Request body must be a valid JSON object", 400)


    # -------------------------------------------------
    # 개별 EndPoint 검증
    # -------------------------------------------------

    # 1) /job/create
    if request.path == '/job/create' and request.method == 'POST':
        request_body = request.get_json()
        if not common.validate_required_fields(request_body, '/job/create'):
            return error_response(
                "Request body must contain 'code', 'codeLanguage', 'questionId', and 'userId'",
                400
            )
        testcases = coditor.TESTCASE_DICT.get(str(request_body["questionId"]))
        if not testcases:
            return error_response("Provided value for 'questionId' does not exist", 404)

    # 2) /job/execute
    elif request.path == '/job/execute' and request.method == 'POST':
        request_body = request.get_json()
        if not common.validate_required_fields(request_body, '/job/execute'):
            return error_response(
                "Request body must contain 'userId' and 'jobId'",
                400
            )

    # 3) /job/delete
    elif request.path == '/job/delete' and request.method == 'DELETE':
        request_body = request.get_json()
        if not common.validate_required_fields(request_body, '/job/delete'):
            return error_response(
                "Request body must contain 'userId' and 'jobId'",
                400
            )

    # 4) /job/cancel
    elif request.path == '/job/cancel' and request.method == 'POST':
        request_body = request.get_json()
        if not common.validate_required_fields(request_body, '/job/cancel'):
            return error_response(
                "Request body must contain 'userId' and 'jobId'",
                400
            )

    return None


# -------------------------------------------------
# Route 처리
# -------------------------------------------------

# 1) /job/create
@job_bp.route('/create', methods=['POST'])
def create_job() :
    request_data = request.get_json()
    question_id = str(request_data['questionId'])
    code_language = request_data['codeLanguage']
    code = request_data['code']
    user_id = str(request_data['userId'])

    testcases = coditor.TESTCASE_DICT.get(question_id)
    new_job = common.create_job(question_id, code_language, code, len(testcases))
    new_job_timeout = math.floor(
        len(testcases) * coditor.TESTCASE_TIMEOUT_LIMIT.get(question_id) * 2
    ) # 초 단위로 처리 (int 타입)

    # redis에 데이터를 저장, ttl 설정
    res = job_repository.save(user_id, new_job, new_job_timeout)

    if res == 1:
        return success_response({"jobId": f"{new_job['jobId']}"}, 201)

    elif res == JOB_MAX_COUNT_EXCEEDED:
        return error_response(f"Max job count exceeded for userId = {user_id}", 422)

    elif res == UNEXPECTED_ERROR:
        return error_response("Internal server error", 500)

    return error_response("Unknown server error", 500)

# 2) /job/execute
@job_bp.route('/execute', methods=['POST'])
def execute_job():
    request_data = request.get_json()
    user_id = str(request_data['userId'])
    job_id = request_data['jobId']

    job = job_repository.find_by_user_id_and_job_id(user_id, job_id)

    if not job:
        return error_response(f"Job not found for user_id={user_id} with job_id={job_id}", 404)

    celeryapp.execute_code.delay(user_id, job)
    return success_response({"numOfTestcase": int(job["numOfTestcase"])}, 200)

# 3) /job/delete
@job_bp.route('/delete', methods=['DELETE'])
def delete_job():
    request_data = request.get_json()
    user_id = str(request_data['userId'])
    job_id = request_data['jobId']

    res = job_repository.delete(user_id, job_id)

    if (res == UNEXPECTED_ERROR):
        return error_response("Internal server error", 500)

    return success_response({"result": res}, 200)

# 4) /job/cancel
@job_bp.route('/cancel', methods=['POST'])
def cancel_job():
    request_data = request.get_json()
    user_id = str(request_data['userId'])
    job_id = request_data['jobId']

    res = job_repository.update(user_id, job_id, stop_flag=True)

    if (res == JOB_NOT_FOUND):
        return error_response("Job not found for user_id={user_id} with job_id={job_id}", 404)

    if (res == UNEXPECTED_ERROR):
        return error_response("Internal server error", 500)

    return success_response()