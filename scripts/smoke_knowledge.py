"""Check a real running API without printing credentials or changing article data."""

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

from support_copilot.config import PROJECT_ROOT
from support_copilot.ingestion import load_articles


def check(base_url: str, skip_model: bool = False) -> dict:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Invalid API URL")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("API credentials require HTTPS for remote hosts")
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    tokens = {
        tenant: os.getenv(tenant.upper() + "_API_TOKEN", "") for tenant in ("northwind", "contoso")
    }
    if not all(tokens.values()):
        raise ValueError("Provision NORTHWIND_API_TOKEN and CONTOSO_API_TOKEN first")
    sources = {
        tenant: {a.id: a.text for a in load_articles(PROJECT_ROOT / "data" / tenant)}
        for tenant in tokens
    }
    checks = []
    with httpx.Client(base_url=base_url, timeout=180, follow_redirects=False) as client:
        for route in ("/health", "/ready"):
            response = client.get(route)
            response.raise_for_status()
            checks.append({"route": route, "status": response.status_code})
        response = client.post("/v1/search", json={"query": "Returns?"})
        if response.status_code != 401:
            raise RuntimeError("Unauthenticated search was not rejected")
        checks.append({"check": "missing_token", "status": 401})
        for tenant, token in tokens.items():
            response = client.post(
                "/v1/search",
                json={"query": "Contoso returns policy for 60 days"},
                headers={"Authorization": "Bearer " + token},
            )
            response.raise_for_status()
            hits = response.json()["results"]
            if not hits or any(
                h["document_id"] not in sources[tenant]
                or h["text"] not in sources[tenant][h["document_id"]]
                for h in hits
            ):
                raise RuntimeError("Search returned data outside the requested tenant corpus")
            checks.append(
                {"check": "tenant_search", "tenant": tenant, "hits": len(hits), "isolated": True}
            )
        headers = {"Authorization": "Bearer " + tokens["northwind"]}
        response = client.post(
            "/v1/ask", headers=headers, json={"query": "When was my refund for NW-1042 approved?"}
        )
        response.raise_for_status()
        if response.json()["found"] or response.json()["reason"] != "record_lookup_required":
            raise RuntimeError("Missing concrete order evidence was not refused")
        checks.append({"check": "order_specific_refusal", "found": False})
        if not skip_model:
            response = client.post(
                "/v1/ask",
                headers=headers,
                json={"query": "How long is the manufacturing defect warranty?"},
            )
            response.raise_for_status()
            result = response.json()
            if not result["found"] or not result["citations"]:
                raise RuntimeError("Live model did not produce a supported answer")
            if any(
                c["document_id"] not in sources["northwind"]
                or c["quote"] not in sources["northwind"][c["document_id"]]
                for c in result["citations"]
            ):
                raise RuntimeError("Answer citation was not present in tenant source text")
            checks.append(
                {
                    "check": "live_cited_answer",
                    "found": True,
                    "answer": result["answer"],
                    "citations": result["citations"],
                }
            )
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "live_model_tested": not skip_model,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8001")
    parser.add_argument("--skip-model", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.base_url, args.skip_model)
    except (httpx.HTTPError, ValueError, RuntimeError) as exc:
        raise SystemExit(
            f"Knowledge API smoke check failed ({type(exc).__name__}); inspect API status and safe server logs."
        ) from None
    payload = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
