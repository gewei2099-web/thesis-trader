from datetime import date

from pydantic import BaseModel, Field

from .decision import DecisionResult
from .enums import ActionType


class StockReviewItem(BaseModel):
    symbol: str
    name: str = ""
    important_info: list[str] = Field(default_factory=list)
    thesis_impact: str = ""
    thesis_changed: bool = False
    suggested_action: ActionType = ActionType.HOLD
    reduce_pct: int = 0
    reason: str = ""


class DailyReview(BaseModel):
    review_date: date
    market_summary: str = ""
    important_events: list[str] = Field(default_factory=list)
    stock_items: list[StockReviewItem] = Field(default_factory=list)
    decisions: list[DecisionResult] = Field(default_factory=list)
    discipline_alerts: list[str] = Field(default_factory=list)
    closing_note: str = ""
