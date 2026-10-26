# Agent loop versus LangGraph

Day 6 baseline; graph column is planned until the Day 8 rebuild is implemented.

| Concern | Current plain Python loop | Planned LangGraph version |
|---|---|---|
| State | Local messages, evidence map, last order, counters | Explicit typed state shared across nodes |
| Model decision | Native tool calls or validated evidence-selection plan | Intake/planning/reply nodes with defined outputs |
| Tool execution | Explicit read-only dispatch and argument validation | Tool/read nodes retain the same authorization boundary |
| Routing | Python branches and loop/return | Edges and conditional routing |
| Bounds | Step/tool budget and time checks | Graph recursion limits plus explicit business/tool/time budgets |
| Refunds | Always escalate; backend execution disabled | Policy check, durable human approval and guarded execution |
| Persistence | None; process exit loses the run | Checkpointer and stable run/thread identity |
| Restart while awaiting approval | Not implemented | Day 9 requirement, tested across restart |
| Observability | Structured result/events and backend request ids | Run/step trace spans and persisted state diagnostics |
| Testing | Fake-model sequences and real read-service cases | Compare same scenarios and test each graph path |

A framework changes orchestration, not authorization. Tenant filtering, strict
schemas and the refund approval boundary must remain plain code protections.
The loop is intentionally the first baseline; migrating to a graph before it
works would obscure whether failures come from tool contracts or orchestration.
