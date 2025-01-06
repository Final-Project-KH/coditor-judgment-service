# app.py
import os
import sys
import base64
import subprocess
import time
import resource


def main():
    # 시작 시각 기록
    start_time = time.time()

    if len(sys.argv) < 3:
        msg = (
        "Failed\n"
        "Insufficient arguments provided"
        )
        print(msg)
        sys.exit(-1)

    encoded_code = sys.argv[1]
    mount_path = sys.argv[2]

    # 1) Base64 디코딩
    try:
        code_str = base64.b64decode(encoded_code).decode('utf-8')
    except Exception as e:
        msg = (
        "Failed\n"
        f"Base64 decode error: {str(e)}"
        )
        print(msg)
        sys.exit(-2)

    # 2) 마운트 경로로 이동
    try:
        os.chdir(mount_path)
    except Exception as e:
        msg = (
        "Failed\n"
        f"Changing directory failed: {str(e)}"
        )
        print(msg)
        sys.exit(-3)

    # 3) 자바 파일 생성
    java_filename = "Main.java"
    try:
        with open(java_filename, "w", encoding="utf-8") as f:
            f.write(code_str)
    except Exception as e:
        msg = (
        "Failed\n"
        f"File write error: {str(e)}"
        )
        print(msg)
        sys.exit(-4)

    # 4) 컴파일
    compile_cmd = ["javac", "-encoding", "UTF-8", java_filename]
    proc_compile = subprocess.run(compile_cmd, capture_output=True, text=True)

    if proc_compile.returncode != 0:
        # 메모리 초과 확인
        if proc_compile.returncode == -9 or "Killed" in proc_compile.stderr:
            msg = (
            "Compile failed\n"
            "Out of memory"
            )
            print(msg)
        else:
            msg = (
            "Compile failed\n"
            f"{proc_compile.stderr.strip()}"
            )
            print(msg)
        sys.exit(proc_compile.returncode)

    # 5) 실행 (Main.class)
    run_cmd = ["java", "Main"]
    proc_run = subprocess.run(run_cmd, capture_output=True, text=True)

    if proc_run.returncode != 0:
        msg = (
        "Runtime exception occurred\n"
        f"{proc_run.stderr.strip()}"
        )
        print(msg)
        sys.exit(proc_run.returncode)

    # 6) 정상 실행 시 stdout 출력
    end_time = time.time()
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    memory_mb = usage.ru_maxrss / 1024.0

    msg = (
    "Success\n"
    f"{proc_run.stdout.strip()}\n"
    f"{round(memory_mb, 2)}\n"
    f"{round((end_time - start_time) * 1000)}\n"
    f"{len(code_str)}"
    )
    print(msg)


if __name__ == "__main__":
    main()
