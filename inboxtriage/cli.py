"""
Unified CLI for InboxTriage.
Subcommands:
  sync: Pull recent messages from Gmail into local database
  classify: Run batch classification on unclassified messages
  eval: Run evaluation against golden dataset
"""
from __future__ import annotations

import argparse
from pathlib import Path

from inboxtriage.ingestion.service import sync_recent_messages
from inboxtriage.classification.batch_runner import run_batch
from inboxtriage.evaluation.runner import run_evaluation


def main():
    parser = argparse.ArgumentParser(description="InboxTriage management CLI")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # sync
    sync_p = subparsers.add_parser("sync", help="Sync recent emails from Gmail")
    sync_p.add_argument("--days", type=int, default=1, help="Lookback days")
    sync_p.add_argument("--limit", type=int, default=20, help="Max emails")

    # classify
    cls_p = subparsers.add_parser("classify", help="Batch classify emails")
    cls_p.add_argument("--dry-run", action="store_true", help="Preview classification without DB/label writes")

    # eval
    ev_p = subparsers.add_parser("eval", help="Evaluate prompt against golden set")
    ev_p.add_argument("--golden-set", type=Path, default=Path("data/golden_set.jsonl"), help="Golden set path")
    ev_p.add_argument("--prompt-version", type=str, default="v1", help="Prompt version")
    ev_p.add_argument("--no-judge", action="store_true", help="Skip LLM-as-a-judge")
    ev_p.add_argument("--notes", type=str, default="", help="Experiment change notes")
    ev_p.add_argument("--limit", type=int, default=None, help="Limit sample count")

    args = parser.parse_args()

    if args.subcommand == "sync":
        count = sync_recent_messages(lookback_days=args.days, max_results=args.limit)
        print(f"Synced {count} messages from Gmail.")
    elif args.subcommand == "classify":
        run_batch(dry_run=args.dry_run)
    elif args.subcommand == "eval":
        run_evaluation(
            golden_set_path=args.golden_set,
            prompt_version=args.prompt_version,
            evaluate_judge=not args.no_judge,
            change_notes=args.notes,
            limit=args.limit,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
