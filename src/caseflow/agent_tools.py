"""Two read-only tools with schemas and credentials fixed outside model control."""

from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from caseflow.auth import Principal


class SearchArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=1000)
    top_k: StrictInt = Field(default=3, ge=1, le=5)


class OrderArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str = Field(pattern=r"^(?:NW|CT)-[0-9]{4,8}$")


ARGUMENTS = {"search_kb": SearchArgs, "get_order": OrderArgs}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": ARGUMENTS[name].model_json_schema(),
        },
    }
    for name, description in [
        (
            "search_kb",
            "Read help articles for the authenticated company. Use for policy questions.",
        ),
        (
            "get_order",
            "Read a fictional order's current status and tracking by order id. No changes.",
        ),
    ]
]


class ToolFailure(RuntimeError):
    pass


class RecordNotFound(ToolFailure):
    pass


def safe_base_url(url: str, *, allow_internal=False) -> str:
    p = urlparse(url)
    if (
        p.scheme not in {"https", "http"}
        or not p.hostname
        or p.username
        or p.password
        or p.query
        or p.fragment
    ):
        raise ValueError("Invalid tool service URL")
    allowed = {"localhost", "127.0.0.1", "::1"}
    if allow_internal:
        allowed |= {"mock-backend", "knowledge-api"}
    if p.scheme != "https" and p.hostname not in allowed:
        raise ValueError("Remote tool credentials require HTTPS")
    return url.rstrip("/")


@dataclass
class BoundTools:
    principal: Principal
    knowledge_url: str
    backend_url: str
    knowledge_token: str = field(repr=False)
    backend_token: str = field(repr=False)
    transport: object = field(default=None, repr=False)
    allow_internal: bool = False

    def __post_init__(self):
        self.knowledge_url = safe_base_url(self.knowledge_url, allow_internal=self.allow_internal)
        self.backend_url = safe_base_url(self.backend_url, allow_internal=self.allow_internal)
        if not self.knowledge_token or not self.backend_token:
            raise ValueError("Read-tool credentials are required")

    def execute(self, name: str, args: dict, timeout: float) -> dict:
        if name not in ARGUMENTS:
            raise ToolFailure("Tool unavailable")
        checked = ARGUMENTS[name].model_validate(args)
        scope = "kb:read" if name == "search_kb" else "orders:read"
        if scope not in self.principal.scopes:
            raise ToolFailure("Insufficient tool scope")
        try:
            with httpx.Client(
                timeout=min(timeout, 20), transport=self.transport, follow_redirects=False
            ) as client:
                if name == "search_kb":
                    response = client.post(
                        self.knowledge_url + "/v1/search",
                        json=checked.model_dump(),
                        headers={"Authorization": "Bearer " + self.knowledge_token},
                    )
                else:
                    response = client.get(
                        self.backend_url + "/orders/" + checked.order_id,
                        headers={"Authorization": "Bearer " + self.backend_token},
                    )
                response.raise_for_status()
                if len(response.content) > 64000:
                    raise ToolFailure("Tool response exceeded limits")
                value = response.json()
            if not isinstance(value, dict):
                raise ToolFailure("Invalid tool response")
            return value
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise RecordNotFound("Record not found") from None
            raise ToolFailure("Read service unavailable") from None
        except (httpx.HTTPError, ValueError):
            raise ToolFailure("Invalid read service response") from None
