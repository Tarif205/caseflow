# Support Copilot Platform

A small, production-style support system built to learn RAG, LangGraph agents, MCP, Docker and AWS in 15 days on a zero budget. All data belongs to a fictional company, Northwind Outfitters.

**Status:** Day 0 (setup). Nothing runs yet.

## Services

| Service | What it does | Status |
|---------|--------------|--------|
| `services/knowledge-api` | Ingests help-center articles and answers questions with citations (RAG) | Not started |
| `services/mock-backend` | Fictional orders, tickets and refunds for two tenants | Not started |
| `services/support-agent` | LangGraph agent that drafts replies and pauses for human approval before a refund | Not started |
| `services/mcp-server` | Read-only MCP tools with token auth and tenant isolation | Not started |

## Repository layout

```
docs/      architecture, decisions, journal, debug log
data/      Northwind help-center articles, mock orders
evals/     retrieval/, agent/, mcp/ datasets and scripts; results/
services/  the four services above
infra/     Compose files, AWS notes
```

## Running it

TODO (Day 1): setup and run steps.

## Results

TODO (Day 3 onward): measured numbers go here.

| Metric | Result | Date |
|--------|--------|------|
| Retrieval Recall@5 (40 questions) | | |
| Agent scenarios completed (25) | | |
| Refund attempts that paused for approval | | |
| Cross-tenant leaks in MCP tests | | |

## Configuration

Copy `.env.example` to `.env` and fill in the values. `.env` is git-ignored and must never be committed.
