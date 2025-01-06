import random
import string
import subprocess
import json


def random_string(length=8):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def execute(encoded_code: str, memory_limit=128, cpu_core_limit=0.5, timeout=5):
    # docker container 내부 랜덤 마운트 경로(파일 쓰기 가능한 경로) 설정
    mount_path = f"/tmp/{random_string(128)}"

    cmd = [
        # --rm: 컨테이너가 종료될 때 컨테이너와 관련된 리소스(파일 시스템, 볼륨) 제거
        "docker", "run", "--rm",

        # 네트워크 차단
        "--network", "none",

        # 쓰기 가능한 tmpfs 지정
        "--mount", f"type=tmpfs,destination={mount_path}",

        # 기본적으로 파일 시스템은 읽기 전용
        "--read-only",

        # memory/cpu 제한
        # 메모리의 경우,
        # 64MB 정도면 간단한 알고리즘 문제는 대부분 해결 가능 => 문자열 조작, 단순 수학 계산, 재귀 깊이가 낮은 문제 등.
        # 128MB ~ 256MB 정도로 잡으면, 조금 더 복잡한 자료구조나, BFS/DFS 같은 탐색 문제도 커버 가능.
        "--memory", f"{memory_limit}m",
        "--cpus", f"{cpu_core_limit}",

        # 프로세스 수 제한
        # 10 ~ 50
        # 10 ~ 30 정도면 일반적인 자바/파이썬 코드(예: GC 스레드나 내부 스레드 생성)도 무리 없이 실행 가능.
        # 코딩 테스트 수준에서는 보통 10~30이면 충분.
        "--pids-limit", "30",

        # 사용할 docker image
        "my-runner:latest",

        # container에 전달할 값
        "python", "/app/app.py",
        encoded_code,
        mount_path
    ]

    response = {}
    try:
        # 일정 시간 초과 시 subprocess.TimeoutExpired 예외 발생
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        response["success"] = False
        response["error"] = f"실행 시간 {timeout}s 초과"
        return json.dumps(response, ensure_ascii=False).encode('utf-8')

    # 컴파일 에러나 런타임 에러일 경우, stdout에서 에러 메시지 return
    if proc.returncode != 0:
        response["success"] = False
        if "Compile" in proc.stdout:
            response["error"] = f"컴파일 실패"
            response["detail"] = proc.stdout[proc.stdout.find("\n")+1:]
        elif "Runtime" in proc.stdout:
            response["error"] = f"런타임 에러"
            response["detail"] = proc.stdout[proc.stdout.find("\n")+1:]
        else:
            response["error"] = "서버에 문제가 발생했습니다. 관리자에게 문의하십시오."
            print(proc.returncode)
            print(proc.stdout)
            print(proc.stderr)
        return json.dumps(response, ensure_ascii=False).encode('utf-8')

    result = proc.stdout.split('\n')
    response["success"] = True
    response["result"] = result[1]
    response["memoryUsage"] = result[2]
    response["runningTime"] = result[3]
    response["codeSize"] = result[4]
    return json.dumps(response, ensure_ascii=False).encode('utf-8')
