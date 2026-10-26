# 003: Read-only bounded agent baseline

Date: 26 October 2026.

Context: Day 6 needs a native tool loop before LangGraph, using existing Ollama
and Groq interfaces and preserving tenant isolation/refund approval requirements.

Options: let the model emit unrestricted replies and expose a refund tool early;
or expose only two validated read tools and render drafts from selected evidence.

Decision: use native tool calls for search_kb/get_order, bind credentials in the
trusted operator configuration, and validate a final evidence-selection plan.
Python renders original policy chunks or whitelisted order fields. Refund proposals
escalate; the mock refund endpoint returns 501 and cannot execute a write.

Why: this separates model choice from authorization, evidence provenance and
financial effects. It supplies a measurable baseline without prematurely adding
Day 7 policy rules, Day 8 graphs or Day 9 approval persistence.

Consequences: replies can be long, incomplete or irrelevant despite valid source
membership. Models can fail the JSON/native-call contract, causing escalation.
No agent state is durable, no approval is recorded, and deadlines are checked at
call boundaries rather than implemented by killing arbitrary code. The local
model's tight hardware/request budget is part of the measured configuration.

Reconsider after: reviewed scenario failures, the complete 25-case set, policy
tests and the graph comparison. Do not relax ownership or enable refunds to
improve apparent completion metrics.

Primary wire-format references checked against installed httpx 0.28.1 and the
existing provider endpoints: [Groq local tool calling](https://console.groq.com/docs/tool-use/local-tool-calling),
[Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling).
