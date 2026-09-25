from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _parse_date(value: str) -> str:
    """Chuan hoa ve YYYY-MM-DD, tra '' neu khong parse duoc."""
    if not value:
        return ""
    text = normalize_whitespace(str(value))
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(text[: len(fmt)], fmt)
            if fmt == "%Y":
                return f"{dt.year:04d}-01-01"
            if fmt == "%Y-%m":
                return f"{dt.year:04d}-{dt.month:02d}-01"
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        return ""


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    rows: list[dict] = []
    run_d = run_date.date() if isinstance(run_date, datetime) else run_date
    for r in records:
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)
        authors = [normalize_whitespace(a) for a in (r.authors or []) if a and a.strip()]
        categories = [normalize_whitespace(c) for c in (r.categories or []) if c and c.strip()]
        published = _parse_date(r.published)
        updated = _parse_date(r.updated)
        if not r.paper_id or not title or not summary or len(summary) < 30:
            continue
        try:
            pub_d = datetime.strptime(published, "%Y-%m-%d").date() if published else None
            age_days = (run_d - pub_d).days if pub_d else None
        except Exception:
            age_days = None
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published}\n"
            f"Categories: {categories_joined or r.primary_category}\n"
            f"Summary: {summary}"
        )
        rows.append(
            {
                "paper_id": r.paper_id.strip(),
                "title": title,
                "summary": summary,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "primary_category": normalize_whitespace(r.primary_category),
                "published": published,
                "updated": updated,
                "age_days": age_days,
                "summary_chars": len(summary),
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": normalize_whitespace(r.comment),
                "text_for_embedding": text_for_embedding,
            }
        )
    df = pd.DataFrame(
        rows,
        columns=[
            "paper_id",
            "title",
            "summary",
            "authors_joined",
            "categories_joined",
            "primary_category",
            "published",
            "updated",
            "age_days",
            "summary_chars",
            "abs_url",
            "pdf_url",
            "comment",
            "text_for_embedding",
        ],
    )
    if df.empty:
        return df
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df[df["text_for_embedding"].str.len() > 0]
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df
