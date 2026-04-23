import argparse
import json
import os
import shutil
import signal
import socket
import sqlite3
import subprocess
import time
from pathlib import Path

import requests
from radon.complexity import cc_visit
from radon.metrics import mi_visit

RUNS_DIR = Path(__file__).resolve().parent / "generated_api_runs"

# ----------------------
# SERVER CONTROL
# ----------------------
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server_ready(base_url, process, timeout_seconds=20):
    start = time.time()
    while time.time() - start < timeout_seconds:
        if process.poll() is not None:
            return False
        try:
            response = requests.get(f"{base_url}/docs", timeout=1)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def start_server(code_dir, port):
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--port", str(port)],
        cwd=str(code_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    if not wait_for_server_ready(base_url, process):
        try:
            _, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            stderr = "Timed out while waiting for uvicorn startup logs."
        raise RuntimeError(f"Server did not start in time. Details: {stderr}")
    return process


def stop_server(process):
    if process.poll() is not None:
        return

    try:
        process.send_signal(signal.SIGINT)
        process.wait(timeout=5)
    except Exception:
        process.terminate()
        process.wait(timeout=5)

# ----------------------
# COMPLEXITY
# ----------------------
def analyze_code(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    complexity = cc_visit(code)
    maintainability = mi_visit(code, True)

    avg_complexity = sum(c.complexity for c in complexity) / len(complexity) if complexity else 0

    return {
        "avg_complexity": avg_complexity,
        "maintainability_index": maintainability,
        "lines_of_code": len(code.splitlines())
    }


def prepare_run_directory(input_file):
    input_path = Path(input_file).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    run_id = int(time.time() * 1000)
    run_dir = RUNS_DIR / f"{input_path.stem}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    target_main = run_dir / "main.py"
    shutil.copy2(input_path, target_main)

    return run_dir, input_path


def get_database_path(run_dir):
    db_files = sorted(run_dir.glob("*.db"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not db_files:
        raise RuntimeError("No SQLite database file was created by the input API.")
    return db_files[0]


def seed_professor(db_path):
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "INSERT OR IGNORE INTO professors (id, name, department) VALUES (?, ?, ?)",
            (1, "Dr. Seed", "Computer Science"),
        )
        connection.commit()
    finally:
        connection.close()

# ----------------------
# TEST ENDPOINTS
# ----------------------
def test_endpoints(base_url):
    results = {}
    start_time = time.time()
    unique_token = int(start_time * 1000)

    try:
        # EASY
        r = requests.post(f"{base_url}/students", json={
            "name": "Alice",
            "email": f"alice_{unique_token}@test.com",
            "enrollment_year": 2024
        }, timeout=5)
        assert r.status_code in [200, 201]
        student_id = r.json().get("id")

        r = requests.get(f"{base_url}/students/{student_id}", timeout=5)
        assert r.status_code == 200

        # MEDIUM
        r = requests.post(f"{base_url}/courses", json={
            "title": "Math",
            "credits": 5,
            "professor_id": 1
        }, timeout=5)
        assert r.status_code in [200, 201]
        course_id = r.json().get("id")

        r = requests.post(f"{base_url}/enrollments", json={
            "student_id": student_id,
            "course_id": course_id
        }, timeout=5)
        assert r.status_code in [200, 201]

        # HARD
        r = requests.get(f"{base_url}/courses/{course_id}/students", timeout=5)
        assert r.status_code == 200

        r = requests.get(f"{base_url}/courses/{course_id}/average-grade", timeout=5)
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

    port = get_free_port()
    base_url = f"http://127.0.0.1:{port}"
    process = start_server(code_dir, port)
    db_path = get_database_path(Path(code_dir))
    seed_professor(db_path)

    try:
        results["functional"] = test_endpoints(base_url)
    finally:
        stop_server(process)

    return results


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate generated FastAPI files.")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the generated Python API file (example: ./Gemini_outputs/output1.py)",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional path to save JSON results.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    run_start_time = time.time()
    args = parse_args()
    run_dir, input_path = prepare_run_directory(args.input)
    results = evaluate(run_dir)
    results["execution_time"] = time.time() - run_start_time
    results["input_file"] = str(input_path)
    results["run_directory"] = str(run_dir)

    output_json = json.dumps(results, indent=2)
    print(output_json)

    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json + "\n", encoding="utf-8")