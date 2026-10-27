"""Reproducible local retrieval experiments over synthetic development questions."""

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict

from caseflow.config import PROJECT_ROOT, Settings
from caseflow.database import KnowledgeStore, connect
from caseflow.embeddings import Embeddings, FastEmbedAdapter
from caseflow.evaluation import (
    Question,
    calibrate_score_gate,
    load_questions,
    summarize_retrieval,
)
from caseflow.ingestion import Article, ingest_articles, load_articles


@dataclass(frozen=True)
class Experiment:
    name: str
    chunk_size: int
    overlap: int
    top_k: int = 5


EXPERIMENTS = [
    Experiment("baseline", 800, 120),
    Experiment("smaller-chunks", 400, 120),
    Experiment("larger-chunks", 1200, 120),
    Experiment("no-overlap", 800, 0),
    Experiment("top-three", 800, 120, 3),
]


def evaluate_experiment(
    conn,
    embedder: Embeddings,
    corpora: dict[str, list[Article]],
    questions: list[Question],
    query_vectors: dict[str, list[float]],
    experiment: Experiment,
) -> dict:
    for question in questions:
        if question.tenant not in corpora:
            raise ValueError("Question names a tenant without a corpus")
        ids = {a.id for a in corpora[question.tenant]}
        if question.answerable and question.expected_doc not in ids:
            raise ValueError("Question references an unknown expected article")

    # Separate fixed tenant names make tied ranks reproducible. The transaction-level
    # lock serializes experiment copies, and the savepoint always rolls them back.
    with conn.transaction(force_rollback=True):
        conn.execute("SELECT pg_advisory_xact_lock(22032026)")
        store = KnowledgeStore(conn, embedder.model_name)
        tenant_map = {tenant: f"retrieval-eval-{tenant}" for tenant in corpora}
        chunk_counts = {}
        for tenant, articles in corpora.items():
            temporary = tenant_map[tenant]
            if conn.execute("SELECT 1 FROM tenants WHERE id = %s", (temporary,)).fetchone():
                raise ValueError("Reserved evaluation tenant already exists; no data was replaced")
            conn.execute("INSERT INTO tenants (id, name) VALUES (%s, %s)", (temporary, temporary))
            imported = ingest_articles(
                store, embedder, temporary, articles, experiment.chunk_size, experiment.overlap
            )
            chunk_counts[tenant] = imported["chunks"]

        def retrieve():
            rows = []
            for question in questions:
                hits = store.search(
                    tenant_map[question.tenant],
                    query_vectors[question.id],
                    max(5, experiment.top_k),
                )
                sources = {a.id: a.text for a in corpora[question.tenant]}
                if any(
                    h["document_id"] not in sources or h["text"] not in sources[h["document_id"]]
                    for h in hits
                ):
                    raise RuntimeError("An evaluation hit is outside the requested tenant corpus")
                rows.append(
                    {
                        **asdict(question),
                        "hits": [
                            {
                                "chunk_id": h["id"],
                                "document_id": h["document_id"],
                                "score": round(h["score"], 8),
                            }
                            for h in hits
                        ],
                    }
                )
            return rows

        rows = retrieve()
        repeated = retrieve()
        if rows != repeated:
            raise RuntimeError("Repeated retrieval changed rankings or scores")
        return {
            "configuration": asdict(experiment),
            "chunk_counts": chunk_counts,
            "metrics": summarize_retrieval(rows, experiment.top_k),
            "identical_on_repeat": True,
            "score_gate": calibrate_score_gate(rows),
            "questions": rows,
        }


