"""Daily review generator (rule-based, no LLM)."""

from __future__ import annotations

from datetime import date

from src.discipline.layer import build_alerts
from src.engine.decision import evaluate_all
from src.engine.trend import trend_from_position
from src.models.enums import ACTION_LABELS, ActionType
from src.models.positions import Position
from src.models.review import DailyReview, StockReviewItem
from src.models.thesis import ThesisCard
from src.storage import DataStore


def extract_important_lines(market_info: str, max_lines: int = 8) -> list[str]:
    lines = [ln.strip() for ln in market_info.splitlines() if ln.strip()]
    if not lines:
        return []
    keywords = ("跌", "涨", "业绩", "公告", "政策", "锂", "芯片", "收入", "利润", "减持", "收购", "停产", "涨价", "降价")
    scored: list[tuple[int, str]] = []
    for line in lines:
        score = sum(1 for kw in keywords if kw in line)
        if score:
            scored.append((score, line))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [line for _, line in scored[:max_lines]]
    return picked or lines[:max_lines]


def _info_affects_symbol(line: str, symbol: str, name: str) -> bool:
    tokens = {symbol, name, name[:2] if len(name) >= 2 else name}
    return any(t and t in line for t in tokens)


def analyze_stock(
    position: Position,
    thesis: ThesisCard | None,
    important_events: list[str],
) -> StockReviewItem:
    related = [
        ev for ev in important_events
        if _info_affects_symbol(ev, position.symbol, position.name or (thesis.name if thesis else ""))
    ]
    decision = evaluate_all([position], {position.symbol: thesis} if thesis else {})[0]
    trend_info = trend_from_position(position)

    thesis_impact = "今日信息未直接冲击持仓逻辑，继续跟踪关键指标。"
    thesis_changed = False
    if related:
        thesis_impact = f"出现 {len(related)} 条相关信息，需核对是否触及失效条件。"
        if thesis and any(kw in " ".join(related) for kw in ("不及预期", "下调", "亏损", "延期", "落空", "跌破")):
            thesis_changed = True
            thesis_impact = "信息偏负面，持仓逻辑可能弱化或失效，必须逐条对照失效条件。"

    if thesis and thesis.thesis_status.value in ("weakening", "invalid"):
        thesis_changed = True
        thesis_impact = f"逻辑卡片状态为 {thesis.thesis_status.value}，这不是观察期，是行动期。"

    reason_parts = list(decision.triggers)
    if trend_info["notes"]:
        reason_parts.append(trend_info["notes"][0])

    return StockReviewItem(
        symbol=position.symbol,
        name=position.name or (thesis.name if thesis else ""),
        important_info=related,
        thesis_impact=thesis_impact,
        thesis_changed=thesis_changed,
        suggested_action=decision.action,
        reduce_pct=decision.reduce_pct,
        reason="；".join(reason_parts),
    )


def generate_daily_review(
    store: DataStore,
    *,
    market_info: str = "",
    review_date: date | None = None,
) -> DailyReview:
    review_date = review_date or date.today()
    positions = store.load_positions().items
    thesis_list = store.load_all_thesis()
    thesis_map = {t.symbol: t for t in thesis_list}

    important_events = extract_important_lines(market_info)
    stock_items = [
        analyze_stock(pos, thesis_map.get(pos.symbol), important_events)
        for pos in positions
    ]
    decisions = evaluate_all(positions, thesis_map)
    alerts = build_alerts(decisions, thesis_map)

    action_items = [s for s in stock_items if s.suggested_action != ActionType.HOLD]
    if action_items:
        closing = "今日有明确交易动作信号，先执行纪律，再考虑新机会。"
    elif important_events:
        closing = "有市场信息需消化，但未触发强制动作；更新逻辑卡片后继续持有。"
    else:
        closing = "无重大变化，保持耐心，不要因无聊而交易。"

    return DailyReview(
        review_date=review_date,
        market_summary=market_info.strip()[:500],
        important_events=important_events,
        stock_items=stock_items,
        decisions=decisions,
        discipline_alerts=[a.message for a in alerts],
        closing_note=closing,
    )


def render_review_markdown(review: DailyReview) -> str:
    lines = [
        f"# 每日复盘 {review.review_date}",
        "",
        "## 重要信息",
    ]
    if review.important_events:
        lines.extend(f"- {ev}" for ev in review.important_events)
    else:
        lines.append("- （未提供或未识别到重要信息）")

    lines.extend(["", "## 持仓逐条分析", ""])
    for item in review.stock_items:
        action = ACTION_LABELS[item.suggested_action]
        lines.append(f"### {item.name or item.symbol} ({item.symbol})")
        lines.append(f"- 逻辑影响：{item.thesis_impact}")
        lines.append(f"- 逻辑是否变化：{'是' if item.thesis_changed else '否'}")
        lines.append(f"- 建议动作：**{action}**" + (f" {item.reduce_pct}%" if item.reduce_pct else ""))
        lines.append(f"- 原因：{item.reason}")
        if item.important_info:
            lines.append("- 相关信息：")
            lines.extend(f"  - {x}" for x in item.important_info)
        lines.append("")

    lines.extend(["## 决策引擎汇总", ""])
    for d in review.decisions:
        action = ACTION_LABELS[d.action]
        lines.append(
            f"- **{d.name or d.symbol}**：{action}"
            + (f" {d.reduce_pct}%" if d.reduce_pct else "")
            + f" — {d.rationale}"
        )

    if review.discipline_alerts:
        lines.extend(["", "## 纪律提醒（必须处理）", ""])
        for msg in review.discipline_alerts:
            lines.append(f"- ⚠️ {msg}")

    lines.extend(["", "## 结语", "", review.closing_note, ""])
    return "\n".join(lines)


def run_daily_review(store: DataStore, market_info: str) -> tuple[DailyReview, str]:
    review = generate_daily_review(store, market_info=market_info)
    markdown = render_review_markdown(review)
    store.save_review_markdown(review.review_date.isoformat(), markdown)
    return review, markdown
