"""JSON file storage helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from src.models.discipline import DisciplineLog
from src.models.positions import Positions
from src.models.thesis import ThesisCard
from src.models.watchlist import Watchlist
from src.private_overlay import load_positions_merged, save_positions_split

T = TypeVar("T", bound=BaseModel)


class DataStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[1]
        self.data_dir = self.root / "data"
        self.thesis_dir = self.data_dir / "thesis"
        self.reviews_dir = self.data_dir / "reviews"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.thesis_dir.mkdir(parents=True, exist_ok=True)
        self.reviews_dir.mkdir(parents=True, exist_ok=True)

    def _read(self, path: Path, model: type[T]) -> T:
        if not path.exists():
            return model.model_validate({})
        data = json.loads(path.read_text(encoding="utf-8"))
        return model.model_validate(data)

    def _write(self, path: Path, model: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_watchlist(self) -> Watchlist:
        return self._read(self.data_dir / "watchlist.json", Watchlist)

    def save_watchlist(self, watchlist: Watchlist) -> None:
        self._write(self.data_dir / "watchlist.json", watchlist)

    def load_positions(self) -> Positions:
        return load_positions_merged(self.data_dir)

    def save_positions(self, positions: Positions) -> None:
        save_positions_split(self.data_dir, positions)

    def load_discipline_log(self) -> DisciplineLog:
        return self._read(self.data_dir / "discipline_log.json", DisciplineLog)

    def save_discipline_log(self, log: DisciplineLog) -> None:
        self._write(self.data_dir / "discipline_log.json", log)

    def list_thesis_symbols(self) -> list[str]:
        return sorted(p.stem for p in self.thesis_dir.glob("*.json"))

    def load_thesis(self, symbol: str) -> ThesisCard | None:
        path = self.thesis_dir / f"{symbol}.json"
        if not path.exists():
            return None
        return ThesisCard.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save_thesis(self, thesis: ThesisCard) -> None:
        self._write(self.thesis_dir / f"{thesis.symbol}.json", thesis)

    def delete_thesis(self, symbol: str) -> bool:
        path = self.thesis_dir / f"{symbol}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def load_all_thesis(self) -> list[ThesisCard]:
        cards: list[ThesisCard] = []
        for symbol in self.list_thesis_symbols():
            card = self.load_thesis(symbol)
            if card:
                cards.append(card)
        return cards

    def save_review_markdown(self, review_date: str, content: str) -> Path:
        path = self.reviews_dir / f"{review_date}.md"
        path.write_text(content, encoding="utf-8")
        return path
