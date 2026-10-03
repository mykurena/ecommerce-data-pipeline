"""Run `dbt test`, summarize the results and send them to an n8n webhook.

n8n decides what to do with the summary (e.g. send a Telegram alert when tests fail).

Usage (from the repo root, with the virtual environment active):
    python monitoring/run_dbt_tests.py

Environment variables (.env):
    GCP_PROJECT_ID     used by dbt
    N8N_WEBHOOK_URL    e.g. http://localhost:5678/webhook/dbt-test-results
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DBT_DIR = Path("dbt_project")
TARGET_DIR = DBT_DIR / "target"


def run_dbt_test() -> int:
    dbt = shutil.which("dbt")
    if not dbt:
        raise SystemExit("dbt not found. Activate the virtual environment first.")
    result = subprocess.run([dbt, "test"], cwd=DBT_DIR)
    return result.returncode


def summarize(run_results_path: Path, manifest_path: Path) -> dict:
    """Build a compact summary from dbt's run_results.json and manifest.json."""
    run_results = json.loads(run_results_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    nodes = manifest.get("nodes", {})

    failures = []
    for r in run_results["results"]:
        if r["status"] in ("pass", "success"):
            continue
        node = nodes.get(r["unique_id"], {})
        depends_on = node.get("depends_on", {}).get("nodes", [])
        models = [d.split(".")[-1] for d in depends_on if d.startswith(("model.", "source."))]
        failures.append(
            {
                "test": node.get("name", r["unique_id"]),
                "model": ", ".join(models) or "unknown",
                "column": node.get("column_name"),
                "status": r["status"],
                "failing_rows": r.get("failures"),
                "message": (r.get("message") or "")[:300],
            }
        )

    total = len(run_results["results"])
    return {
        "source": "dbt test",
        "project": run_results.get("metadata", {}).get("project_name", "ecommerce_pipeline"),
        "generated_at": run_results.get("metadata", {}).get("generated_at"),
        "total": total,
        "failed": len(failures),
        "passed": total - len(failures),
        "failures": failures,
    }


def send_to_n8n(payload: dict, url: str) -> None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            print(f"Sent summary to n8n (HTTP {response.status}).")
    except urllib.error.URLError as exc:
        print(f"Could not reach n8n at {url}: {exc}")


def main() -> None:
    exit_code = run_dbt_test()

    run_results_path = TARGET_DIR / "run_results.json"
    manifest_path = TARGET_DIR / "manifest.json"
    if not run_results_path.exists():
        raise SystemExit("dbt did not produce run_results.json. Check the dbt output above.")

    payload = summarize(run_results_path, manifest_path)
    print(f"\nSummary: {payload['passed']} passed, {payload['failed']} failed of {payload['total']}.")

    url = os.getenv("N8N_WEBHOOK_URL")
    if url:
        send_to_n8n(payload, url)
    else:
        print("N8N_WEBHOOK_URL is not set; skipping notification.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
