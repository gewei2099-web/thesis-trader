from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from .enums import ThesisStatus, ThesisType


class KeyMetric(BaseModel):
    name: str
    target: str = ""
    current: str = ""
    status: str = Field(default="watch", description="watch | ok | fail")


class ThesisCard(BaseModel):
    symbol: str
    name: str = ""
    core_thesis: str = Field(..., min_length=1, description="核心买入逻辑")
    thesis_type: ThesisType
    key_metrics: list[KeyMetric] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    expected_outcome: str = ""
    last_reviewed: Optional[date] = None
    thesis_status: ThesisStatus = ThesisStatus.VALID
    notes: str = ""
