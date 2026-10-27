"""Measure actual API refusals; HTTP/provider failures are never successful refusals."""

import hashlib
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

from caseflow.evaluation import load_questions

REFUSAL_REASONS = {"no_evidence", "record_lookup_required", "model_declined", "invalid_evidence"}


def evaluate_refusals(base_url: str, token: str, dataset: Path, *, transport=None) -> dict:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Invalid API URL")
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Remote API credentials require HTTPS")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("API URL must not contain credentials, a query or a fragment")
    if not token.strip():
        raise ValueError("An API token is required")
    cases = [q for q in load_questions(dataset) if not q.answerable]
    if len(cases) != 10 or any(q.tenant != "northwind" for q in cases):
        raise ValueError("This gate requires ten Northwind unanswerable cases")
    results = []
    with httpx.Client(
        base_url=base_url.rstrip("/"), timeout=180, follow_redirects=False, transport=transport
    ) as client:
        for case in cases:
            row = {"id": case.id, "question": case.question, "refused": False}
            try:
                response = client.post(
                    "/v1/ask",
                    headers={"Authorization": "Bearer " + token},
                    json={"query": case.question, "top_k": 5},
                )
                row["http_status"] = response.status_code
                response.raise_for_status()
                body = response.json()
                if (
                    not isinstance(body, dict)
                    or type(body.get("found")) is not bool
                    or not isinstance(body.get("answer"), str)
                    or not body["answer"].strip()
                    or not isinstance(body.get("citations"), list)
                    or body.get("reason") not in REFUSAL_REASONS | {"answered"}
                ):
                    raise ValueError("Invalid answer contract")
                if body["found"]:
                    if body["reason"] != "answered" or not body["citations"]:
                        raise ValueError("Invalid positive answer contract")
                    # Keep false acceptances for review, without trusting returned
                    # strings as safe diagnostics. Our corpus/questions are fictional.
                    row["false_acceptance"] = True
                else:
                    if body["reason"] not in REFUSAL_REASONS or body["citations"]:
                        raise ValueError("Invalid refusal contract")
                    row["refused"] = True
                row["reason"] = body["reason"]
            except (httpx.HTTPError, ValueError) as exc:
                # Never record exception text or raw upstream bodies/headers.
                row["error"] = type(exc).__name__
                results.append(row)
                break  # Do not keep consuming quota after a failed dependency.
            results.append(row)
            if transport is None:
                time.sleep(1)
    refused = sum(r["refused"] for r in results)
    errors = sum("error" in r for r in results)
    complete = len(results) == len(cases) and not errors
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "dataset_kind": "assistant-authored synthetic development cases, not held-out",
        "top_k": 5,
        "expected_cases": len(cases),
        "completed_cases": len(results) - errors,
        "complete": complete,
        "errors": errors,
        "refused": refused,
        "refusal_rate": refused / len(cases),
        "minimum_required": 0.7,
        "gate_passed": complete and refused >= 7,
        "limitations": "Refusal behavior only; not answerable coverage or semantic faithfulness. Invalid-evidence refusals are counted but reported by reason.",
        "results": results,
    }
