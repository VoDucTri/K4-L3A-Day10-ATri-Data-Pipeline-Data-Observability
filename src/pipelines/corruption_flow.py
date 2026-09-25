from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()

    # 1. Load baseline
    baseline_df = pd.read_csv(settings.paths.clean_csv)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    print(f"Baseline: {len(baseline_df)} dong")

    # 2-3. Corrupt + save
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    print(f"Corrupted: {len(corrupted_df)} dong (xem {settings.paths.corruption_log})")

    # 4. Rebuild index + evaluate corrupted
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, embeddings_output_path=settings.paths.corrupted_embeddings_json
    )
    corrupted_bundle = evaluate_pipeline(
        settings, corrupted_index, settings.paths.eval_testset,
        settings.paths.corrupted_metrics, settings.paths.corrupted_answers,
    )
    print(f"Corrupted metrics: hit={corrupted_bundle.summary['retrieval_hit_rate']:.3f} "
          f"f1={corrupted_bundle.summary['mean_token_f1']:.3f}")

    # 5. Quality/freshness corrupted
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted_quality_report")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, settings.paths.quality_dir / "corrupted_freshness_report.json"
    )
    print(f"Corrupted quality success={corrupted_quality['success']} "
          f"fresh={corrupted_freshness['is_fresh']}")

    # 6. Repair tu raw (idempotent)
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"Repaired: {len(repaired_df)} dong")

    # 7. Evaluate repaired
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, embeddings_output_path=settings.paths.repaired_embeddings_json
    )
    repaired_bundle = evaluate_pipeline(
        settings, repaired_index, settings.paths.eval_testset,
        settings.paths.repaired_metrics, settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired_quality_report")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, settings.paths.quality_dir / "repaired_freshness_report.json"
    )
    print(f"Repaired metrics: hit={repaired_bundle.summary['retrieval_hit_rate']:.3f} "
          f"f1={repaired_bundle.summary['mean_token_f1']:.3f}")

    # 8. Comparison report
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics, corrupted_bundle.summary, repaired_bundle.summary,
        corrupted_quality, repaired_quality, corrupted_freshness, repaired_freshness,
    )
    print(f"Comparison report: {settings.paths.comparison_report}")
