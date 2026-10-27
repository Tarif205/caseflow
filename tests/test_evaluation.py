import json

import pytest

from caseflow.evaluation import (
    Question,
    calibrate_score_gate,
    load_questions,
    score_gate,
    summarize_retrieval,
)
from caseflow.experiments import Experiment, evaluate_experiment
from caseflow.ingestion import Article


def row(answerable, expected, scores_and_ids):
    return {
        "answerable": answerable,
        "expected_doc": expected,
        "hits": [{"score": score, "document_id": doc} for score, doc in scores_and_ids],
    }


def test_recall_and_reciprocal_rank_use_chunks_and_exclude_unanswerables():
    rows = [
        row(True, "returns", [(0.9, "shipping"), (0.8, "shipping"), (0.7, "returns")]),
        row(True, "gifts", [(0.6, "returns")]),
        row(False, None, [(0.5, "gifts")]),
    ]
    result = summarize_retrieval(rows)
    assert result["answerable_questions"] == 2
    assert result["unanswerable_questions"] == 1
    assert result["recall_at_5"] == 0.5
    assert result["mrr_at_5"] == pytest.approx(1 / 6)
    assert result["top1_accuracy"] == 0
    smaller = summarize_retrieval(rows, top_k=2)
    assert smaller["recall_at_k"] == 0
    assert smaller["mrr_at_k"] == 0
    assert smaller["recall_at_5"] == 0.5


def test_empty_search_results_count_as_misses():
    assert summarize_retrieval([row(True, "returns", [])])["recall_at_5"] == 0


@pytest.mark.parametrize("k", [0, -1, 21, True, 1.5])
def test_invalid_metric_cutoff_rejected(k):
    with pytest.raises(ValueError):
        summarize_retrieval([row(True, "returns", [])], k)


def test_metric_requires_answerable_examples():
    with pytest.raises(ValueError):
        summarize_retrieval([row(False, None, [])])


def test_threshold_equality_and_false_acceptance_are_counted():
    rows = [row(True, "a", [(0.8, "a")]), row(False, None, [(0.8, "b")])]
    gate = score_gate(rows, 0.8)
    assert gate["answerable_acceptance"] == 1
    assert gate["unanswerable_rejection"] == 0
    assert gate["unanswerable_false_acceptances"] == 1
    assert gate["balanced_accuracy"] == 0.5


def test_score_gate_does_not_confuse_acceptance_with_correct_retrieval():
    gate = score_gate([row(True, "a", [(0.9, "wrong")]), row(False, None, [])], 0.8)
    assert gate["answerable_acceptance"] == 1
    assert gate["unanswerable_rejection"] == 1
    # Correctness is evaluated by separate retrieval metrics, not by the score alone.


def test_calibration_exposes_tradeoff_and_is_deterministic():
    rows = [
        row(True, "a", [(0.9, "a")]),
        row(True, "b", [(0.7, "b")]),
        row(False, None, [(0.8, "a")]),
    ]
    result = calibrate_score_gate(rows)
    assert result == calibrate_score_gate(rows)
    best = result["recommended"]
    assert best["balanced_accuracy"] == 0.75
    assert best["answerable_acceptance"] == 0.5
    assert best["unanswerable_rejection"] == 1
    assert 0.8 < best["threshold"] < 0.9
    assert "in-sample" in result["provenance"]


@pytest.mark.parametrize("threshold", [float("nan"), float("inf")])
def test_nonfinite_threshold_rejected(threshold):
    with pytest.raises(ValueError):
        score_gate([row(True, "a", []), row(False, None, [])], threshold)


def test_gate_analysis_requires_both_classes():
    with pytest.raises(ValueError):
        calibrate_score_gate([row(True, "a", [])])


def valid_question():
    return {
        "id": "q1",
        "tenant": "northwind",
        "question": "Can I return it?",
        "expected_doc": "returns",
        "answerable": True,
    }


def test_jsonl_loader_accepts_null_expected_doc_only_for_unanswerable(tmp_path):
    path = tmp_path / "questions.jsonl"
    negative = {**valid_question(), "id": "q2", "expected_doc": None, "answerable": False}
    path.write_text(json.dumps(valid_question()) + "\n" + json.dumps(negative))
    records = load_questions(path)
    assert records[0].expected_doc == "returns"
    assert records[1].expected_doc is None


