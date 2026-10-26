# Day 8: LangGraph rebuild

Date: 26 October 2026. Implemented under the agreed implementation-first override.
Learning explain-backs remain deferred; no independent understanding is claimed.

Implemented typed state, structured model intake/planning, separate retrieval and
lookup nodes, plain policy, evidence-only draft, escalation and terminal approval
placeholder. Execute is unreachable and independently disabled. Dependencies and
trusted identity stay outside model state. No scope/identity comes from ticket prose.

Checked installed LangGraph 1.2.16 signatures and official Graph API documentation.
No new package needed. Generated docs/agent-graph.mmd from the compiled graph;
docs/agent-graph.md explains state, branches and trust boundaries. Filled the
loop-vs-graph comparison with actual behavior rather than future persistence claims.

Runner supports --engine graph|loop and explicitly labels placeholder scoring.
266 tests passed in 7.42s, including Postgres integration; all graph paths and
budgets tested. The real hosted 25-case run scored graph 14/25, loop 10/25;
first-five graph 5/5, loop 4/5. Every result and failure is saved. This is a single
synthetic development comparison, with changed model protocols/step units and
provider failures; not evidence of a general framework advantage.

The graph's eligible-refund demo lacks end-customer identity/refund scope; the
code correctly denies it. A foreign-order fixture expectation requires downstream
policy details that secure lookup cannot expose. Nine graph/six loop calls returned
model_unavailable with no retained per-case provider status. Separate low-token
400/normal-token 200 probes do not establish those failures' causes. See
evals/results/day-08-summary.md for the complete counts and open limitations.

No refund executed, real approval record persisted, checkpoint, trace integration,
agent API or cloud deployment was added. Existing local tokens, Neon and EC2
deployment unchanged. No local model was loaded for this day. User commits/pushes.

Next: Day 9 persistence, real human approval interrupt/resume and tracing. The
Day 10 G2 quality gate remains open (56% is below its 60% target). Before that
gate, improve per-call safe diagnostics, reconcile foreign-order scenario semantics
and verify the complete approved/refused workflow across process restarts.
