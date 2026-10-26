# Day 6 development baseline

Recorded on 26 October 2026 (Asia/Dhaka); raw artifacts preserve UTC timestamps.

| Configuration | Cases | Success | Evidence |
|---|---:|---:|---|
| Groq GPT-OSS-20B + read-only loop | s001–s005 | 4/5 (80%) | [Hosted JSON](day-06-hosted.json) |
| Ollama qwen3:4b + same loop | s001–s005 | 0/5 (0%) | [Local JSON](day-06-local.json) |

Hosted s001 made one successful search, then failed to produce parseable final
output at step 2. The other four met deterministic expected article/order checks.
Local s001 failed as model_unavailable at step 1 after 62.109 seconds; s002–s005
failed as invalid_model_output at step 1 with zero tool calls, taking roughly
46–60 seconds each. No refund or other side effect was available/executed.

These are the same five synthetic development cases and dataset hash. Both runs
have six-step/six-tool limits, a 120-second call-boundary budget and model calls
capped at 60 seconds. Local loading/unloading and limited laptop resources affect
results; qwen3 was stopped afterward. Raw model reasoning/error bodies were not
retained, so finer root-cause claims are not supported by these artifacts.

The hosted minimum of 3/5 for Day 6 is met. These are not 25-scenario agent results,
held-out quality, a general 80% task-success promise or proof of injection safety.
The judge checks selected source membership and expected order fields, not full
semantic relevance/completeness. Human approval persistence and refunds are not
implemented. Backend execution is independently disabled.
