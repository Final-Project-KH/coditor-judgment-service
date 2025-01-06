import base64
from flask import Flask, request, stream_with_context, Response
import json
import coditor


# 초기화 시에 필수 입력 매개변수는 import_name 으로, Flask 애플리케이션의 패키지나 모듈(소스 파일) 이름을 지정한다.
# Flask(__name__)는 현재 파일(app.py)을 기준으로 경로를 설정하도록 함
# 이 초기화 방식은 Flask는 현재 모듈이 어디에서 실행되는지 자동으로 파악할 수 있음
app = Flask(__name__)

def validate_required_fields(json_data) -> bool:
    required_fields = ["code", "language", "questionId"]
    missing_fields = [field for field in required_fields if json_data.get(field) is None]

    if not json_data or missing_fields:
        return False
    return True


@app.route("/execute-code", methods=['POST'])
def execute_code() :
    data = request.get_json()

    if not validate_required_fields(data):
        return json.dumps({"success": False, "error": "Invalid request body format"}, ensure_ascii=False).encode('utf-8'), 400

    code_encoded = data["code"]
    testcases = coditor.java_test_cases.get(data["questionId"])

    # if question_id in []:
    #     # 문제 종류에 따라 자원 조정이 필요한 경우
    #     pass

    # run 함수는 아래 3개 값이 default 매개변수로 설정되어 있습니다.
    # memory_limit = 128
    # cpu_core_limit = 0.5
    # timeout = 5

    @stream_with_context
    def generate():
        # 1) SSE 시작
        yield "event: start\n"
        yield f"data: {json.dumps({'msg': 'test start', 'total': len(testcases)}, ensure_ascii=False)}\n\n"

        # 2) 테스트 케이스를 순차적으로 실행
        for tc in testcases:
            testcase_json = json.dumps({"input": tc[0]}, ensure_ascii=False)
            testcases_encoded = base64.b64encode(testcase_json.encode("utf-8")).decode("utf-8")

            test_result = coditor.execute(code_encoded, testcases_encoded)

            """
                test_result의 result와 tc[1]을 비교하여 성공 실패 처리할 것
            """

            # 테스트 결과 이벤트 전송
            yield "event: testResult\n"
            yield f"data: {json.dumps({'testcase': tc, 'result': test_result}, ensure_ascii=False)}\n\n"

        # 3) 모든 테스트 케이스 완료 후
        yield "event: complete\n"
        yield f"data: {json.dumps({'msg': 'test end'}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run()

"""


######### 답안 제출 코드 sample (java 문제1: 두 정수의 덧셈) #########
public class Main {
    public static void main(String[] args) {
        Solution solution = new Solution();
        int result = solution.solve(4, 6);
        System.out.println(result);
    }
}

class Solution {
    public int solve(int number1, int number2) {
        return number1 + number2;
    }
}

######### 두 정수의 덧셈 코드 base64 encoding 버전 #########
cHVibGljIGNsYXNzIE1haW4gewogICAgcHVibGljIHN0YXRpYyB2b2lkIG1haW4oU3RyaW5nW10gYXJncykgewogICAgICAgIFNvbHV0aW9uIHNvbHV0aW9uID0gbmV3IFNvbHV0aW9uKCk7CiAgICAgICAgaW50IHJlc3VsdCA9IHNvbHV0aW9uLnNvbHZlKDQsIDYpOwogICAgICAgIFN5c3RlbS5vdXQucHJpbnRsbihyZXN1bHQpOwogICAgfQp9CgpjbGFzcyBTb2x1dGlvbiB7CiAgICBwdWJsaWMgaW50IHNvbHZlKGludCBudW1iZXIxLCBpbnQgbnVtYmVyMikgewogICAgICAgIHJldHVybiBudW1iZXIxICsgbnVtYmVyMjsKICAgIH0KfQ==


"""
