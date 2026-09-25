from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import ensure_parent, write_text


def _kv_table(data: dict[str, Any]) -> str:
    lines = ["| Metric | Value |", "|---|---|"]
    for k, v in data.items():
        if isinstance(v, dict):
            v = f"success={v.get('success')}" if "success" in v else str(v)[:120]
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    rp = Path(report_path)
    md = f"""# Phase 1 — Baseline Report

## 1. Source
{_kv_table(source_summary)}

## 2. RAG Metrics
{_kv_table(metrics)}

## 3. Data Quality Gate
- success: {quality.get("success")}
- engine: {quality.get("engine")}
- rows: {quality.get("rows")}

## 4. Freshness
{_kv_table(freshness)}

## 5. Conclusion
Baseline pipeline chay end-to-end: ingestion -> cleaning -> quality gate -> Chroma index -> evaluation.
"""
    ensure_parent(rp)
    write_text(rp, md)


def _mrow(name: str, b: dict, c: dict, r: dict) -> str:
    def g(d: dict):
        v = d.get(name, "-")
        return f"{v:.4f}" if isinstance(v, float) else str(v)

    return f"| {name} | {g(b)} | {g(c)} | {g(r)} |"


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    rp = Path(report_path)
    md = f"""# Corruption & Repair — 3-State Comparison

| Metric | Baseline (sach) | Corrupted (loi) | Repaired (sua) |
|---|---|---|---|
{_mrow("samples", baseline_metrics, corrupted_metrics, repaired_metrics)}
{_mrow("retrieval_hit_rate", baseline_metrics, corrupted_metrics, repaired_metrics)}
{_mrow("mean_token_f1", baseline_metrics, corrupted_metrics, repaired_metrics)}
{_mrow("judge_accuracy", baseline_metrics, corrupted_metrics, repaired_metrics)}
{_mrow("mean_judge_score", baseline_metrics, corrupted_metrics, repaired_metrics)}

## Quality gate
- Corrupted: success={corrupted_quality.get("success")} engine={corrupted_quality.get("engine")}
- Repaired: success={repaired_quality.get("success")} engine={repaired_quality.get("engine")}

## Freshness
- Corrupted: is_fresh={corrupted_freshness.get("is_fresh")} stale={corrupted_freshness.get("stale_rows")}/{corrupted_freshness.get("total_rows")}
- Repaired: is_fresh={repaired_freshness.get("is_fresh")} stale={repaired_freshness.get("stale_rows")}/{repaired_freshness.get("total_rows")}

## Conclusion
Du lieu loi lam chi so giam va bi Quality Gate bat; repair tu raw khoi phuc gan baseline (idempotent).
"""
    ensure_parent(rp)
    write_text(rp, md)
