from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, computed_field

from .enums import FundamentalState, MarketSentiment, TrendState


class Position(BaseModel):
    symbol: str
    name: str = ""
    shares: float = Field(..., gt=0)
    avg_cost: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    trend: TrendState = TrendState.RANGE
    fundamental_state: FundamentalState = FundamentalState.UNCHANGED
    market_sentiment: MarketSentiment = MarketSentiment.MEDIUM
    opened_at: date = Field(default_factory=date.today)
    notes: str = ""

    @computed_field
    @property
    def return_pct(self) -> float:
        return round((self.current_price - self.avg_cost) / self.avg_cost * 100, 2)

    @computed_field
    @property
    def market_value(self) -> float:
        return round(self.shares * self.current_price, 2)


class Positions(BaseModel):
    items: list[Position] = Field(default_factory=list)
