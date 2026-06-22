"""Build static GitHub Pages site (public summary + reports only)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.public_summary import build_public_summary  # noqa: E402
from src.storage import DataStore  # noqa: E402

DOCS = ROOT / "docs"
PAGES_SRC = ROOT / "pages"
REPO_ISSUES_URL = "https://github.com/gewei2099-web/thesis-trader/issues/new?template=flash_note"


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

    public_dir = DOCS / "public"
    public_dir.mkdir(parents=True)

    summary = build_public_summary(store)
    summary["flash_note_url"] = REPO_ISSUES_URL
    (public_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    reports_src = store.reviews_dir
    reports_dst = DOCS / "reports"
    reports_dst.mkdir(parents=True)
    review_files = sorted(reports_src.glob("*.md"), reverse=True) if reports_src.exists() else []
    for review in review_files:
        shutil.copy2(review, reports_dst / review.name)

    reviews_index = [{"date": p.stem, "path": f"reports/{p.name}"} for p in review_files]
    (public_dir / "reviews_index.json").write_text(
        json.dumps(reviews_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Built public GitHub Pages site at {DOCS}")
    print(f"  public summary only (no raw data/)")
    print(f"  reviews: {len(reviews_index)}")
    return DOCS


if __name__ == "__main__":
    build()