@pytest.mark.parametrize(
    "kind",
    [
        "invalid-json",
        "empty",
        "duplicate",
        "missing",
        "extra",
        "boolean",
        "blank",
        "article",
        "negative-article",
    ],
)
def test_bad_question_files_fail_before_experiment(tmp_path, kind):
    path = tmp_path / "questions.jsonl"
    question = valid_question()
    if kind == "missing":
        question.pop("tenant")
    elif kind == "extra":
        question["extra"] = "not allowed"
    elif kind == "boolean":
        question["answerable"] = "true"
    elif kind == "blank":
        question["question"] = " "
    elif kind == "article":
        question["expected_doc"] = None
    elif kind == "negative-article":
        question["answerable"] = False
    contents = json.dumps(question)
    if kind == "invalid-json":
        contents = "{broken"
    elif kind == "empty":
        contents = ""
    elif kind == "duplicate":
        contents += "\n" + contents
    path.write_text(contents)
    with pytest.raises(ValueError):
        load_questions(path)


@pytest.mark.integration
def test_experiment_rolls_back_copies_and_preserves_application_data(db):
    store, (tenant, _) = db
    vector = [1.0] + [0.0] * 383
    store.put_document(tenant, "original", "Original", "test", ["Keep this"], [vector])

    class FakeEmbedder:
        model_name = "test-model"
        dimension = 384

        def embed_documents(self, texts):
            return [vector for _ in texts]

    questions = [
        Question("a", "fixture", "How do I return?", "returns", True),
        Question("b", "fixture", "What is the weather?", None, False),
    ]
    result = evaluate_experiment(
        store.conn,
        FakeEmbedder(),
        {"fixture": [Article("returns", "Title", "test.md", "A return policy.")]},
        questions,
        {"a": vector, "b": vector},
        Experiment("test", 800, 120),
    )
    assert result["metrics"]["recall_at_5"] == 1
    assert result["identical_on_repeat"] is True
    assert store.search(tenant, vector)[0]["text"] == "Keep this"
    assert not store.conn.execute(
        "SELECT 1 FROM tenants WHERE id = 'retrieval-eval-fixture'"
    ).fetchone()


@pytest.mark.integration
def test_failed_experiment_rolls_back_partially_created_tenants(db):
    store, _ = db

    class BrokenEmbedder:
        model_name = "test-model"
        dimension = 384

        def embed_documents(self, texts):
            raise RuntimeError("Simulated embedding failure")

    with pytest.raises(RuntimeError):
        evaluate_experiment(
            store.conn,
            BrokenEmbedder(),
            {"fixture": [Article("returns", "Title", "test.md", "Body")]},
            [Question("a", "fixture", "Question", "returns", True)],
            {},
            Experiment("test", 800, 120),
        )
    assert not store.conn.execute(
        "SELECT 1 FROM tenants WHERE id = 'retrieval-eval-fixture'"
    ).fetchone()


@pytest.mark.integration
def test_experiment_refuses_existing_reserved_tenant_without_replacing_data(db):
    store, _ = db
    store.conn.execute(
        "INSERT INTO tenants (id, name) VALUES ('retrieval-eval-fixture', 'Existing')"
    )
    vector = [1.0] + [0.0] * 383
    store.put_document("retrieval-eval-fixture", "original", "Title", "test", ["Keep me"], [vector])

    class UnusedEmbedder:
        model_name = "test-model"
        dimension = 384

        def embed_documents(self, texts):
            pytest.fail("Existing reserved data must be rejected before embedding")

    with pytest.raises(ValueError, match="already exists"):
        evaluate_experiment(
            store.conn,
            UnusedEmbedder(),
            {"fixture": [Article("returns", "Title", "test.md", "Body")]},
            [Question("a", "fixture", "Question", "returns", True)],
            {},
            Experiment("test", 800, 120),
        )
    assert store.search("retrieval-eval-fixture", vector)[0]["text"] == "Keep me"
