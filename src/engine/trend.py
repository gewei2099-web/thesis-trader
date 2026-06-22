"""Simplified trend rules without complex indicators."""

from __future__ import annotations

from src.models.enums import TrendState
from src.models.positions import Position


def is_right_side_trend(trend: TrendState) -> bool:
    return trend == TrendState.UP


def evaluate_trend(
    *,
    trend: TrendState,
    return_pct: float,
    made_new_high: bool | None = None,
    made_new_low: bool | None = None,
) -> dict:
    notes: list[str] = []
    right_side = is_right_side_trend(trend)

    if made_new_high:
        notes.append("价格创阶段新高，上涨结构延续")
    if made_new_low:
        notes.append("价格创阶段新低，下跌结构延续")
        right_side = False

    if trend == TrendState.UP:
        notes.append("当前归类为上涨")
    elif trend == TrendState.RANGE:
        notes.append("当前归类为震荡")
        if return_pct > 10:
            notes.append("已有浮盈但趋势未确认，警惕利润回吐")
    else:
        notes.append("当前归类为下跌")
        right_side = False

    return {"trend": trend, "right_side": right_side, "notes": notes}


def trend_from_position(position: Position) -> dict:
    return evaluate_trend(trend=position.trend, return_pct=position.return_pct)
