"""Validated fictional fixtures and tenant-bound read-only backend operations."""

import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from caseflow.config import Settings
from caseflow.database import connect


class FixtureModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: Literal["northwind", "contoso"]
    id: str = Field(min_length=1, max_length=80)
    customer_id: str = Field(min_length=1, max_length=80)


class Order(FixtureModel):
    status: Literal["processing", "shipped", "delivered", "cancelled", "refunded"]
    total_cents: StrictInt = Field(ge=0)
    currency: Literal["USD"]
    tracking_number: str | None
    placed_on: date


class Ticket(FixtureModel):
    text: str = Field(min_length=1, max_length=4000)
    status: Literal["open", "closed"]


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: Literal["northwind", "contoso"]
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)


class Fixtures(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customers: list[Customer]
    orders: list[Order]
    tickets: list[Ticket]


def seed_mock(settings: Settings, path: Path) -> dict:
    data = Fixtures.model_validate(json.loads(path.read_text(encoding="utf-8")))
    customers = {(c.tenant_id, c.id) for c in data.customers}
    for records in (data.customers, data.orders, data.tickets):
        if len({(r.tenant_id, r.id) for r in records}) != len(records):
            raise ValueError("Duplicate mock fixture identity")
    if any((r.tenant_id, r.customer_id) not in customers for r in [*data.orders, *data.tickets]):
        raise ValueError("Mock customer references must belong to the same tenant")
    with connect(settings) as conn:
        for customer in data.customers:
            conn.execute(
                "INSERT INTO customers (tenant_id,id,name) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (customer.tenant_id, customer.id, customer.name),
            )
        for order in data.orders:
            conn.execute(
                """INSERT INTO orders
                   (tenant_id,id,customer_id,status,total_cents,currency,tracking_number,placed_on)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                tuple(
                    getattr(order, k)
                    for k in (
                        "tenant_id",
                        "id",
                        "customer_id",
                        "status",
                        "total_cents",
                        "currency",
                        "tracking_number",
                        "placed_on",
                    )
                ),
            )
        for ticket in data.tickets:
            conn.execute(
                """INSERT INTO tickets (tenant_id,id,customer_id,text,status)
                   VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (ticket.tenant_id, ticket.id, ticket.customer_id, ticket.text, ticket.status),
            )
    return {
        "status": "seeded",
        "customers": len(data.customers),
        "orders": len(data.orders),
        "tickets": len(data.tickets),
    }


class MockStore:
    def __init__(self, conn):
        self.conn = conn

    def get_order(self, tenant: str, order_id: str) -> dict | None:
        return self.conn.execute(
            """SELECT id, customer_id, status, total_cents, currency, tracking_number, placed_on
               FROM orders WHERE tenant_id=%s AND id=%s""",
            (tenant, order_id),
        ).fetchone()

    def open_tickets(self, tenant: str, limit: int = 10) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 50:
            raise ValueError("Ticket limit must be 1 through 50")
        return self.conn.execute(
            """SELECT id, customer_id, text, status FROM tickets
               WHERE tenant_id=%s AND status='open' ORDER BY id LIMIT %s""",
            (tenant, limit),
        ).fetchall()
