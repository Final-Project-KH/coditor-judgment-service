import json
import base64
import subprocess
import common


def execute_with_docker(
    code_language: str,
    code: str,
    testcase: tuple,
    timeout: int,
    memory_limit: int = 128,
    cpu_core_limit: float = 0.5,
):
    # 컨테이너 내부적으로 쓰기 가능한 마운트 경로(파일 쓰기 가능한 경로) 설정
    mount_path = f"/tmp/{common.get_random_string(16)}"

    # 테스트 케이스에서 입력 값만 JSON→Base64 인코딩
    testcase_input_json = json.dumps({"input": testcase[0]}, ensure_ascii=False)
    testcase_input_encoded = base64.b64encode(testcase_input_json.encode("utf-8")).decode("utf-8")

    cmd = [
        "docker", "run", "--rm",  # --rm: 컨테이너가 종료될 때 컨테이너와 관련된 리소스(파일 시스템, 볼륨) 제거
        "--network", "none",  # 네트워크 차단
        "--mount", f"type=tmpfs,destination={mount_path}",  # 쓰기 가능한 tmpfs 지정
        "--read-only",  # 파일 시스템은 기본적으로 읽기 전용
        "--memory", f"{memory_limit}m",
        # 64MB 정도면 간단한 알고리즘 문제는 대부분 해결 가능 => 문자열 조작, 단순 수학 계산, 재귀 깊이가 낮은 문제 등. 128MB ~ 256MB 정도로 잡으면, 조금 더 복잡한 자료구조나, BFS/DFS 같은 탐색 문제도 커버 가능.
        "--cpus", f"{cpu_core_limit}",  # CPU 코어 수 제한
        "--pids-limit", "30",  # 생성 가능한 프로세스 상한, 10 ~ 50 정도면 일반적인 자바/파이썬 코드(예: GC 스레드나 내부 스레드 생성)도 무리 없이 실행 가능
        "java-code-runner:v0.0.1",  # docker image 이름

        # container 실행 시 사용할 명령어 커맨드와 전달할 값
        # docker file의 초기 명령어 설정은 아래 명령어로 overwrite 됨
        "python", "/src/app.py",
        code,
        mount_path,
        testcase_input_encoded
    ]

    response = {}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        response["success"] = False
        response["error"] = f"실행 시간 {timeout}s 초과"
        return response

    # 컴파일 에러나 런타임 에러일 경우, stdout에서 에러 메시지 return
    if proc.returncode != 0:
        response["success"] = False
        if "Compile" in proc.stdout:
            response["error"] = f"컴파일 실패"
            response["detail"] = proc.stdout[proc.stdout.find("\n") + 1:]
        elif "Runtime" in proc.stdout:
            response["error"] = f"런타임 에러"
            response["detail"] = proc.stdout[proc.stdout.find("\n") + 1:]
        else:
            response["error"] = "예상치 못한 에러 발생"
            print(f'In Docker.. 반환 코드: {proc.returncode}')
            print(f'In Docker.. stdout: {proc.stdout}')
            print(f'In Docker.. stderr: {proc.stderr}')
        return response

    # 정상 종료
    outputs = proc.stdout.split('\n')
    # outputs[1]: 실제 실행 결과
    # outputs[2]: memoryUsage
    # outputs[3]: runningTime
    # outputs[4]: codeSize

    is_success = (testcase[1] == outputs[1]) if len(outputs) > 1 else False
    response["success"] = is_success
    if len(outputs) > 1:
        response["result"] = outputs[1]
    if len(outputs) > 2:
        response["memoryUsage"] = outputs[2]
    if len(outputs) > 3:
        response["runningTime"] = outputs[3]
    if len(outputs) > 4:
        response["codeSize"] = outputs[4]

    return response