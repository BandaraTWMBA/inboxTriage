"""
Evaluation Runner for Feature 03.
Runs offline/isolated evaluations against golden_set.jsonl.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from inboxtriage.classification.agent import classify_email
from inboxtriage.core.schemas import VALID_CATEGORIES
from inboxtriage.evaluation.judge import score_action_items
from inboxtriage.evaluation.metrics import CATEGORY_ORDER, compute_metrics, format_confusion_matrix

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("eval")


def load_golden_set(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Golden dataset not found at {path}")
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as err:
                logger.warning("Skipping invalid JSON on line %d of %s: %s", line_num, path, err)
    return items


def append_eval_log(
    log_dir: Path,
    record: dict[str, Any],
) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = log_dir / "eval_history.jsonl"
    csv_path = log_dir / "eval_history.csv"

    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    logger.info("Appended eval run to %s", jsonl_path)

    csv_fields = [
        "timestamp",
        "prompt_version",
        "sample_count",
        "accuracy",
        "macro_f1",
        "weighted_f1",
        "judge_action_score_mean",
        "validation_failures",
        "change_notes",
    ]
    file_exists = csv_path.exists()
    row = {
        "timestamp": record["timestamp"],
        "prompt_version": record["prompt_version"],
        "sample_count": record["sample_count"],
        "accuracy": record["accuracy"],
        "macro_f1": record["macro_f1"],
        "weighted_f1": record["weighted_f1"],
        "judge_action_score_mean": record.get("judge_action_score_mean", ""),
        "validation_failures": record.get("validation_failures", 0),
        "change_notes": record.get("change_notes", ""),
    }
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    logger.info("Appended eval run to %s", csv_path)


def run_evaluation(
    golden_set_path: Path,
    prompt_version: str = "v1",
    evaluate_judge: bool = True,
    change_notes: str = "",
    limit: Optional[int] = None,
) -> dict[str, Any]:
    logger.info("Loading golden set from %s...", golden_set_path)
    golden_items = load_golden_set(golden_set_path)
    if limit:
        golden_items = golden_items[:limit]
    logger.info("Evaluating %d samples under prompt_version='%s'...", len(golden_items), prompt_version)

    y_true: list[str] = []
    y_pred: list[str] = []
    judge_scores: list[int] = []
    validation_failures = 0

    predictions_detail: list[dict[str, Any]] = []

    for idx, item in enumerate(golden_items, 1):
        mid = item.get("message_id", f"msg_{idx}")
        true_cat = item["true_category"]
        sender = item.get("sender", "")
        subject = item.get("subject", "")
        body = item.get("body", "")

        pred = classify_email(
            gmail_id=mid,
            sender=sender,
            subject=subject,
            body=body,
        )

        if pred is None:
            predicted_cat = "failed_validation"
            validation_failures += 1
            action_items: list[str] = []
            confidence = 0.0
            reasoning = "Failed schema validation twice"
        else:
            predicted_cat = pred.category
            action_items = pred.action_items
            confidence = pred.confidence
            reasoning = pred.reasoning

        y_true.append(true_cat)
        y_pred.append(predicted_cat)

        judge_score = None
        judge_critique = None
        if evaluate_judge and pred is not None:
            judge_score, judge_critique = score_action_items(
                sender=sender,
                subject=subject,
                body=body,
                action_items=action_items,
            )
            judge_scores.append(judge_score)

        predictions_detail.append({
            "message_id": mid,
            "true_category": true_cat,
            "predicted_category": predicted_cat,
            "is_correct": (true_cat == predicted_cat),
            "confidence": confidence,
            "action_items": action_items,
            "reasoning": reasoning,
            "judge_score": judge_score,
            "judge_critique": judge_critique,
        })

    eval_categories = list(CATEGORY_ORDER)
    if "failed_validation" in y_pred:
        eval_categories.append("failed_validation")

    metrics = compute_metrics(y_true, y_pred, categories=eval_categories)
    mean_judge_score = round(sum(judge_scores) / len(judge_scores), 2) if judge_scores else None

    print("\n" + "=" * 60)
    print(f"EVALUATION RESULTS — Prompt Version: {prompt_version}")
    print("=" * 60)
    print(f"Total Samples: {len(golden_items)}")
    print(f"Accuracy:      {metrics['accuracy']:.2%}")
    print(f"Macro F1:      {metrics['macro_f1']:.4f}")
    print(f"Weighted F1:   {metrics['weighted_f1']:.4f}")
    if mean_judge_score is not None:
        print(f"Action Completeness (Judge 1-5): {mean_judge_score} / 5.0")
    print(f"Validation Failures: {validation_failures}")
    print("\nDetailed Classification Report:\n")
    print(metrics["report_text"])
    print("Confusion Matrix:")
    print(format_confusion_matrix(metrics["confusion_matrix"], eval_categories))
    print("=" * 60 + "\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "prompt_version": prompt_version,
        "sample_count": len(golden_items),
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "weighted_f1": metrics["weighted_f1"],
        "category_metrics": metrics["category_metrics"],
        "confusion_matrix": metrics["confusion_matrix"],
        "judge_action_score_mean": mean_judge_score,
        "validation_failures": validation_failures,
        "change_notes": change_notes,
    }

    log_dir = golden_set_path.parent
    append_eval_log(log_dir, record)

    return {
        "record": record,
        "metrics": metrics,
        "details": predictions_detail,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate classification agent against golden set")
    parser.add_argument(
        "--golden-set",
        type=Path,
        default=Path("data/golden_set.jsonl"),
        help="Path to golden set jsonl",
    )
    parser.add_argument(
        "--prompt-version",
        type=str,
        default="v1",
        help="Prompt version tag (e.g. v1, v2, v3)",
    )
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Skip LLM-as-a-judge action scoring to save API calls",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Description of what changed for this run",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of samples evaluated",
    )
    args = parser.parse_args()

    run_evaluation(
        golden_set_path=args.golden_set,
        prompt_version=args.prompt_version,
        evaluate_judge=not args.no_judge,
        change_notes=args.notes,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()

