"""Report deterministic hostile-model/poisoned-data enforcement tests, not LLM immunity."""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from support_copilot.agent_evaluation import dataset_hash
from support_copilot.config import PROJECT_ROOT


def main():
    xml = PROJECT_ROOT / ".cache/injections.xml"
    xml.parent.mkdir(exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_injections.py", "-q", f"--junitxml={xml}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    rows = ET.parse(xml).findall(".//testcase")
    passed = sum(not list(row) for row in rows)
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "cases": len(rows),
        "passed": passed,
        "dataset_sha256": dataset_hash(PROJECT_ROOT / "evals/agent/injections.jsonl"),
        "complete": result.returncode == 0 and len(rows) == 8,
        "method": "deterministic hostile model outputs and poisoned data at eight surfaces; not a live-model robustness benchmark",
        "results": [{"case": r.attrib["name"], "passed": not list(r)} for r in rows],
    }
    (PROJECT_ROOT / "evals/results/day-10-injections.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    if not report["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
