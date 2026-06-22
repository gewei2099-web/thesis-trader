from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .enums import ActionType


class DisciplineAlert(BaseModel):
    symbol: str
    name: str = ""
    severity: str = Field(default="high", description="high | critical")
    rule_name: str
    message: str
    required_action: ActionType
    reduce_pct: int = 0
    risk_if_ignored: str


class DisciplineLogEntry(BaseModel):
    id: str
    created_at: datetime
    symbol: str
    rule_name: str
    alert_message: str
    required_action: ActionType
    reduce_pct: int = 0
    acknowledged: bool = False
    defer_reason: str = ""


class DisciplineLog(BaseModel):
    entries: list[DisciplineLogEntry] = Field(default_factory=list)
