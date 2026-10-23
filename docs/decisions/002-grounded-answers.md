# 002: Return verified source quotations

Date: 22 October 2026.

Context: retrieval can return related policies for questions whose actual answer
is absent, such as a specific order's refund approval date. A high similarity score
cannot establish that the corpus answers the question.

Options: allow free-form model prose with citation ids; or ask the model to select
verbatim evidence and construct the response from validated quotations.

Decision: use extractive quotations for the first Knowledge API. Validate the JSON
schema, ensure selected chunk ids belong to the authenticated tenant's retrieved
context, match quotes to source text allowing only whitespace normalization, and
return the original matched substring. Reject invalid evidence. Skip generation
for evidence below the provisional threshold and for concrete order references.

Why: this gives an auditable link between each returned claim's words and source
material, while limiting unverified prose from a small or hosted model. Adapters
support local Ollama and HTTPS-compatible hosted inference without changing routes.

Consequences: answers are less conversational and can omit relevant material. A
real source quote can still be irrelevant or incomplete; this is not a semantic
correctness guarantee. The order-reference rule is a conservative heuristic, not
an order lookup. Independent answer/refusal evaluation is still needed. Keep
800/120 chunks rather than selecting larger chunks based only on retrieval MRR.

Reconsider when: reviewed answer evaluations show unacceptable omissions, irrelevant
quotes, excessive refusal or a clear benefit from verified paraphrasing.