def run(settings: Settings, question_path: Path) -> dict:
    target = conninfo_to_dict(settings.database_url)
    if (
        target.get("host") not in {"127.0.0.1", "localhost", "::1"}
        or target.get("dbname") != "copilot"
    ):
        raise ValueError("Experiments require the local copilot development database")
    questions = load_questions(question_path)
    corpora = {
        tenant: load_articles(PROJECT_ROOT / "data" / tenant) for tenant in ("northwind", "contoso")
    }
    inputs = {
        "questions": [asdict(q) for q in questions],
        "articles": {tenant: [asdict(a) for a in articles] for tenant, articles in corpora.items()},
    }
    fingerprint = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    embedder = FastEmbedAdapter(settings)
    vectors = {question.id: embedder.embed_query(question.question) for question in questions}
    with connect(settings) as conn:
        results = [
            evaluate_experiment(conn, embedder, corpora, questions, vectors, experiment)
            for experiment in EXPERIMENTS
        ]
    best = max(
        results,
        key=lambda result: (
            result["metrics"]["recall_at_5"],
            result["metrics"]["mrr_at_5"],
            result["metrics"]["top1_accuracy"],
            -sum(result["chunk_counts"].values()),
        ),
    )
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "dataset_provenance": "assistant-authored synthetic development set; labels not independently reviewed",
        "input_sha256": fingerprint,
        "model": embedder.model_name,
        "versions": {name: version(name) for name in ("fastembed", "numpy", "psycopg", "pgvector")},
        "ranking_unit": "chunks; relevance is expected article id; duplicate article chunks occupy ranks",
        "retrieval_pool": "max(5, top_k), so Recall@5 is comparable even for the top-three experiment",
        "experiments": results,
        "recommended_configuration": best["configuration"],
        "selection": "maximize Recall@5 then MRR@5 then top1 accuracy then minimize total chunks",
        "limitations": [
            "Tuning and score-gate calibration use the same synthetic development set.",
            "Unanswerable rejection measures the score gate only, not generated answer faithfulness.",
            "No chat model, hosted inference or public API was used.",
        ],
    }


def write_summary(result: dict, path: Path) -> None:
    counts = result["experiments"][0]["metrics"]
    lines = [
        "# Retrieval development results",
        "",
        f"Measured at: {result['checked_at']}",
        "",
        f"Synthetic assistant-authored development set: {counts['answerable_questions']} answerable and {counts['unanswerable_questions']} unanswerable questions.",
        "Labels are not independently reviewed. These are in-sample results, not a held-out benchmark.",
        "",
        "| Experiment | Chars | Overlap | Context k | Northwind chunks | Recall@5 | MRR@5 | Top 1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for experiment in result["experiments"]:
        cfg, metrics = experiment["configuration"], experiment["metrics"]
        lines.append(
            f"| {cfg['name']} | {cfg['chunk_size']} | {cfg['overlap']} | {cfg['top_k']} | "
            f"{experiment['chunk_counts']['northwind']} | {metrics['recall_at_5']:.3f} | "
            f"{metrics['mrr_at_5']:.3f} | {metrics['top1_accuracy']:.3f} |"
        )
    lines += [
        "",
        "## Score gate calibration",
        "",
        "The threshold is selected in-sample for maximum balanced accuracy. It does not measure LLM answers.",
        "",
        "| Experiment | Threshold | Answerable accepted | Unanswerable rejected | Balanced accuracy |",
        "|---|---:|---:|---:|---:|",
    ]
    for experiment in result["experiments"]:
        gate = experiment["score_gate"]["recommended"]
        lines.append(
            f"| {experiment['configuration']['name']} | {gate['threshold']:.6f} | "
            f"{gate['answerable_acceptance']:.3f} | {gate['unanswerable_rejection']:.3f} | "
            f"{gate['balanced_accuracy']:.3f} |"
        )
    lines += [
        "",
        f"Recommended configuration: {json.dumps(result['recommended_configuration'], sort_keys=True)}.",
        "This recommendation optimizes retrieval ranks only. Its score gate can reject more answerable questions than another setting.",
        "The imported corpus and default importer settings remain at the Day 2 baseline pending API-level evaluation.",
        "",
        "All experiments reproduced identical rankings and rounded scores on a second query pass.",
        "Temporary evaluation tenants were rolled back; the imported corpus was not replaced.",
        "",
        "Recall@5 and MRR@5 use chunk positions, including repeated chunks from one article.",
        "The top-three experiment still fetches five hits for comparable @5 measurements; context uses three.",
        "The full per-question rankings, threshold sweep, package versions and input SHA256 are in day-03-retrieval.json.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions", type=Path, default=PROJECT_ROOT / "evals/retrieval/questions.jsonl"
    )
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "evals/results/day-03-retrieval.json"
    )
    parser.add_argument(
        "--summary", type=Path, default=PROJECT_ROOT / "evals/results/day-03-retrieval.md"
    )
    args = parser.parse_args()
    try:
        result = run(Settings.from_env(), args.questions)
    except psycopg.Error:
        parser.exit(1, "Database evaluation failed. Check local Docker and schema settings.\n")
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"Evaluation failed: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_summary(result, args.summary)
    print(
        json.dumps(
            {
                "recommended_configuration": result["recommended_configuration"],
                "experiments": [
                    {
                        "name": r["configuration"]["name"],
                        "metrics": r["metrics"],
                        "score_gate": r["score_gate"]["recommended"],
                    }
                    for r in result["experiments"]
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
