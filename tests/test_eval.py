from pathlib import Path
import json

from inboxtriage.evaluation.metrics import compute_metrics, format_confusion_matrix
from inboxtriage.evaluation.runner import append_eval_log


def test_compute_metrics_exact_accuracy():
    y_true = ["urgent_action", "fyi", "can_wait", "low_priority"]
    y_pred = ["urgent_action", "fyi", "can_wait", "low_priority"]
    categories = ["urgent_action", "fyi", "can_wait", "low_priority"]

    metrics = compute_metrics(y_true, y_pred, categories=categories)
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["category_metrics"]["urgent_action"]["precision"] == 1.0
    assert metrics["category_metrics"]["urgent_action"]["recall"] == 1.0


def test_compute_metrics_with_misclassifications():
    y_true = ["urgent_action", "urgent_action", "fyi", "can_wait"]
    y_pred = ["urgent_action", "fyi", "fyi", "can_wait"]
    categories = ["urgent_action", "fyi", "can_wait", "low_priority"]

    metrics = compute_metrics(y_true, y_pred, categories=categories)
    assert metrics["accuracy"] == 0.75
    assert metrics["category_metrics"]["urgent_action"]["recall"] == 0.5
    assert metrics["category_metrics"]["urgent_action"]["precision"] == 1.0


def test_compute_metrics_with_failed_validation():
    y_true = ["urgent_action", "fyi"]
    y_pred = ["failed_validation", "fyi"]
    categories = ["urgent_action", "fyi", "failed_validation"]

    metrics = compute_metrics(y_true, y_pred, categories=categories)
    assert metrics["accuracy"] == 0.5
    assert metrics["category_metrics"]["urgent_action"]["recall"] == 0.0


def test_format_confusion_matrix_returns_nonempty_string():
    conf_mat = [[1, 0], [0, 1]]
    text = format_confusion_matrix(conf_mat, ["cat_a", "cat_b"])
    assert "cat_a" in text
    assert "cat_b" in text


def test_append_eval_log_does_not_overwrite(tmp_path: Path):
    rec1 = {
        "timestamp": "2026-11-04T10:00:00Z",
        "prompt_version": "v1",
        "sample_count": 10,
        "accuracy": 0.8,
        "macro_f1": 0.75,
        "weighted_f1": 0.78,
        "change_notes": "First test",
    }
    rec2 = {
        "timestamp": "2026-11-04T11:00:00Z",
        "prompt_version": "v2",
        "sample_count": 10,
        "accuracy": 0.9,
        "macro_f1": 0.88,
        "weighted_f1": 0.89,
        "change_notes": "Second test",
    }

    append_eval_log(tmp_path, rec1)
    append_eval_log(tmp_path, rec2)

    jsonl_lines = (tmp_path / "eval_history.jsonl").read_text(encoding="utf-8").strip().split("\n")
    assert len(jsonl_lines) == 2
    assert json.loads(jsonl_lines[0])["prompt_version"] == "v1"
    assert json.loads(jsonl_lines[1])["prompt_version"] == "v2"

    csv_lines = (tmp_path / "eval_history.csv").read_text(encoding="utf-8").strip().split("\n")
    assert len(csv_lines) == 3
