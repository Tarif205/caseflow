"""Report deterministic hostile-model/poisoned-data enforcement tests, not LLM immunity."""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from caseflow.agent_evaluation import dataset_hash
from caseflow.config import PROJECT_ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "evals/results/day-13-injections.json"
    )
    args = parser.parse_args()
    xml = PROJECT_ROOT / ".cache/injections.xml"
    xml.parent.mkdir(exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_injections.py",
            "-q",
            f"--junitxml={xml}",
            "--basetemp=" + str(PROJECT_ROOT / ".cache" / ("injection-temp-" + uuid4().hex)),
            "-p",
            "no:cacheprovider",
        ],
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
        "surfaces": 8,
        "transports": ["direct", "mcp"],
        "complete": result.returncode == 0 and len(rows) == 16,
        "method": "deterministic hostile model outputs and poisoned data at eight surfaces through direct and MCP adapters; not a live-model robustness benchmark",
        "results": [{"case": r.attrib["name"], "passed": not list(r)} for r in rows],
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    if not report["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
