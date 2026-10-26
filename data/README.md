# Fictional help center

Every policy, organization and business term here is invented for this demo. Do not
use these articles as real shopping, legal or financial advice. No actual customer
information, account credentials or real order data belongs in this directory.

## Corpus

Day 6 also adds `mock/entities.json`: 3 fictional customers, 5 orders and 4
tickets across Northwind and Contoso. Monetary amounts are integer USD cents;
dates/statuses are frozen fixtures, not current business facts. Seed them into
the local database with `copilot seed-mock`; repeated seeds insert missing rows
without replacing operator edits. They are not part of the help-center embedding
corpus, and no refund execution or actual customer information is present.

- `northwind/`: 15 Markdown help articles covering returns, shipping, cancellation,
  damaged items, missing parcels, exchanges, payments, promotions, gifts, address
  changes, sizing, warranty, product care, account privacy and contacting support.
- `contoso/`: three isolation fixtures. Returns, shipping and damaged-item rules
  deliberately differ from Northwind's rules. These files reuse Northwind document
  ids so an incorrect join or missing tenant filter will be exposed by tests.

An article filename is its id. The first line must be a `# Title`. The trusted local
CLI supplies the tenant explicitly; file contents cannot select or change tenants.
Only direct `.md` children are loaded. The containing directory is an explicit
trusted-admin argument, not input accepted from a customer or model.

## Import

After `copilot init-db`, run from the repository root:

```powershell
uv run --frozen copilot ingest --tenant northwind --directory data/northwind
uv run --frozen copilot ingest --tenant contoso --directory data/contoso
```

The baseline is 800-character windows with 120-character overlap. Original text is
preserved, including whitespace, and windows may split words. The article title is
prefixed when embedding each window, but stored chunk text retains the original
substring. These are character sizes, not tokenizer counts. The controlled English
corpus is small; token-aware limits for arbitrary input are not implemented here.

Each batch is validated and embedded before replacements are applied inside one
transaction. Re-running with the same inputs replaces existing chunks rather than
appending duplicates; changed chunk sizes remove obsolete chunks for those documents.
Files removed from the directory are not deleted from the database automatically.
The importer never deletes documents outside the batch or changes another tenant.

The Day 1 three-article experiment uses its own `northwind-day1-demo` tenant, so
running `copilot check-search` cannot replace the full help-center articles.

## Evaluation provenance

`evals/retrieval/questions.jsonl` contains 40 answerable questions with expected
article ids and 10 unanswerable questions with null article ids. These are
assistant-authored synthetic development examples, not a held-out human-authored
benchmark. Day 3 results are in `evals/results/day-03-retrieval.md`; validate labels
independently before treating them as evidence of broader real-world quality.
