"""Merge phone-local export into desktop data store."""

from __future__ import annotations

from datetime import date
from typing import Any

from src.models.enums import FundamentalState, MarketSentiment, TrendState
from src.models.positions import Position, Positions
from src.storage import DataStore


def import_local_payload(store: DataStore, payload: dict[str, Any]) -> dict[str, int]:
    raw_items = payload.get("positions") or []
    if not raw_items:
        raise ValueError("导入数据中没有 positions")

    items: list[Position] = []
    for raw in raw_items:
        opened = raw.get("opened_at")
        items.append(
            Position(
                symbol=str(raw["symbol"]).strip(),
                name=str(raw.get("name") or ""),
                shares=float(raw["shares"]),
                avg_cost=float(raw["avg_cost"]),
                current_price=float(raw["current_price"]),
                trend=TrendState(raw.get("trend", "range")),
                fundamental_state=FundamentalState(raw.get("fundamental_state", "unchanged")),
                market_sentiment=MarketSentiment(raw.get("market_sentiment", "medium")),
                opened_at=date.fromisoformat(opened) if opened else date.today(),
                notes=str(raw.get("notes") or ""),
            )
        )

    store.save_positions(Positions(items=items))
    return {"positions": len(items)}
