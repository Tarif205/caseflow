"""Provision only existing read-only MCP credential hashes in configured Neon.

Raw values remain in ignored local .env and memory; no cloud environment/config
file or SSM parameter stores these client tokens. Run after release CI passes.
"""

from dataclasses import replace
from urllib.parse import urlparse

from dotenv import dotenv_values

from caseflow.config import PROJECT_ROOT, Settings
from caseflow.mcp_credentials import SCOPES, provision


def main():
    values = dotenv_values(PROJECT_ROOT / ".env")
    url = values.get("NEON_DATABASE_URL") or ""
    if not (urlparse(url).hostname or "").endswith(".neon.tech"):
        raise ValueError("Expected the configured Neon database")
    provision(
        replace(Settings(), database_url=url),
        {
            tenant: values.get(tenant.upper() + "_MCP_API_TOKEN")
            for tenant in ("northwind", "contoso")
        },
    )
    print({"status": "read_only_hashes_verified", "tenants": 2, "scopes": sorted(SCOPES)})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(
            f"MCP cloud credentials failed ({type(exc).__name__}); values withheld"
        ) from None
