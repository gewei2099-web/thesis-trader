"""Fetch A-share closing prices and update positions.json."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.storage import DataStore  # noqa: E402


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().split(".")[0].zfill(6)


def fetch_prices(symbols: list[str]) -> dict[str, float]:
    import akshare as ak

    spot = ak.stock_zh_a_spot_em()
    code_col = "代码" if "代码" in spot.columns else spot.columns[0]
    price_col = "最新价" if "最新价" in spot.columns else "最新"

    prices: dict[str, float] = {}
    for raw in symbols:
        code = _normalize_symbol(raw)
        rows = spot[spot[code_col].astype(str).str.zfill(6) == code]
        if rows.empty:
            print(f"Warning: no price for {code}")
            continue
        prices[code] = float(rows.iloc[0][price_col])
    return prices


def update_positions(root: Path | None = None) -> int:
    store = DataStore(root or ROOT)
    positions = store.load_positions()
    if not positions.items:
        print("No positions to update.")
        return 0

    symbols = [_normalize_symbol(p.symbol) for p in positions.items]
    prices = fetch_prices(symbols)

    updated = 0
    for pos in positions.items:
        code = _normalize_symbol(pos.symbol)
        if code in prices:
            pos.current_price = prices[code]
            pos.symbol = code
            updated += 1
            print(f"Updated {code}: {prices[code]}")

    store.save_positions(positions)
    print(f"Updated {updated}/{len(positions.items)} positions on {date.today()}")
    return updated


if __name__ == "__main__":
    update_positions()
