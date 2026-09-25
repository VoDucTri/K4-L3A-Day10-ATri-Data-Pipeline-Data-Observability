from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import ensure_parent
from core.utils import write_json


def _manual_checks(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    n = len(df)
    checks["row_count"] = {
        "value": n,
        "pass": 5 <= n <= 5000,
        "expect": "5 <= n <= 5000",
    }
    for col in ("paper_id", "title", "text_for_embedding"):
        nulls = int(df[col].isna().sum() + (df[col].astype(str).str.strip() == "").sum()) if col in df else n
        checks[f"{col}_not_null"] = {"nulls": nulls, "pass": nulls == 0}
    dupes = int(df.duplicated(subset=["paper_id"]).sum()) if "paper_id" in df else 0
    checks["paper_id_unique"] = {"duplicates": dupes, "pass": dupes == 0}
    if "summary" in df:
        short = int((df["summary"].astype(str).str.len() < 30).sum())
    else:
        short = n
    checks["summary_min_length_30"] = {"too_short": short, "pass": short == 0}
    success = all(v.get("pass") for v in checks.values())
    return {"success": success, "checks": checks, "engine": "manual"}


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tao bo data quality checks (GX 1.x neu co, fallback manual)."""
    result: dict[str, Any] = _manual_checks(df, settings)
    # Co gang chay GX 1.x de dung chuan slide; that bai thi giu manual
    try:
        import great_expectations as gx  # type: ignore

        context = gx.get_context(mode="ephemeral")
        data_source = context.data_sources.add_pandas(name="papers_source")
        data_asset = data_source.add_dataframe_asset(name="papers_asset")
        batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
        batch = batch_def.get_batch(batch_parameters={"dataframe": df})
        import great_expectations.expectations as gxe  # type: ignore

        gx_results = []
        gx_results.append(batch.validate(gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000)))
        for col in ("paper_id", "title", "text_for_embedding"):
            gx_results.append(batch.validate(gxe.ExpectColumnValuesToNotBeNull(column=col)))
        gx_results.append(batch.validate(gxe.ExpectColumnValuesToBeUnique(column="paper_id")))
        gx_results.append(
            batch.validate(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))
        )
        result["gx_validations"] = [
            {"success": bool(r.get("success", r))} if isinstance(r, dict) else {"success": bool(getattr(r, "success", True))}
            for r in gx_results
        ]
        result["engine"] = "great_expectations"
        result["success"] = result["success"] and all(v["success"] for v in result["gx_validations"])
    except Exception as exc:  # noqa: BLE001
        result["gx_note"] = f"GX skipped, manual used: {exc}"

    out_path = settings.paths.quality_dir / f"{report_name}.json"
    ensure_parent(out_path)
    payload = {
        "report": report_name,
        "rows": len(df),
        "success": bool(result["success"]),
        **result,
        "generated_at": datetime.now().isoformat(),
    }
    write_json(out_path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tong hop freshness report."""
    from pathlib import Path

    rp = Path(report_path)
    total = len(df)
    if total and "age_days" in df:
        stale = int((pd.to_numeric(df["age_days"], errors="coerce") > settings.freshness_threshold_days).sum())
    else:
        stale = 0
    latest = str(df["published"].max()) if total and "published" in df else ""
    oldest = str(df["published"].min()) if total and "published" in df else ""
    stale_rate = (stale / total) if total else 0.0
    payload = {
        "latest_published": latest,
        "oldest_published": oldest,
        "stale_rows": stale,
        "total_rows": total,
        "stale_rate": stale_rate,
        "threshold_days": settings.freshness_threshold_days,
        "is_fresh": bool(stale_rate <= 0.25),
        "generated_at": datetime.now().isoformat(),
    }
    ensure_parent(rp)
    write_json(rp, payload)
    return payload
