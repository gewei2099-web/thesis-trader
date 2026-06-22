"""Send discipline alerts to Feishu group bot webhook."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from src.models.discipline import DisciplineAlert


def send_feishu_text(webhook_url: str, text: str) -> bool:
    payload = json.dumps({"msg_type": "text", "content": {"text": text}}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("StatusCode") == 0 or body.get("code") == 0
    except urllib.error.URLError as exc:
        print(f"Feishu notify failed: {exc}")
        return False


def format_discipline_message(alerts: list[DisciplineAlert], review_date: str) -> str:
    lines = [f"【thesis-trader 纪律提醒】{review_date}", ""]
    for alert in alerts:
        lines.append(alert.message)
        lines.append(f"风险：{alert.risk_if_ignored}")
        lines.append("")
    lines.append("请打开本地系统确认执行，勿忽视规则。")
    return "\n".join(lines).strip()


def notify_discipline_if_needed(
    alerts: list[DisciplineAlert],
    *,
    review_date: str,
    webhook_url: str | None = None,
) -> bool:
    if not alerts:
        print("No discipline alerts, skip Feishu notify.")
        return False

    url = webhook_url or os.environ.get("FEISHU_WEBHOOK_URL", "").strip()
    if not url:
        print("FEISHU_WEBHOOK_URL not set, skip notify.")
        return False

    text = format_discipline_message(alerts, review_date)
    ok = send_feishu_text(url, text)
    print("Feishu notify sent." if ok else "Feishu notify failed.")
    return ok
