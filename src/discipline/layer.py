"""Discipline layer — hard rules, no soft language."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from src.models.discipline import DisciplineAlert, DisciplineLog, DisciplineLogEntry
from src.models.decision import DecisionResult
from src.models.enums import ACTION_LABELS, ActionType
from src.models.thesis import ThesisCard


def build_alerts(
    decisions: list[DecisionResult],
    thesis_map: dict[str, ThesisCard],
) -> list[DisciplineAlert]:
    alerts: list[DisciplineAlert] = []

    for decision in decisions:
        if decision.action == ActionType.HOLD:
            continue

        action_label = ACTION_LABELS[decision.action]
        severity = "critical" if decision.action == ActionType.EXIT else "high"

        if any("逻辑失效" in t for t in decision.triggers):
            rule_name = "logic_invalidation"
            message = (
                f"{decision.name or decision.symbol}：买入逻辑已失效。"
                f"你必须执行{action_label}"
                + (f" {decision.reduce_pct}%" if decision.reduce_pct else "")
                + "，不允许以'再观察'为由拖延。"
            )
            risk = "逻辑失效后继续持有可能导致深度回撤，且违背你的交易体系。"
        elif any("止损" in t for t in decision.triggers):
            rule_name = "stop_loss"
            message = (
                f"{decision.name or decision.symbol}：已触发止损纪律。"
                f"必须{action_label} {decision.reduce_pct}%，禁止加仓摊平。"
            )
            risk = "不止损会把小亏拖成大亏，破坏账户曲线。"
        elif any("强制止盈" in t for t in decision.triggers):
            rule_name = "forced_take_profit"
            message = (
                f"{decision.name or decision.symbol}：浮盈过高，必须锁定利润。"
                f"执行{action_label} {decision.reduce_pct}%，禁止幻想继续翻倍。"
            )
            risk = "利润回吐是大多数交易者亏损的主因之一。"
        else:
            rule_name = "reduce_signal"
            message = (
                f"{decision.name or decision.symbol}：系统触发{action_label}信号。"
                f"执行比例 {decision.reduce_pct}%。"
                f"原因：{'；'.join(decision.triggers)}"
            )
            risk = "忽视系统化减仓信号，等同于用情绪替代规则。"

        alerts.append(
            DisciplineAlert(
                symbol=decision.symbol,
                name=decision.name,
                severity=severity,
                rule_name=rule_name,
                message=message,
                required_action=decision.action,
                reduce_pct=decision.reduce_pct,
                risk_if_ignored=risk,
            )
        )

    return alerts


def log_alerts(log: DisciplineLog, alerts: list[DisciplineAlert]) -> DisciplineLog:
    for alert in alerts:
        log.entries.append(
            DisciplineLogEntry(
                id=str(uuid4())[:8],
                created_at=datetime.now(),
                symbol=alert.symbol,
                rule_name=alert.rule_name,
                alert_message=alert.message,
                required_action=alert.required_action,
                reduce_pct=alert.reduce_pct,
            )
        )
    return log


def acknowledge_entry(
    log: DisciplineLog,
    entry_id: str,
    *,
    acknowledged: bool = True,
    defer_reason: str = "",
) -> DisciplineLog:
    for entry in log.entries:
        if entry.id == entry_id:
            entry.acknowledged = acknowledged
            entry.defer_reason = defer_reason
            break
    return log
