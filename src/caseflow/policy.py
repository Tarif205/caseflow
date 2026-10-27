"""Pure, conservative demo policy. A decision never authorizes execution.

Context and order must come from authenticated intake/tenant-bound storage, not
ticket text or model arguments. There is deliberately no approval input here.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

REFUND_CAP_CENTS = 8000


class PolicyInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ActionProposal(PolicyInput):
    action: Literal["reply", "escalate", "refund"]
    order_id: str | None = None
    amount_cents: StrictInt | None = None


class PolicyContext(PolicyInput):
    tenant_id: str = Field(min_length=1, max_length=80)
    customer_id: str | None = None
    scopes: frozenset[str] = frozenset()


class PolicyOrder(PolicyInput):
    tenant_id: str = Field(min_length=1, max_length=80)
    id: str = Field(min_length=1, max_length=80)
    customer_id: str = Field(min_length=1, max_length=80)
    status: Literal["processing", "shipped", "delivered", "cancelled", "refunded"]
    total_cents: StrictInt = Field(ge=0)
    currency: str


class PolicyDecision(PolicyInput):
    outcome: Literal["reply", "escalate", "denied", "needs_approval"]
    reasons: tuple[str, ...] = ()
    # Literal False prevents downstream code mistaking eligibility for permission.
    execution_allowed: Literal[False] = False


def policy_check(
    proposal: ActionProposal,
    context: PolicyContext,
    order: PolicyOrder | None = None,
    *,
    prior_denials: tuple[str, ...] = (),
) -> PolicyDecision:
    """Combine independent restrictions; no model, database, clock or side effects.

    An eligible refund yields needs_approval, never an executable permission.
    Prior denial details are not reflected (they can contain untrusted text).
    """
    reasons = ["prior_denial"] if prior_denials else []
    if "agent:run" not in context.scopes:
        reasons.append("missing_agent_scope")
    if proposal.action != "refund":
        if proposal.amount_cents is not None or proposal.order_id is not None:
            reasons.append("unexpected_action_fields")
        if reasons:
            return PolicyDecision(outcome="denied", reasons=tuple(reasons))
        return PolicyDecision(outcome=proposal.action)

    if "refunds:propose" not in context.scopes:
        reasons.append("missing_refund_scope")
    amount = proposal.amount_cents
    if amount is None or amount <= 0:
        reasons.append("invalid_amount")
    elif amount > REFUND_CAP_CENTS:
        reasons.append("cap_exceeded")
    if not proposal.order_id:
        reasons.append("missing_order_id")
    if not context.customer_id:
        reasons.append("missing_customer_identity")
    if order is None:
        reasons.append("order_not_found")
    else:
        if order.tenant_id != context.tenant_id:
            reasons.append("tenant_mismatch")
        if order.customer_id != context.customer_id:
            reasons.append("customer_mismatch")
        if order.id != proposal.order_id:
            reasons.append("order_mismatch")
        if order.status != "delivered":
            reasons.append("ineligible_status")
        if order.currency != "USD":
            reasons.append("unsupported_currency")
        if amount is not None and amount > order.total_cents:
            reasons.append("amount_exceeds_order")
    return PolicyDecision(outcome="denied" if reasons else "needs_approval", reasons=tuple(reasons))
