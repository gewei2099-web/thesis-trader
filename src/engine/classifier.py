"""Stock classification standards and guidance."""

from __future__ import annotations

from src.models.enums import StockType, ThesisType

CLASSIFICATION_RULES: dict[StockType, dict] = {
    StockType.CYCLE: {
        "label": "周期股",
        "criteria": [
            "盈利与产品价格/产能利用率高度相关",
            "行业存在明显供需周期",
            "估值常用 PB/PE 分位而非持续成长",
        ],
        "focus": ["产品价格", "库存", "产能利用率", "资本开支周期"],
        "take_profit_logic": "逻辑兑现（价格/盈利拐点确认）+ 趋势转弱分批减仓",
        "risk_points": ["周期误判、抄底过早、顶部贪婪"],
    },
    StockType.GROWTH: {
        "label": "成长股",
        "criteria": [
            "收入/利润有可持续增长预期",
            "核心竞争力或行业渗透率提升是核心",
            "估值容忍度更高，但需跟踪增速",
        ],
        "focus": ["收入增速", "毛利率", "市场份额", "研发/产品迭代"],
        "take_profit_logic": "成长逻辑弱化或估值透支时分批减仓，不因短期波动轻易清仓",
        "risk_points": ["增速不及预期", "竞争格局恶化", "估值泡沫"],
    },
    StockType.EVENT: {
        "label": "事件驱动",
        "criteria": [
            "核心收益来自单一或少数可识别事件",
            "事件有时间窗口和兑现节点",
            "事件落空则逻辑立即失效",
        ],
        "focus": ["事件进度", "政策/审批节点", "兑现时间表"],
        "take_profit_logic": "事件兑现即止盈，落空即止损，不恋战",
        "risk_points": ["事件延期", "预期落空", "利好出尽"],
    },
}


def classify_guidance(stock_type: StockType | ThesisType) -> dict:
    key = StockType(stock_type.value)
    return CLASSIFICATION_RULES[key]
