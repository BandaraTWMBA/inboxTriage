from __future__ import annotations

import argparse

from inboxtriage.sync import sync_recent_messages


def main():
    parser = argparse.ArgumentParser(description="InboxTriage sync utility")
    parser.add_argument("--days", type=int, default=1, help="Number of days of recent emails to sync")
    parser.add_argument("--limit", type=int, default=20, help="Maximum messages to pull")
    args = parser.parse_args()

    synced_count = sync_recent_messages(lookback_days=args.days, max_results=args.limit)
    print(f"Synced {synced_count} recent messages")


if __name__ == "__main__":
    main()
