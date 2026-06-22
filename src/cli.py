"""CLI entry for thesis-trader."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from src.discipline.layer import build_alerts, log_alerts
from src.engine.decision import evaluate_all
from src.review.daily import run_daily_review
from src.storage import DataStore


def cmd_decisions(store: DataStore) -> None:
    positions = store.load_positions().items
    thesis_map = {t.symbol: t for t in store.load_all_thesis()}
    decisions = evaluate_all(positions, thesis_map)
    alerts = build_alerts(decisions, thesis_map)
    print(json.dumps({"decisions": [d.model_dump(mode="json") for d in decisions]}, ensure_ascii=False, indent=2))
    if alerts:
        print("\n=== 纪律提醒 ===")
        for a in alerts:
            print(f"- {a.message}")


def cmd_review(store: DataStore, market_info: str) -> None:
    review, markdown = run_daily_review(store, market_info)
    log = store.load_discipline_log()
    thesis_map = {t.symbol: t for t in store.load_all_thesis()}
    log_alerts(log, build_alerts(review.decisions, thesis_map))
    store.save_discipline_log(log)
    print(markdown)


def main() -> None:
    parser = argparse.ArgumentParser(description="thesis-trader CLI")
    parser.add_argument("command", choices=["decisions", "review", "build-pages"])
    parser.add_argument("--market-info", default="", help="Paste market info for daily review")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    store = DataStore(root)

    if args.command == "decisions":
        cmd_decisions(store)
    elif args.command == "review":
        cmd_review(store, args.market_info)
    elif args.command == "build-pages":
        import subprocess
        subprocess.run([sys.executable, str(root / "scripts" / "build_pages.py")], check=True)


if __name__ == "__main__":
    main()
