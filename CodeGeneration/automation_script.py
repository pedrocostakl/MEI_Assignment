import subprocess
import time
import requests
import os
import signal
from radon.complexity import cc_visit
from radon.metrics import mi_visit

BASE_URL = "http://127.0.0.1:8000"

# ----------------------
# SERVER CONTROL
# ----------------------
def start_server(code_dir):
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--port", "8000"],
        cwd=code_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)
    return process

def stop_server(process):
    process.send_signal(signal.SIGINT)
    process.wait()

# ----------------------
# COMPLEXITY
# ----------------------
def analyze_code(file_path):
    with open(file_path, "r") as f:
        code = f.read()

    complexity = cc_visit(code)
    maintainability = mi_visit(code, True)

    avg_complexity = sum(c.complexity for c in complexity) / len(complexity) if complexity else 0

    return {
        "avg_complexity": avg_complexity,
        "maintainability_index": maintainability,
        "lines_of_code": len(code.splitlines())
    }

# ----------------------
# TEST ENDPOINTS
# ----------------------
def test_endpoints():
    results = {}
    start_time = time.time()

    try:
        # EASY
        r = requests.post(f"{BASE_URL}/students", json={
            "name": "Alice",
            "email": "alice@test.com",
            "enrollment_year": 2024
        })
        assert r.status_code in [200, 201]
        student_id = r.json().get("id")

        r = requests.get(f"{BASE_URL}/students/{student_id}")
        assert r.status_code == 200

        # MEDIUM
        r = requests.post(f"{BASE_URL}/courses", json={
            "title": "Math",
            "credits": 5,
            "professor_id": 1
        })
        assert r.status_code in [200, 201]
        course_id = r.json().get("id")

        r = requests.post(f"{BASE_URL}/enrollments", json={
            "student_id": student_id,
            "course_id": course_id
        })
        assert r.status_code in [200, 201]

        # HARD
        r = requests.get(f"{BASE_URL}/courses/{course_id}/students")
        assert r.status_code == 200

        r = requests.get(f"{BASE_URL}/courses/{course_id}/average-grade")
        assert r.status_code == 200

        end_time = time.time()

        results["success"] = True
        results["latency"] = end_time - start_time

    except Exception as e:
        results["success"] = False
        results["error"] = str(e)

    return results

# ----------------------
# MAIN
# ----------------------
def evaluate(code_dir):
    results = {}

    results["complexity"] = analyze_code(os.path.join(code_dir, "main.py"))

    process = start_server(code_dir)

    try:
        results["functional"] = test_endpoints()
    finally:
        stop_server(process)

    return results


if __name__ == "__main__":
    results = evaluate("./generated_api")
    print(results)