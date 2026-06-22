from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from .enums import StockType, WatchStatus


class WatchItem(BaseModel):
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    stock_type: StockType = Field(..., description="分类")
    status: WatchStatus = Field(default=WatchStatus.WATCHING)
    added_reason: str = Field(default="", description="加入原因")
    added_at: date = Field(default_factory=date.today)
    notes: str = Field(default="")


class Watchlist(BaseModel):
    items: list[WatchItem] = Field(default_factory=list)
