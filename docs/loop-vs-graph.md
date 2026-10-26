# Hand loop versus LangGraph

Day 8 baseline below. For the implemented Day 9 durable mode, see [approval flow](approval-flow.md).


Day 8 comparison; persistence and durable approval are still future work.

| Concern | Day 6 plain Python loop | Day 8 implemented graph |
|---|---|---|
| State | Local messages, evidence map, last order, counters | Explicit typed state and node updates |
| Model decision | Native tool calls or final evidence-selection JSON | Structured intake and planning JSON; code dispatches reads |
| Tool execution | Native call validation and read dispatch | Retrieve/lookup nodes retain bound auth and strict arguments |
| Routing | Branches and loop/return | Conditional edges and terminal branches |
| Bounds | Six model turns, six reads, run/call timeouts | Six node executions, six reads, run/call timeouts; recursion limit 16 |
| Refunds | All escalate; backend disabled | Pure eligibility policy; eligible proposal stops at non-durable approval marker |
| Execution | No refund tool | Unreachable disabled node; backend still disabled |
| Reply drafting | Original chunks and whitelisted facts | Same evidence-only rendering in a draft node |
| Persistence | None | None yet; Day 9 checkpointer pending |
| Restart awaiting approval | Not implemented | Not implemented; placeholder is not durable |
| Observability | Result/events and backend request ids | Node events and exported compiled diagram; Langfuse pending |
| Verification | Fake native-call sequences and real read services | Each graph branch plus same 25 live hosted scenarios |

The graph changes both orchestration and the model protocol (native tools to
structured stages). Numeric step limits have different units. Real runs use the
same corpus/model/scenario hash but are sequential, not a controlled experiment.
See [graph details](agent-graph.md) and the Day 8 results summary for failures and
measurement limits. No automatic security or persistence comes from the framework.
