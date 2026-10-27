"""Run the ten-case actual API refusal gate without displaying credentials."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from caseflow.config import PROJECT_ROOT
from caseflow.refusal_evaluation import evaluate_refusals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    try:
        result = evaluate_refusals(
            args.base_url,
            os.getenv("NORTHWIND_API_TOKEN", ""),
            PROJECT_ROOT / "evals/retrieval/questions.jsonl",
        )
    except ValueError:
        raise SystemExit(
            "Invalid evaluation URL, dataset or missing token; no values displayed"
        ) from None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))
    if not result["gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
