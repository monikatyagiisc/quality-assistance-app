"""Run the evaluation scenarios against a running Quality Assistance backend.

Each scenario is sent once, then replayed in the same session with review
guidance (its "refinements"), which imitates an engineer refining a result.
The script records the response time of every round in results/results.csv and
saves each response under results/responses/. The columns manual_time_h,
human_review_min, accepted_pct and notes are left empty for the reviewer.

Usage, with the backend and agent running (for example via scripts/dev.sh):

    export QA_EVAL_EMAIL=reviewer@example.com
    export QA_EVAL_PASSWORD='choose-a-password'
    python3 evaluation/run_scenarios.py --register --repeat 3
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Heuristic only: counts how many specialist topics appear in the response text.
KEYWORDS = ["test case", "test data", "automation", "execution", "self-healing",
            "change impact", "bug report", "summary", "release readiness"]

COLUMNS = ["timestamp", "scenario", "run", "round", "latency_s", "status", "http_status",
           "session_id", "response_chars", "specialists_mentioned",
           "manual_time_h", "human_review_min", "accepted_pct", "notes"]


def post(url, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, json.dumps(
        payload).encode(), headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        try:
            return error.code, json.loads(body)
        except ValueError:
            return error.code, {"detail": body}


def login(base, email, password, register):
    if register:
        status, body = post(f"{base}/api/auth/register",
                            {"email": email, "password": password, "full_name": "Evaluation Reviewer"})
        if status == 201:
            return body["access_token"]
        if status != 409:
            sys.exit(f"Registration failed ({status}): {body}")
    status, body = post(f"{base}/api/auth/login",
                        {"email": email, "password": password})
    if status != 200:
        sys.exit(f"Login failed ({status}): {body}")
    return body["access_token"]


def main():
    parser = argparse.ArgumentParser(description="Run evaluation scenarios.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--scenarios", default=str(HERE / "scenarios.json"))
    parser.add_argument("--only", nargs="*",
                        help="Scenario ids to run (default: all).")
    parser.add_argument("--repeat", type=int, default=1,
                        help="Runs per scenario.")
    parser.add_argument("--max-rounds", type=int, default=3,
                        help="Rounds per run: the first request plus refinements.")
    parser.add_argument("--register", action="store_true",
                        help="Create the user if missing.")
    args = parser.parse_args()

    email = os.environ.get("QA_EVAL_EMAIL")
    password = os.environ.get("QA_EVAL_PASSWORD")
    if not email or not password:
        sys.exit("Set QA_EVAL_EMAIL and QA_EVAL_PASSWORD in the environment.")

    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    if args.only:
        scenarios = [s for s in scenarios if s["id"] in args.only]
    if not scenarios:
        sys.exit("No scenarios selected.")

    base = args.base_url.rstrip("/")
    token = login(base, email, password, args.register)

    out_dir = HERE / "results"
    (out_dir / "responses").mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "results.csv"
    is_new = not csv_path.exists()

    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        if is_new:
            writer.writeheader()
        for scenario in scenarios:
            for run in range(1, args.repeat + 1):
                session_id = None
                steps = [None] + scenario.get("refinements", [])
                for round_no, guidance in enumerate(steps[: args.max_rounds], start=1):
                    payload = {
                        "requirements": scenario["requirements"],
                        "user_stories": scenario.get("user_stories") or None,
                        "code_diffs": scenario.get("code_diffs") or None,
                        "session_id": session_id,
                        "human_guidance": guidance,
                    }
                    started = time.perf_counter()
                    status, body = post(f"{base}/api/assist", payload, token)
                    latency = time.perf_counter() - started

                    ok = status == 200
                    text = body.get("response", "") if ok else ""
                    if ok:
                        session_id = body.get("session_id", session_id)
                        name = f"{scenario['id']}_run{run}_round{round_no}.md"
                        (out_dir / "responses" /
                         name).write_text(text, encoding="utf-8")

                    writer.writerow({
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "scenario": scenario["id"],
                        "run": run,
                        "round": round_no,
                        "latency_s": f"{latency:.1f}",
                        "status": body.get("status", "") if ok else "error",
                        "http_status": status,
                        "session_id": session_id or "",
                        "response_chars": len(text),
                        "specialists_mentioned": sum(k in text.lower() for k in KEYWORDS),
                        "manual_time_h": "",
                        "human_review_min": "",
                        "accepted_pct": "",
                        "notes": "" if ok else json.dumps(body)[:200],
                    })
                    handle.flush()
                    print(
                        f"{scenario['id']} run {run} round {round_no}: HTTP {status}, {latency:.1f}s")
                    if not ok:
                        break

    print(f"Results written to {csv_path}")


if __name__ == "__main__":
    main()
