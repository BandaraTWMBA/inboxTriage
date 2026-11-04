from __future__ import annotations

import argparse
import sys

from inboxtriage.db import get_session
from inboxtriage.digest import fetch_digest_data, generate_digest_markdown
from inboxtriage.digest_delivery import deliver_to_file
from inboxtriage.sync import sync_recent_messages


def main():
    parser = argparse.ArgumentParser(description="InboxTriage CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync recent messages from Gmail")
    sync_parser.add_argument("--days", type=int, default=1, help="Lookback days")
    sync_parser.add_argument("--limit", type=int, default=20, help="Max messages to pull")

    # digest command
    digest_parser = subparsers.add_parser("digest", help="Generate and deliver daily digest")
    digest_parser.add_argument("--hours", type=int, default=24, help="Lookback window in hours (default 24)")
    digest_parser.add_argument("--output", type=str, default=None, help="Output file path (default reports/digest_YYYY-MM-DD.md)")
    digest_parser.add_argument("--stdout", action="store_true", help="Print digest to stdout")

    args = parser.parse_args()

    if args.command == "sync":
        synced = sync_recent_messages(lookback_days=args.days, max_results=args.limit)
        print(f"Synced {synced} recent messages")
    elif args.command == "digest":
        with get_session() as session:
            data = fetch_digest_data(session=session, hours=args.hours)
            markdown = generate_digest_markdown(data)

        if args.stdout:
            print("\n" + markdown)
        else:
            path = deliver_to_file(markdown, args.output)
            print(f"Digest generated successfully: {path}")
    else:
        # Fallback / backward-compat default
        parser.print_help()


if __name__ == "__main__":
    main()
