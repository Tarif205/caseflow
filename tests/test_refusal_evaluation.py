import json

import httpx
import pytest

from support_copilot.config import PROJECT_ROOT
from support_copilot.refusal_evaluation import evaluate_refusals

DATASET = PROJECT_ROOT / "evals/retrieval/questions.jsonl"
TOKEN = "test-token-never-publish-real-values"


def test_counts_real_refusals_and_false_acceptance_against_full_denominator():
    count = 0

    def respond(request):
        nonlocal count
        count += 1
        assert request.headers["Authorization"] == "Bearer " + TOKEN
        positive = count > 7
        return httpx.Response(
            200,
            json={
                "found": positive,
                "answer": "Related policy" if positive else "Not found",
                "citations": [{"chunk_id": "example"}] if positive else [],
                "reason": "answered" if positive else "no_evidence",
            },
        )

    report = evaluate_refusals(
        "https://api.example", TOKEN, DATASET, transport=httpx.MockTransport(respond)
    )
    assert report["complete"] and report["gate_passed"]
    assert report["refused"] == 7 and report["refusal_rate"] == 0.7
    assert sum(r.get("false_acceptance", False) for r in report["results"]) == 3
    assert TOKEN not in json.dumps(report)


@pytest.mark.parametrize("status", [401, 403, 429, 503])
def test_http_errors_stop_and_never_count_as_refusals(status):
    report = evaluate_refusals(
        "https://api.example",
        TOKEN,
        DATASET,
        transport=httpx.MockTransport(lambda r: httpx.Response(status, text=TOKEN)),
    )
    assert not report["complete"] and not report["gate_passed"]
    assert report["refused"] == 0 and report["completed_cases"] == 0
    assert report["expected_cases"] == 10 and report["errors"] == 1
    assert TOKEN not in json.dumps(report)


def test_malformed_false_result_cannot_pass_gate():
    report = evaluate_refusals(
        "https://api.example",
        TOKEN,
        DATASET,
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"found": False})),
    )
    assert not report["gate_passed"] and report["errors"] == 1


@pytest.mark.parametrize(
    "url",
    ["http://api.example", "https://user:secret@api.example", "https://api.example?key=secret"],
)
def test_rejects_unsafe_credential_destinations(url):
    with pytest.raises(ValueError):
        evaluate_refusals(url, TOKEN, DATASET)
