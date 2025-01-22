from flask import Blueprint, request

from redisutils.repository import JobRepository

test_bp = Blueprint('test_bp', __name__)
job_repository = JobRepository()

# 단위 테스트
# Celery JOB 실행 및 결과 수신
@test_bp.route('/send-result', methods=['POST'])
def test() :
    request_data = request.get_json()
    print(request_data)
    return "", 200

# 단위 테스트
# Celery JOB 중단 및 결과 수신
@test_bp.route('/stop', methods=['POST'])
def stop():
    request_data = request.get_json()
    code = job_repository.update(request_data['memberId'], request_data['jobId'], stop_flag=True)
    print(code)
    return "", 200
