from enum import Enum


class StockType(str, Enum):
    CYCLE = "cycle"
    GROWTH = "growth"
    EVENT = "event"


class ThesisType(str, Enum):
    CYCLE = "cycle"
    GROWTH = "growth"
    EVENT = "event"


class WatchStatus(str, Enum):
    WATCHING = "watching"
    READY = "ready"
    REMOVED = "removed"


class TrendState(str, Enum):
    UP = "up"
    RANGE = "range"
    DOWN = "down"


class FundamentalState(str, Enum):
    STRENGTHENED = "strengthened"
    UNCHANGED = "unchanged"
    WEAKENED = "weakened"


class MarketSentiment(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThesisStatus(str, Enum):
    VALID = "valid"
    WEAKENING = "weakening"
    INVALID = "invalid"


class ActionType(str, Enum):
    HOLD = "hold"
    ADD = "add"
    REDUCE = "reduce"
    EXIT = "exit"


STOCK_TYPE_LABELS = {
    StockType.CYCLE: "周期股",
    StockType.GROWTH: "成长股",
    StockType.EVENT: "事件驱动",
}

TREND_LABELS = {
    TrendState.UP: "上涨",
    TrendState.RANGE: "震荡",
    TrendState.DOWN: "下跌",
}

ACTION_LABELS = {
    ActionType.HOLD: "持有",
    ActionType.ADD: "加仓",
    ActionType.REDUCE: "减仓",
    ActionType.EXIT: "清仓",
}
