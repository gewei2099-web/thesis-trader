"""Build anonymized public summary for GitHub Pages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.discipline.layer import build_alerts
from src.engine.decision import evaluate_all
from src.models.discipline import DisciplineAlert
from src.storage import DataStore


def build_public_summary(store: DataStore) -> dict[str, Any]:
    positions = store.load_positions().items
    watchlist = store.load_watchlist().items
    thesis_list = store.load_all_thesis()
    thesis_map = {t.symbol: t for t in thesis_list}

    decisions = evaluate_all(positions, thesis_map)
    alerts = build_alerts(decisions, thesis_map)

    returns = [p.return_pct for p in positions]
    avg_return = round(sum(returns) / len(returns), 2) if returns else 0.0

    by_type: dict[str, int] = {}
    for pos in positions:
        thesis = thesis_map.get(pos.symbol)
        key = thesis.thesis_type.value if thesis else "unknown"
        by_type[key] = by_type.get(key, 0) + 1

    by_action = {"hold": 0, "reduce": 0, "exit": 0, "add": 0}
    for d in decisions:
        by_action[d.action.value] = by_action.get(d.action.value, 0) + 1

    public_decisions = []
    for idx, decision in enumerate(decisions, start=1):
        pos = next((p for p in positions if p.symbol == decision.symbol), None)
        thesis = thesis_map.get(decision.symbol)
        public_decisions.append(
            {
                "label": f"持仓{idx}",
                "stock_type": thesis.thesis_type.value if thesis else "unknown",
                "action": decision.action.value,
                "reduce_pct": decision.reduce_pct,
                "return_pct": pos.return_pct if pos else None,
                "trend": pos.trend.value if pos else None,
                "trigger_summary": decision.triggers[0] if decision.triggers else "",
                "priority": decision.priority,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "portfolio": {
            "position_count": len(positions),
            "watchlist_count": len(watchlist),
            "thesis_count": len(thesis_list),
            "avg_return_pct": avg_return,
            "by_stock_type": by_type,
            "by_action": by_action,
        },
        "decisions": public_decisions,
        "discipline": _public_discipline(alerts),
    }


def _public_discipline(alerts: list[DisciplineAlert]) -> dict[str, Any]:
    if not alerts:
        return {"alert_count": 0, "severity": "none", "summary": "当前无纪律提醒"}

    critical = sum(1 for a in alerts if a.severity == "critical")
    severity = "critical" if critical else "high"
    return {
        "alert_count": len(alerts),
        "severity": severity,
        "summary": f"有 {len(alerts)} 条纪律提醒待处理（{'含清仓级' if critical else '减仓级'}）",
        "rule_names": sorted({a.rule_name for a in alerts}),
    }
