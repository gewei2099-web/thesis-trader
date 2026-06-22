"""Local-only sensitive position fields (gitignored)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.positions import Position, Positions

PLACEHOLDER_SHARES = 100


def private_path(data_dir: Path) -> Path:
    return data_dir / "local" / "private.json"


def _read_private(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"positions": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_private(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_likely_masked(pos: Position) -> bool:
    return pos.shares == PLACEHOLDER_SHARES and abs(pos.avg_cost - pos.current_price) < 0.01


def _mask_position(pos: Position) -> Position:
    return pos.model_copy(
        update={
            "shares": PLACEHOLDER_SHARES,
            "avg_cost": pos.current_price,
        }
    )


def _overlay_position(pos: Position, private_entry: dict[str, Any] | None) -> Position:
    if not private_entry:
        return pos
    updates: dict[str, Any] = {}
    for key in ("shares", "avg_cost", "name", "notes"):
        if key in private_entry and private_entry[key] is not None:
            updates[key] = private_entry[key]
    return pos.model_copy(update=updates) if updates else pos


def load_positions_merged(data_dir: Path) -> Positions:
    path = data_dir / "positions.json"
    if not path.exists():
        return Positions()

    positions = Positions.model_validate(json.loads(path.read_text(encoding="utf-8")))
    priv_file = private_path(data_dir)
    priv = _read_private(priv_file)
    priv_positions: dict[str, Any] = priv.get("positions", {})

    if not priv_positions and positions.items:
        if any(not _is_likely_masked(p) for p in positions.items):
            _migrate_to_private(data_dir, positions)
            priv = _read_private(priv_file)
            priv_positions = priv.get("positions", {})

    merged = [_overlay_position(p, priv_positions.get(p.symbol)) for p in positions.items]
    return Positions(items=merged)


def save_positions_split(data_dir: Path, positions: Positions) -> None:
    priv_file = private_path(data_dir)
    priv = _read_private(priv_file)
    priv_positions = priv.setdefault("positions", {})

    for pos in positions.items:
        priv_positions[pos.symbol] = {
            "shares": pos.shares,
            "avg_cost": pos.avg_cost,
            "name": pos.name,
            "notes": pos.notes,
        }

    _write_private(priv_file, priv)

    masked = Positions(items=[_mask_position(p) for p in positions.items])
    out = data_dir / "positions.json"
    out.write_text(
        json.dumps(masked.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _migrate_to_private(data_dir: Path, positions: Positions) -> None:
    save_positions_split(data_dir, positions)
