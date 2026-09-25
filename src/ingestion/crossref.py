from __future__ import annotations

import html
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

from core.config import Settings
from core.utils import ensure_parent, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _date_to_iso(node: dict | None) -> str:
    try:
        if not node:
            return ""
        parts = (node.get("date-parts") or [[]])[0]
        if not parts:
            return ""
        y = int(parts[0]) if len(parts) > 0 else 1900
        m = int(parts[1]) if len(parts) > 1 else 1
        d = int(parts[2]) if len(parts) > 2 else 1
        return f"{y:04d}-{m:02d}-{d:02d}"
    except Exception:
        return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    items = (payload.get("message") or {}).get("items") or []
    records: list[PaperRecord] = []
    for it in items:
        doi = str(it.get("DOI") or "").strip()
        title = _clean_text((it.get("title") or [""])[0] if it.get("title") else "")
        summary = _clean_text(it.get("abstract") or "")
        if not doi or not title or not summary or len(summary) < 30:
            continue
        authors: list[str] = []
        for a in it.get("author") or []:
            name = " ".join(x for x in [a.get("given"), a.get("family")] if x).strip()
            name = _clean_text(name)
            if name:
                authors.append(name)
        subjects = [_clean_text(s) for s in (it.get("subject") or []) if s]
        publisher = _clean_text(it.get("publisher") or "")
        containers = [_clean_text(c) for c in (it.get("container-title") or []) if c]
        primary = subjects[0] if subjects else (containers[0] if containers else publisher)
        published = _date_to_iso(it.get("published")) or _date_to_iso(it.get("created"))
        updated = ""
        try:
            ts_ms = (it.get("indexed") or {}).get("timestamp")
            if ts_ms:
                from datetime import UTC, datetime

                updated = datetime.fromtimestamp(int(ts_ms) / 1000, tz=UTC).date().isoformat()
        except Exception:
            updated = ""
        abs_url = f"https://doi.org/{doi}"
        pdf_url = ""
        for lk in it.get("link") or []:
            url = lk.get("URL") or ""
            ctype = str(lk.get("content-type") or "").lower()
            if "pdf" in ctype or url.lower().endswith(".pdf"):
                pdf_url = url
                break
        comment = containers[0] if containers else publisher
        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=subjects,
                primary_category=primary,
                published=published,
                updated=updated,
                abs_url=abs_url or str(it.get("URL") or ""),
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API (co offline fallback), luu raw response, parse thanh records."""
    raw_resp = settings.paths.raw_api_response
    raw_recs = settings.paths.raw_records_json

    # Offline / cache mode: dung snapshot neu co va khong yeu cau refresh
    if raw_resp.exists() and not settings.refresh_source:
        try:
            payload = json.loads(raw_resp.read_text(encoding="utf-8"))
            records = parse_crossref_payload(payload)
            if records:
                write_json(raw_recs, [asdict(r) for r in records])
                return records
        except Exception:
            pass

    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": "DOI,title,abstract,author,subject,published,created,indexed,URL,link,publisher,container-title",
    }
    headers = {
        "User-Agent": "VinUni-Day10-Lab/0.1 (mailto:student@vinuni.edu.vn)",
        "Accept": "application/json",
    }
    last_exc: Exception | None = None
    payload: dict | None = None
    for attempt in range(5):
        try:
            resp = requests.get(
                "https://api.crossref.org/works", params=params, headers=headers, timeout=30
            )
            if resp.status_code == 200:
                payload = resp.json()
                break
            if resp.status_code in (429, 503):
                time.sleep(2 * (attempt + 1))
                continue
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - retry roi fallback snapshot
            last_exc = exc
            time.sleep(2 * (attempt + 1))

    if payload is None:
        # Fallback cuoi: doc snapshot cu neu co
        if raw_resp.exists():
            payload = json.loads(raw_resp.read_text(encoding="utf-8"))
        else:
            raise RuntimeError(f"Crossref fetch failed and no snapshot: {last_exc}")

    ensure_parent(raw_resp)
    raw_resp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    records = parse_crossref_payload(payload)
    write_json(raw_recs, [asdict(r) for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    data = read_json(path)
    if isinstance(data, dict):
        data = data.get("records", data.get("items", []))
    records: list[PaperRecord] = []
    for row in data:
        records.append(
            PaperRecord(
                paper_id=str(row.get("paper_id", "")),
                title=str(row.get("title", "")),
                summary=str(row.get("summary", "")),
                authors=list(row.get("authors", []) or []),
                categories=list(row.get("categories", []) or []),
                primary_category=str(row.get("primary_category", "")),
                published=str(row.get("published", "")),
                updated=str(row.get("updated", "")),
                abs_url=str(row.get("abs_url", "")),
                pdf_url=str(row.get("pdf_url", "")),
                comment=str(row.get("comment", "")),
            )
        )
    return records
