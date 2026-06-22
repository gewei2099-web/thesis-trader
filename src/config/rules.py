"""Load and validate trading rules from data/config/rules.json."""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

DEFAULT_RULES: dict[str, Any] = {
    "profit_take": {
        "cycle": [15, 35],
        "growth": [25, 50],
        "event": [10, 25],
        "default": [15, 30],
    },
    "stop_loss_pct": -8,
    "reduce_pct": {
        "weakening": 30,
        "failed_metrics": 40,
        "trend_down": 40,
        "range": 20,
        "force_take_profit": 30,
        "sentiment_high": 20,
        "stop_loss": 50,
        "fundamental_weakened_growth": 30,
        "fundamental_weakened_other": 20,
    },
    "sentiment_high_min_return_pct": 10,
    "rule_priority": [
        "logic_fail",
        "stop_loss",
        "logic_weakening",
        "failed_metrics",
        "fundamental_weakened",
        "trend_down",
        "force_take_profit",
        "range_take_profit",
        "sentiment_high",
    ],
}


class RulesConfig(BaseModel):
    profit_take: dict[str, list[int]] = Field(default_factory=lambda: deepcopy(DEFAULT_RULES["profit_take"]))
    stop_loss_pct: float = -8
    reduce_pct: dict[str, int] = Field(default_factory=lambda: deepcopy(DEFAULT_RULES["reduce_pct"]))
    sentiment_high_min_return_pct: float = 10
    rule_priority: list[str] = Field(default_factory=lambda: list(DEFAULT_RULES["rule_priority"]))


def rules_path(root: Path | None = None) -> Path:
    base = root or Path(__file__).resolve().parents[2]
    return base / "data" / "config" / "rules.json"


def load_rules(root: Path | None = None) -> RulesConfig:
    path = rules_path(root)
    if not path.exists():
        return RulesConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = {**DEFAULT_RULES, **data}
    if "profit_take" in data:
        merged["profit_take"] = {**DEFAULT_RULES["profit_take"], **data["profit_take"]}
    if "reduce_pct" in data:
        merged["reduce_pct"] = {**DEFAULT_RULES["reduce_pct"], **data["reduce_pct"]}
    return RulesConfig.model_validate(merged)


def save_rules(rules: RulesConfig | dict[str, Any], root: Path | None = None) -> None:
    path = rules_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = rules.model_dump() if isinstance(rules, RulesConfig) else rules
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    get_rules.cache_clear()


@lru_cache(maxsize=1)
def get_rules() -> RulesConfig:
    return load_rules()


def profit_thresholds(thesis_type: str | None, rules: RulesConfig | None = None) -> tuple[int, int]:
    rules = rules or get_rules()
    key = thesis_type or "default"
    pair = rules.profit_take.get(key) or rules.profit_take.get("default") or [15, 30]
    return int(pair[0]), int(pair[1])
