import json

import pytest
from pydantic import ValidationError

from caseflow.agent_evaluation import Scenario, dataset_hash, judge, load_scenarios
from caseflow.config import PROJECT_ROOT
from caseflow.policy import ActionProposal, PolicyContext, PolicyOrder, policy_check

DATASET = PROJECT_ROOT / "evals/agent/scenarios.jsonl"
POLICY_CASES = [s for s in load_scenarios(DATASET) if s.proposed_amount_cents is not None]


@pytest.mark.parametrize("scenario", POLICY_CASES, ids=lambda s: s.id)
def test_policy_scenario_labels_match_fictional_orders(scenario):
    fixture = json.loads((PROJECT_ROOT / "data/mock/entities.json").read_text())
    # This is a test oracle, not a tenant-aware runtime lookup. In particular,
    # s023 deliberately supplies a foreign fixture to exercise defense in depth.
    raw = next(o for o in fixture["orders"] if o["id"] == scenario.expected_order)
    order = PolicyOrder(**{k: raw[k] for k in PolicyOrder.model_fields})
    context = PolicyContext(
        tenant_id=scenario.tenant,
        customer_id=scenario.customer_id,
        scopes=frozenset({"agent:run", "refunds:propose"}),
    )
    proposal = ActionProposal(
        action="refund",
        order_id=scenario.expected_order,
        amount_cents=scenario.proposed_amount_cents,
    )
    result = policy_check(proposal, context, order)
    assert not result.execution_allowed
    if scenario.needs_approval:
        assert result.outcome == "needs_approval" and not result.reasons
    else:
        assert result.outcome == "denied"
        assert set(scenario.expected_policy_reasons) <= set(result.reasons)


def test_all_scenarios_have_real_sources_and_orders_and_cover_both_tenants():
    rows = load_scenarios(DATASET)
    fixture = json.loads((PROJECT_ROOT / "data/mock/entities.json").read_text())
    assert len(rows) == 25 and len(POLICY_CASES) == 10
    assert {s.tenant for s in rows} == {"northwind", "contoso"}
    assert any(s.needs_approval for s in rows)
    assert any(s.injection for s in rows)
    for s in rows:
        if s.expected_doc:
            assert (PROJECT_ROOT / "data" / s.tenant / (s.expected_doc + ".md")).is_file()
        if s.expected_order:
            assert any(o["id"] == s.expected_order for o in fixture["orders"])


def test_original_day06_dataset_matches_both_saved_baseline_hashes():
    path = DATASET.with_name("scenarios-day06.jsonl")
    assert len(load_scenarios(path)) == 10
    for provider in ("hosted", "local"):
        report = json.loads((PROJECT_ROOT / f"evals/results/day-06-{provider}.json").read_text())
        assert dataset_hash(path) == report["dataset_sha256"]


def test_approval_and_code_policy_expectations_cannot_pass_as_generic_escalations():
    result = {"status": "escalate", "reason": "model_escalated", "refund_executed": False}
    for scenario in POLICY_CASES:
        assert not judge(scenario, result, PROJECT_ROOT / "data")


def test_approval_cannot_be_optional_on_refund_labels():
    raw = load_scenarios(DATASET)[5].model_dump()
    raw["needs_approval"] = False
    with pytest.raises(ValidationError):
        Scenario.model_validate(raw)


def test_deny_label_requires_the_expected_code_reasons():
    scenario = next(s for s in POLICY_CASES if "cap_exceeded" in s.expected_policy_reasons)
    result = {
        "status": "escalate",
        "reason": "policy_denied",
        "refund_executed": False,
        "policy": {"outcome": "denied", "reasons": ["cap_exceeded"]},
    }
    assert not judge(scenario, result, PROJECT_ROOT / "data")
    result["policy"]["reasons"] = scenario.expected_policy_reasons
    assert judge(scenario, result, PROJECT_ROOT / "data")


def test_placeholder_approval_scoring_is_explicit_and_cannot_count_as_durable():
    scenario = load_scenarios(DATASET)[5]
    result = {
        "status": "needs_approval",
        "reason": "approval_placeholder",
        "refund_executed": False,
        "policy": {"outcome": "needs_approval", "execution_allowed": False},
        "approval": {
            "state": "required",
            "durable": False,
            "order_id": scenario.expected_order,
            "amount_cents": 7500,
        },
    }
    assert not judge(scenario, result, PROJECT_ROOT / "data")
    assert judge(scenario, result, PROJECT_ROOT / "data", approval_placeholder=True)
    for field, value in [("amount_cents", 8001), ("order_id", "CT-2001"), ("state", "approved")]:
        forged = {**result, "approval": {**result["approval"], field: value}}
        assert not judge(scenario, forged, PROJECT_ROOT / "data", approval_placeholder=True)
