from uuid import uuid4

import pytest

from support_copilot.approvals import ApprovalDenied, ApprovalStore
from support_copilot.auth import authenticate, provision_token


@pytest.fixture
def ledger(db):
    store, tenants = db
    conn = store.conn
    for tenant in tenants:
        conn.execute(
            "INSERT INTO customers (tenant_id,id,name) VALUES (%s,'c1','Synthetic')", (tenant,)
        )
        conn.execute(
            """INSERT INTO orders (tenant_id,id,customer_id,status,total_cents,currency,placed_on)
                      VALUES (%s,'NW-1044','c1','delivered',7500,'USD','2026-10-20')""",
            (tenant,),
        )
        conn.execute(
            """INSERT INTO tickets (tenant_id,id,customer_id,text,status)
                      VALUES (%s,'t1','c1','Refund NW-1044 for 75 dollars','open')""",
            (tenant,),
        )
    for tenant, token, scopes in [
        (tenants[0], "w" * 43, ["agent:run", "tickets:read", "refunds:propose", "refunds:execute"]),
        (tenants[0], "a" * 43, ["refund:approve"]),
        (tenants[1], "f" * 43, ["refund:approve", "agent:run"]),
        (tenants[0], "r" * 43, ["agent:run", "tickets:read"]),
    ]:
        provision_token(conn, tenant, token, scopes)
    actors = {
        name: authenticate(conn, char * 43)
        for name, char in [("worker", "w"), ("approver", "a"), ("foreign", "f"), ("reader", "r")]
    }
    service = ApprovalStore(conn)
    run_id = str(uuid4())
    service.create_run(actors["worker"], run_id, "t1")
    yield service, actors, run_id


def request(ledger):
    service, actors, run_id = ledger
    service.request(actors["worker"], run_id, "NW-1044", 7500)
    return service, actors, run_id


@pytest.mark.integration
def test_no_refund_without_stored_human_approval(ledger):
    service, actors, run_id = ledger
    with pytest.raises(ApprovalDenied):
        service.execute(actors["worker"], run_id)
    request(ledger)
    with pytest.raises(ApprovalDenied):
        service.execute(actors["worker"], run_id)
    assert (
        service.conn.execute(
            "SELECT count(*) n FROM refunds WHERE tenant_id=%s", (actors["worker"].tenant_id,)
        ).fetchone()["n"]
        == 0
    )


@pytest.mark.integration
def test_approved_refund_is_atomic_idempotent_and_closes_order(ledger):
    service, actors, run_id = request(ledger)
    service.decide(actors["approver"], run_id, True)
    first = service.execute(actors["worker"], run_id)
    assert first == service.execute(actors["worker"], run_id)
    assert first == {"order_id": "NW-1044", "amount_cents": 7500}
    assert (
        service.conn.execute(
            "SELECT status FROM orders WHERE tenant_id=%s AND id='NW-1044'",
            (actors["worker"].tenant_id,),
        ).fetchone()["status"]
        == "refunded"
    )
    assert (
        service.conn.execute(
            "SELECT count(*) n FROM refunds WHERE tenant_id=%s", (actors["worker"].tenant_id,)
        ).fetchone()["n"]
        == 1
    )


@pytest.mark.integration
def test_rejected_approval_never_executes_or_changes_decision(ledger):
    service, actors, run_id = request(ledger)
    service.decide(actors["approver"], run_id, False)
    with pytest.raises(ApprovalDenied):
        service.execute(actors["worker"], run_id)
    with pytest.raises(ApprovalDenied):
        service.decide(actors["approver"], run_id, True)


@pytest.mark.integration
def test_foreign_and_missing_run_fail_identically(ledger):
    service, actors, run_id = request(ledger)
    for candidate in (run_id, str(uuid4())):
        with pytest.raises(ApprovalDenied):
            service.decide(actors["foreign"], candidate, True)
        with pytest.raises(ApprovalDenied):
            service.get(actors["foreign"], candidate)
    assert service.pending(actors["foreign"]) == []


@pytest.mark.integration
def test_requester_cannot_self_approve_even_with_approval_scope(ledger):
    service, actors, run_id = request(ledger)
    service.conn.execute(
        "UPDATE api_tokens SET scopes=array_append(scopes,'refund:approve') WHERE token_hash=%s",
        (actors["worker"].token_hash,),
    )
    with pytest.raises(ApprovalDenied):
        service.decide(actors["worker"], run_id, True)


@pytest.mark.integration
@pytest.mark.parametrize("role", ["worker", "approver"])
@pytest.mark.parametrize(
    "change", ["revoked_at=now()", "expires_at=now()-interval '1 second'", "scopes='{}'"]
)
def test_permission_revocation_after_approval_blocks_execution(ledger, role, change):
    service, actors, run_id = request(ledger)
    service.decide(actors["approver"], run_id, True)
    # Fixed test cases, no user-controlled SQL fragment.
    service.conn.execute(
        f"UPDATE api_tokens SET {change} WHERE token_hash=%s", (actors[role].token_hash,)
    )
    with pytest.raises(ApprovalDenied):
        service.execute(actors["worker"], run_id)


@pytest.mark.integration
@pytest.mark.parametrize("change", ["status='cancelled'", "total_cents=7000", "total_cents=9000"])
def test_order_change_after_approval_blocks_execution(ledger, change):
    service, actors, run_id = request(ledger)
    service.decide(actors["approver"], run_id, True)
    service.conn.execute(
        f"UPDATE orders SET {change} WHERE tenant_id=%s AND id='NW-1044'",
        (actors["worker"].tenant_id,),
    )
    with pytest.raises(ApprovalDenied):
        service.execute(actors["worker"], run_id)


@pytest.mark.integration
def test_different_proposal_cannot_reuse_approval(ledger):
    service, actors, run_id = request(ledger)
    with pytest.raises(ApprovalDenied):
        service.request(actors["worker"], run_id, "NW-1044", 5000)


@pytest.mark.integration
def test_second_run_cannot_refund_same_order_twice(ledger):
    service, actors, run_id = request(ledger)
    other = str(uuid4())
    service.create_run(actors["worker"], other, "t1")
    service.request(actors["worker"], other, "NW-1044", 7500)
    service.decide(actors["approver"], other, True)
    service.decide(actors["approver"], run_id, True)
    service.execute(actors["worker"], run_id)
    with pytest.raises(ApprovalDenied):
        service.execute(actors["worker"], other)


@pytest.mark.integration
def test_read_actor_cannot_propose_or_execute(ledger):
    service, actors, run_id = request(ledger)
    with pytest.raises(ApprovalDenied):
        service.request(actors["reader"], run_id, "NW-1044", 7500)
    with pytest.raises(ApprovalDenied):
        service.execute(actors["reader"], run_id)


@pytest.mark.integration
def test_pending_list_is_minimal_and_does_not_return_hashes(ledger):
    service, actors, run_id = request(ledger)
    rows = service.pending(actors["approver"])
    assert len(rows) == 1 and rows[0]["run_id"] == run_id
    assert set(rows[0]) == {"run_id", "order_id", "amount_cents", "created_at"}
