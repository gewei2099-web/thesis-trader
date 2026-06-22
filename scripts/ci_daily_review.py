"""CI entry: run daily review using MARKET_INFO env var."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.discipline.layer import build_alerts, log_alerts  # noqa: E402
from src.review.daily import run_daily_review  # noqa: E402
from src.storage import DataStore  # noqa: E402


def main() -> None:
    store = DataStore(ROOT)
    market_info = os.environ.get("MARKET_INFO", "").strip()
    review, markdown = run_daily_review(store, market_info)

    log = store.load_discipline_log()
    thesis_map = {t.symbol: t for t in store.load_all_thesis()}
    log_alerts(log, build_alerts(review.decisions, thesis_map))
    store.save_discipline_log(log)

    print(f"Review generated for {review.review_date}")
    print(f"Market info length: {len(market_info)} chars")
    print(f"Discipline alerts: {len(review.discipline_alerts)}")
    print("---")
    print(markdown[:500] + ("..." if len(markdown) > 500 else ""))


if __name__ == "__main__":
    main()
