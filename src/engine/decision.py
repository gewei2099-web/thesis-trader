"""Take-profit / reduce decision engine (rule-based)."""

from __future__ import annotations

from src.models.decision import DecisionResult
from src.models.enums import (
    ActionType,
    FundamentalState,
    MarketSentiment,
    ThesisStatus,
    ThesisType,
    TrendState,
)
from src.models.positions import Position
from src.models.thesis import ThesisCard
from src.engine.classifier import classify_guidance


def _profit_thresholds(thesis_type: ThesisType | None) -> tuple[int, int]:
    if thesis_type == ThesisType.CYCLE:
        return 15, 35
    if thesis_type == ThesisType.GROWTH:
        return 25, 50
    if thesis_type == ThesisType.EVENT:
        return 10, 25
    return 15, 30


def evaluate_position(position: Position, thesis: ThesisCard | None = None) -> DecisionResult:
    triggers: list[str] = []
    action = ActionType.HOLD
    reduce_pct = 0
    priority = 0
    thesis_type = thesis.thesis_type if thesis else None
    trend_tp, force_tp = _profit_thresholds(thesis_type)
    name = position.name or (thesis.name if thesis else "")

    if thesis and thesis.thesis_status == ThesisStatus.INVALID:
        triggers.append("逻辑失效：买入假设不再成立")
        action = ActionType.EXIT
        reduce_pct = 100
        priority = 100
    elif thesis and thesis.thesis_status == ThesisStatus.WEAKENING:
        triggers.append("逻辑弱化：关键验证指标出现不利变化")
        action = ActionType.REDUCE
        reduce_pct = max(reduce_pct, 30)
        priority = max(priority, 80)

    failed_metrics = [m for m in (thesis.key_metrics if thesis else []) if m.status == "fail"]
    if failed_metrics:
        metric_names = "、".join(m.name for m in failed_metrics)
        triggers.append(f"关键指标未达标：{metric_names}")
        action = ActionType.REDUCE if action == ActionType.HOLD else action
        reduce_pct = max(reduce_pct, 40)
        priority = max(priority, 85)

    if position.fundamental_state == FundamentalState.WEAKENED:
        triggers.append("基本面弱化")
        if thesis_type == ThesisType.GROWTH:
            action = ActionType.REDUCE
            reduce_pct = max(reduce_pct, 30)
            priority = max(priority, 70)
        else:
            action = ActionType.REDUCE if action == ActionType.HOLD else action
            reduce_pct = max(reduce_pct, 20)
            priority = max(priority, 60)

    if position.return_pct >= trend_tp and position.trend == TrendState.DOWN:
        triggers.append(f"趋势止盈：浮盈 {position.return_pct}% 且趋势转跌")
        action = ActionType.REDUCE
        reduce_pct = max(reduce_pct, 40)
        priority = max(priority, 65)

    if position.return_pct >= trend_tp and position.trend == TrendState.RANGE:
        triggers.append(f"震荡止盈：浮盈 {position.return_pct}% 但趋势未确认")
        action = ActionType.REDUCE if action == ActionType.HOLD else action
        reduce_pct = max(reduce_pct, 20)
        priority = max(priority, 50)

    if position.return_pct >= force_tp:
        triggers.append(f"强制止盈：浮盈已达 {position.return_pct}%，必须锁定部分利润")
        action = ActionType.REDUCE if action != ActionType.EXIT else action
        reduce_pct = max(reduce_pct, 30)
        priority = max(priority, 75)

    if position.market_sentiment == MarketSentiment.HIGH and position.return_pct > 10:
        triggers.append("市场情绪过热，且已有浮盈")
        action = ActionType.REDUCE if action == ActionType.HOLD else action
        reduce_pct = max(reduce_pct, 20)
        priority = max(priority, 55)

    if position.return_pct <= -8:
        triggers.append(f"止损纪律：亏损已达 {position.return_pct}%")
        if thesis and thesis.thesis_status == ThesisStatus.INVALID:
            action = ActionType.EXIT
            reduce_pct = 100
        else:
            action = ActionType.REDUCE
            reduce_pct = max(reduce_pct, 50)
        priority = max(priority, 90)

    if not triggers:
        triggers.append("未触发减仓/清仓规则，继续持有并跟踪逻辑")

    guidance = classify_guidance(thesis_type) if thesis_type else {}
    type_label = guidance.get("label", "未分类")
    rationale = f"【{type_label}】" + "；".join(triggers)
    if guidance:
        rationale += f"。该类止盈逻辑：{guidance.get('take_profit_logic', '')}"

    return DecisionResult(
        symbol=position.symbol,
        name=name,
        action=action,
        reduce_pct=reduce_pct if action != ActionType.HOLD else 0,
        triggers=triggers,
        rationale=rationale,
        priority=priority,
    )


def evaluate_all(
    positions: list[Position],
    thesis_map: dict[str, ThesisCard],
) -> list[DecisionResult]:
    results = [evaluate_position(pos, thesis_map.get(pos.symbol)) for pos in positions]
    return sorted(results, key=lambda r: r.priority, reverse=True)
