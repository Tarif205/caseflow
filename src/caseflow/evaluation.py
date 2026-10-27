"""Pure evaluation helpers; abstention here is a retrieval-score gate, not an LLM answer."""

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from caseflow.ingestion import SLUG


@dataclass(frozen=True)
class Question:
    id: str
    tenant: str
    question: str
    expected_doc: str | None
    answerable: bool


def load_questions(path: Path) -> list[Question]:
    records = []
    ids = set()
    fields = {"id", "tenant", "question", "expected_doc", "answerable"}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on question line {number}") from exc
        if not isinstance(raw, dict) or set(raw) != fields:
            raise ValueError(f"Unexpected fields on question line {number}")
        if any(
            not isinstance(raw[k], str) or not raw[k].strip() for k in ("id", "tenant", "question")
        ):
            raise ValueError(f"Question line {number} needs nonempty id, tenant and question")
        if not SLUG.fullmatch(raw["tenant"]) or len(raw["question"]) > 2000:
            raise ValueError(f"Invalid tenant or oversized question on line {number}")
        expected = raw["expected_doc"]
        if type(raw["answerable"]) is not bool:
            raise ValueError(f"answerable must be a boolean on line {number}")
        if raw["answerable"]:
            if not isinstance(expected, str) or not SLUG.fullmatch(expected):
                raise ValueError(f"Answerable question line {number} needs an article id")
        elif expected is not None:
            raise ValueError(f"Unanswerable question line {number} must have a null article id")
        if raw["id"] in ids:
            raise ValueError(f"Duplicate question id on line {number}")
        ids.add(raw["id"])
        records.append(Question(**raw))
    if not records:
        raise ValueError("Question set is empty")
    return records


def summarize_retrieval(rows: Sequence[dict], top_k: int = 5) -> dict:
    """Each row contains answerability, expected_doc and ranked chunk hits.

    Metrics use the first relevant chunk's position, including duplicate-article
    chunks in the ranked list. Recall@5 is always evaluated from at least five hits.
    """
    if type(top_k) is not int or not 1 <= top_k <= 20:
        raise ValueError("top_k must be an integer between 1 and 20")
    answerable = [r for r in rows if r["answerable"]]
    if not answerable:
        raise ValueError("At least one answerable question is required")

    def rank(row, k):
        return next(
            (
                i
                for i, hit in enumerate(row["hits"][:k], 1)
                if hit["document_id"] == row["expected_doc"]
            ),
            None,
        )

    ranks = [rank(row, top_k) for row in answerable]
    ranks5 = [rank(row, 5) for row in answerable]
    count = len(answerable)
    return {
        "answerable_questions": count,
        "unanswerable_questions": len(rows) - count,
        "top_k": top_k,
        "recall_at_k": sum(r is not None for r in ranks) / count,
        "recall_at_5": sum(r is not None for r in ranks5) / count,
        "mrr_at_k": sum(1 / r for r in ranks if r is not None) / count,
        "mrr_at_5": sum(1 / r for r in ranks5 if r is not None) / count,
        "top1_accuracy": sum(r == 1 for r in ranks5) / count,
    }


def score_gate(rows: Sequence[dict], threshold: float) -> dict:
    if not math.isfinite(threshold):
        raise ValueError("Threshold must be finite")
    positives = [r for r in rows if r["answerable"]]
    negatives = [r for r in rows if not r["answerable"]]
    if not positives or not negatives:
        raise ValueError("Threshold analysis needs both answerable and unanswerable examples")

    def accepts(row):
        return bool(row["hits"]) and row["hits"][0]["score"] >= threshold

    accepted = sum(accepts(r) for r in positives)
    rejected = sum(not accepts(r) for r in negatives)
    return {
        "threshold": threshold,
        "answerable_acceptance": accepted / len(positives),
        "answerable_false_rejections": len(positives) - accepted,
        "unanswerable_rejection": rejected / len(negatives),
        "unanswerable_false_acceptances": len(negatives) - rejected,
        "balanced_accuracy": (accepted / len(positives) + rejected / len(negatives)) / 2,
    }


def calibrate_score_gate(rows: Sequence[dict]) -> dict:
    scores = sorted({r["hits"][0]["score"] for r in rows if r["hits"]})
    # Midpoints keep the selected threshold away from a rounded example score.
    # Include both extremes to evaluate accepting everything or rejecting everything.
    candidates = sorted(
        {-1.000001, 1.000001} | {(lower + upper) / 2 for lower, upper in pairwise(scores)}
    )
    sweep = [score_gate(rows, threshold) for threshold in candidates]
    best = max(
        sweep, key=lambda r: (r["balanced_accuracy"], r["answerable_acceptance"], -r["threshold"])
    )
    return {
        "selection": "maximum balanced accuracy; ties prefer answerable acceptance then lower threshold",
        "provenance": "in-sample synthetic development calibration; not held-out validation",
        "recommended": best,
        "sweep": sweep,
    }
