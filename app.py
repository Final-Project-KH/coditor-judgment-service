from flask import Flask, request
import coditor


# 초기화 시에 필수 입력 매개변수는 import_name 으로, Flask 애플리케이션의 패키지나 모듈(소스 파일) 이름을 지정한다.
# Flask(__name__)는 현재 파일(app.py)을 기준으로 경로를 설정하도록 함
# 이 초기화 방식은 Flask는 현재 모듈이 어디에서 실행되는지 자동으로 파악할 수 있음
app = Flask(__name__)

@app.route("/execute-code", methods=['POST'])
def execute_code():
    request_body = request.json
    question_id = request_body["question_id"]
    encoded_code = request_body["code"]

    if question_id in []:
        # 문제 종류에 따라 자원 조정이 필요한 경우
        pass

    # run 함수는 아래 3개 값이 default 매개변수로 설정되어 있습니다.
    # memory_limit = 128
    # cpu_core_limit = 0.5
    # timeout = 5
    return coditor.execute(encoded_code)

if __name__ == '__main__':
    app.run()

"""


######### 테스트용 sample (두 정수의 덧셈) #########
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
