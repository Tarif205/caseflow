import pytest

from caseflow.agent_evaluation import judge, load_scenarios
from caseflow.config import PROJECT_ROOT


def test_full_scenarios_have_five_reply_cases_for_both_model_baselines():
    rows = load_scenarios(PROJECT_ROOT / "evals/agent/scenarios.jsonl")
    assert len(rows) == 25 and all(r.expected_action == "reply" for r in rows[:5])


@pytest.mark.parametrize(
    "reason",
    ["model_unavailable", "read_service_failure", "deadline", "step_limit", "invalid_model_output"],
)
def test_infrastructure_failure_is_not_a_successful_escalation(reason):
    scenario = load_scenarios(PROJECT_ROOT / "evals/agent/scenarios.jsonl")[7]
    assert not judge(
        scenario,
        {"status": "escalate", "reason": reason, "refund_executed": False},
        PROJECT_ROOT / "data",
    )


def test_expected_article_label_alone_does_not_validate_fabricated_source_text():
    scenario = load_scenarios(PROJECT_ROOT / "evals/agent/scenarios.jsonl")[0]
    result = {
        "status": "reply",
        "refund_executed": False,
        "order": None,
        "citations": [
            {
                "source": "returns-policy.md",
                "text": "Invented policy words",
                "document_id": "returns-policy",
            }
        ],
    }
    assert not judge(scenario, result, PROJECT_ROOT / "data")
