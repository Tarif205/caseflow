from itertools import product

import pytest
from pydantic import ValidationError

from caseflow.policy import (
    ActionProposal,
    PolicyContext,
    PolicyDecision,
    PolicyOrder,
    policy_check,
)


def inputs(**changes):
    proposal = {"action": "refund", "order_id": "NW-1044", "amount_cents": 7500}
    context = {
        "tenant_id": "northwind",
        "customer_id": "NW-C002",
        "scopes": frozenset({"agent:run", "refunds:propose"}),
    }
    order = {
        "tenant_id": "northwind",
        "id": "NW-1044",
        "customer_id": "NW-C002",
        "status": "delivered",
        "total_cents": 7500,
        "currency": "USD",
    }
    for key, value in changes.items():
        group, field = key.split("__")
        {"proposal": proposal, "context": context, "order": order}[group][field] = value
    return ActionProposal(**proposal), PolicyContext(**context), PolicyOrder(**order)


@pytest.mark.parametrize("amount,total", [(1, 7500), (7500, 7500), (8000, 9000)])
def test_eligible_refund_requires_approval_never_execution(amount, total):
    result = policy_check(*inputs(proposal__amount_cents=amount, order__total_cents=total))
    assert result.outcome == "needs_approval" and not result.execution_allowed


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"context__scopes": frozenset({"refunds:propose"})}, "missing_agent_scope"),
        ({"context__scopes": frozenset({"agent:run"})}, "missing_refund_scope"),
        ({"proposal__amount_cents": None}, "invalid_amount"),
        ({"proposal__amount_cents": 0}, "invalid_amount"),
        ({"proposal__amount_cents": -1}, "invalid_amount"),
        ({"proposal__amount_cents": 8001}, "cap_exceeded"),
        ({"proposal__amount_cents": 7501}, "amount_exceeds_order"),
        ({"proposal__order_id": None}, "missing_order_id"),
        ({"proposal__order_id": "NW-9999"}, "order_mismatch"),
        ({"context__customer_id": None}, "missing_customer_identity"),
        ({"context__customer_id": "NW-C001"}, "customer_mismatch"),
        ({"order__tenant_id": "contoso"}, "tenant_mismatch"),
        ({"order__status": "processing"}, "ineligible_status"),
        ({"order__status": "shipped"}, "ineligible_status"),
        ({"order__status": "cancelled"}, "ineligible_status"),
        ({"order__status": "refunded"}, "ineligible_status"),
        ({"order__currency": "EUR"}, "unsupported_currency"),
        ({"order__total_cents": 0}, "amount_exceeds_order"),
    ],
)
def test_every_refund_deny_path(changes, reason):
    result = policy_check(*inputs(**changes))
    assert result.outcome == "denied" and reason in result.reasons
    assert not result.execution_allowed


def test_missing_order_is_denied():
    proposal, context, _ = inputs()
    assert "order_not_found" in policy_check(proposal, context).reasons


@pytest.mark.parametrize("value", [True, 75.0, "7500"])
def test_money_is_strict_integer_cents(value):
    with pytest.raises(ValidationError):
        ActionProposal(action="refund", amount_cents=value)


def test_model_cannot_supply_approval_or_raise_cap():
    for field in ("approved", "refund_cap", "tenant_id"):
        with pytest.raises(ValidationError):
            ActionProposal(action="refund", **{field: True})
    with pytest.raises(ValidationError):
        PolicyDecision(outcome="needs_approval", execution_allowed=True)


@pytest.mark.parametrize("action", ["reply", "escalate"])
def test_read_only_actions_do_not_need_refund_scope(action):
    _, context, _ = inputs(context__scopes=frozenset({"agent:run"}))
    assert policy_check(ActionProposal(action=action), context).outcome == action


def test_refund_fields_cannot_be_smuggled_into_reply():
    _, context, _ = inputs()
    result = policy_check(ActionProposal(action="reply", amount_cents=75), context)
    assert result.reasons == ("unexpected_action_fields",)


def test_deny_wins_over_all_bounded_combinations_and_widening_scopes():
    # Exhaustive finite-domain property check, not a claim over all Python values.
    checked = 0
    for amount, tenant, customer, status, scopes, currency in product(
        [None, -1, 0, 1, 7500, 8000, 8001],
        ["northwind", "contoso"],
        [None, "NW-C001", "NW-C002"],
        ["processing", "shipped", "delivered", "cancelled", "refunded"],
        [frozenset(), frozenset({"agent:run"}), frozenset({"agent:run", "refunds:propose"})],
        ["USD", "EUR"],
    ):
        args = inputs(
            proposal__amount_cents=amount,
            order__tenant_id=tenant,
            context__customer_id=customer,
            order__status=status,
            context__scopes=scopes,
            order__currency=currency,
        )
        base = policy_check(*args)
        eligible = (
            amount is not None
            and 0 < amount <= 7500
            and tenant == "northwind"
            and customer == "NW-C002"
            and status == "delivered"
            and {"agent:run", "refunds:propose"} <= scopes
            and currency == "USD"
        )
        assert (base.outcome == "needs_approval") == eligible
        result = policy_check(*args, prior_denials=("external restriction",))
        assert result.outcome == "denied" and "prior_denial" in result.reasons
        assert not result.execution_allowed
        checked += 1
    assert checked == 1260


def test_all_denial_reasons_accumulate_and_inputs_are_unchanged():
    args = inputs(
        proposal__amount_cents=8001,
        order__tenant_id="contoso",
        order__status="refunded",
        context__scopes=frozenset(),
    )
    before = tuple(a.model_dump() for a in args)
    result = policy_check(*args)
    assert {
        "cap_exceeded",
        "tenant_mismatch",
        "ineligible_status",
        "missing_agent_scope",
        "missing_refund_scope",
    } <= set(result.reasons)
    assert tuple(a.model_dump() for a in args) == before


@pytest.mark.parametrize("action", ["reply", "escalate", "refund"])
def test_prior_denial_blocks_every_action_without_reflecting_details(action):
    _, context, order = inputs()
    decision = policy_check(
        ActionProposal(action=action), context, order, prior_denials=("untrusted secret detail",)
    )
    assert decision.outcome == "denied"
    assert "untrusted secret detail" not in decision.model_dump_json()
