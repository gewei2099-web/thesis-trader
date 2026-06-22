"""FastAPI server for mobile-friendly web UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config.rules import RulesConfig, get_rules, load_rules, save_rules
from src.discipline.layer import acknowledge_entry, build_alerts, log_alerts
from src.engine.decision import evaluate_all
from src.models.enums import (
    ACTION_LABELS,
    ActionType,
    FundamentalState,
    MarketSentiment,
    StockType,
    ThesisStatus,
    ThesisType,
    TrendState,
    WatchStatus,
)
from src.models.positions import Positions
from src.models.thesis import ThesisCard
from src.models.watchlist import Watchlist
from src.review.daily import run_daily_review
from src.storage import DataStore

ROOT = Path(__file__).resolve().parents[1]
store = DataStore(ROOT)

app = FastAPI(title="thesis-trader", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = ROOT / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/watchlist")
def get_watchlist() -> dict:
    return store.load_watchlist().model_dump(mode="json")


@app.post("/api/watchlist")
def save_watchlist(payload: Watchlist) -> dict:
    store.save_watchlist(payload)
    return {"ok": True}


@app.get("/api/positions")
def get_positions() -> dict:
    data = store.load_positions().model_dump(mode="json")
    return data


@app.post("/api/positions")
def save_positions(payload: Positions) -> dict:
    store.save_positions(payload)
    return {"ok": True}


@app.get("/api/thesis")
def list_thesis() -> dict:
    cards = store.load_all_thesis()
    return {"items": [c.model_dump(mode="json") for c in cards]}


@app.get("/api/thesis/{symbol}")
def get_thesis(symbol: str) -> dict:
    card = store.load_thesis(symbol)
    if not card:
        raise HTTPException(status_code=404, detail="thesis not found")
    return card.model_dump(mode="json")


@app.post("/api/thesis")
def upsert_thesis(payload: ThesisCard) -> dict:
    store.save_thesis(payload)
    return {"ok": True}


@app.delete("/api/thesis/{symbol}")
def remove_thesis(symbol: str) -> dict:
    ok = store.delete_thesis(symbol)
    if not ok:
        raise HTTPException(status_code=404, detail="thesis not found")
    return {"ok": True}


@app.get("/api/decisions")
def get_decisions() -> dict:
    positions = store.load_positions().items
    thesis_map = {t.symbol: t for t in store.load_all_thesis()}
    decisions = evaluate_all(positions, thesis_map)
    alerts = build_alerts(decisions, thesis_map)
    return {
        "decisions": [d.model_dump(mode="json") for d in decisions],
        "alerts": [a.model_dump(mode="json") for a in alerts],
    }


class ReviewRequest(BaseModel):
    market_info: str = ""


@app.post("/api/review")
def create_review(payload: ReviewRequest) -> dict:
    review, markdown = run_daily_review(store, payload.market_info)
    log = store.load_discipline_log()
    thesis_map = {t.symbol: t for t in store.load_all_thesis()}
    alerts = build_alerts(review.decisions, thesis_map)
    log_alerts(log, alerts)
    store.save_discipline_log(log)

    from src.notify.feishu import notify_discipline_if_needed

    notify_discipline_if_needed(alerts, review_date=str(review.review_date))

    return {
        "review": review.model_dump(mode="json"),
        "markdown": markdown,
    }


@app.get("/api/discipline")
def get_discipline_log() -> dict:
    return store.load_discipline_log().model_dump(mode="json")


class AckRequest(BaseModel):
    entry_id: str
    acknowledged: bool = True
    defer_reason: str = ""


@app.post("/api/discipline/ack")
def ack_discipline(payload: AckRequest) -> dict:
    log = store.load_discipline_log()
    acknowledge_entry(
        log,
        payload.entry_id,
        acknowledged=payload.acknowledged,
        defer_reason=payload.defer_reason,
    )
    store.save_discipline_log(log)
    return {"ok": True}


@app.get("/api/rules")
def get_rules_config() -> dict:
    return load_rules(ROOT).model_dump(mode="json")


@app.post("/api/rules")
def update_rules_config(payload: RulesConfig) -> dict:
    save_rules(payload, ROOT)
    get_rules.cache_clear()
    return {"ok": True}


@app.get("/api/meta/enums")
def get_enums() -> dict[str, Any]:
    return {
        "stock_types": [{"value": e.value, "label": e.value} for e in StockType],
        "thesis_types": [{"value": e.value, "label": e.value} for e in ThesisType],
        "trends": [{"value": e.value, "label": e.value} for e in TrendState],
        "fundamentals": [{"value": e.value, "label": e.value} for e in FundamentalState],
        "sentiments": [{"value": e.value, "label": e.value} for e in MarketSentiment],
        "thesis_statuses": [{"value": e.value, "label": e.value} for e in ThesisStatus],
        "actions": [{"value": e.value, "label": ACTION_LABELS[e]} for e in ActionType],
        "watch_statuses": [{"value": e.value, "label": e.value} for e in WatchStatus],
    }
