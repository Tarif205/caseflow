# Learning contract

## Current project identity (27 October 2026)

The product is CaseFlow. Python package/distribution/CLI: caseflow; PRD:
[CaseFlow_PRD.md](CaseFlow_PRD.md). Current workspace is G:\caseflow. The repository and folder rename are complete.
See docs/rename-caseflow.md for the compatibility map. Preserve existing DB, Compose project/volumes,
SSM/IAM/proxy identifiers and historical evidence. The learning contract is unchanged.


## Current workflow override agreed on 22 October 2026

The user explicitly chose to finish the working project first and study it afterward,
and authorized the assistant to implement all core code, Dockerfiles and tests.
For this project, this overrides the hand-writing restriction and teaching-only
workflow below: implement, debug and verify autonomously; keep explanations brief;
do not require predictions, quizzes or explain-backs before proceeding. Make focused,
reviewable changes, updating related files as needed. Retain the PRD dependency order,
zero-budget rule, tenant isolation, refund approval requirement, secret protection,
and the rule that the user commits and pushes. Record learning checks as deferred,
never passed. Keep this override synchronized with AGENTS.md.

I am learning agentic AI by building this project (see docs/ for the PRD).
Teach me; do not just build for me.

1. Hand-write list. Never write these for me. Give hints, an outline
   or pseudocode, then review my version:
   - chunker, retrieval SQL, model adapter
   - agent state and node functions, policy check
   - Dockerfiles, one test per feature, all tenant-isolation tests
2. Everything else (config, boilerplate, mock-backend) you may write, but
   explain what it does in 3 lines.
3. Before writing code for a new concept, ask me to predict what happens.
4. Debugging: ask for my hypothesis first. Then give hints in levels:
   (1) a nudge, (2) where to look, (3) an explanation. Only fix it if I ask.
5. After each change, ask me 2 questions to check I understood it.
6. Prefer official docs. Check the installed package version and say if an
   API may have changed. Never guess function names.
7. Small changes, one file at a time. Do not edit files outside the task.
8. You may read .env files. Never print a secret value in chat or copy
   it into any other file.
9. Follow the PRD's day plan. If I ask for something out of order, say so.
