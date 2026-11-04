from __future__ import annotations

from typing import Any
from sklearn.metrics import classification_report, confusion_matrix

CATEGORY_ORDER = ["urgent_action", "fyi", "can_wait", "low_priority"]


def compute_metrics(
    y_true: list[str],
    y_pred: list[str],
    categories: list[str] = CATEGORY_ORDER,
) -> dict[str, Any]:
    report_dict = classification_report(
        y_true,
        y_pred,
        labels=categories,
        output_dict=True,
        zero_division=0,
    )
    conf_mat = confusion_matrix(y_true, y_pred, labels=categories)

    accuracy = report_dict.get("accuracy", 0.0)
    macro_f1 = report_dict.get("macro avg", {}).get("f1-score", 0.0)
    weighted_f1 = report_dict.get("weighted avg", {}).get("f1-score", 0.0)

    category_metrics = {}
    for cat in categories:
        if cat in report_dict:
            category_metrics[cat] = {
                "precision": round(report_dict[cat]["precision"], 3),
                "recall": round(report_dict[cat]["recall"], 3),
                "f1": round(report_dict[cat]["f1-score"], 3),
                "support": report_dict[cat]["support"],
            }

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "category_metrics": category_metrics,
        "confusion_matrix": conf_mat.tolist(),
        "report_text": classification_report(y_true, y_pred, labels=categories, digits=3, zero_division=0),
    }


def format_confusion_matrix(conf_mat: list[list[int]], categories: list[str]) -> str:
    col_width = 15
    header = f"{'True \\ Pred':<{col_width}}" + "".join(f"{cat:>{col_width}}" for cat in categories)
    lines = [header, "-" * len(header)]
    for idx, true_cat in enumerate(categories):
        row = f"{true_cat:<{col_width}}" + "".join(f"{conf_mat[idx][c_idx]:>{col_width}}" for c_idx in range(len(categories)))
        lines.append(row)
    return "\n".join(lines)

