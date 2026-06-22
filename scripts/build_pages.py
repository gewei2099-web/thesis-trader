"""Build static GitHub Pages site from data/ and pages/."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.discipline.layer import build_alerts  # noqa: E402
from src.engine.decision import evaluate_all  # noqa: E402
from src.storage import DataStore  # noqa: E402

DOCS = ROOT / "docs"
PAGES_SRC = ROOT / "pages"


def build() -> Path:
    store = DataStore(ROOT)

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)

    for name in ("index.html", "app.js", "styles.css", "manifest.json"):
        src = PAGES_SRC / name
        if src.exists():
            shutil.copy2(src, DOCS / name)

    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    data_src = ROOT / "data"
    data_dst = DOCS / "data"
    if data_src.exists():
        shutil.copytree(data_src, data_dst)

    positions = store.load_positions().items
    thesis_map = {t.symbol: t for t in store.load_all_thesis()}
    decisions = evaluate_all(positions, thesis_map)
    alerts = build_alerts(decisions, thesis_map)

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decisions": [d.model_dump(mode="json") for d in decisions],
        "alerts": [a.model_dump(mode="json") for a in alerts],
    }
    (data_dst / "snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    reviews_dir = data_dst / "reviews"
    review_files = sorted(reviews_dir.glob("*.md"), reverse=True) if reviews_dir.exists() else []
    reviews_index = [{"date": p.stem, "path": f"data/reviews/{p.name}"} for p in review_files]
    (data_dst / "reviews_index.json").write_text(
        json.dumps(reviews_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    thesis_symbols = store.list_thesis_symbols()
    (data_dst / "thesis_index.json").write_text(
        json.dumps(thesis_symbols, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Built GitHub Pages site at {DOCS}")
    print(f"  reviews: {len(reviews_index)}")
    print(f"  decisions: {len(decisions)}")
    return DOCS


if __name__ == "__main__":
    build()
