from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def main() -> None:
    settings = load_settings()
    print(f"Source: {settings.source_api} | query='{settings.source_query}' max={settings.max_results}")

    # 1-2. Raw records (fetch live hoac offline snapshot)
    try:
        records = fetch_source_records(settings)
        print(f"Da tai {len(records)} bai bao")
    except Exception as exc:
        print(f"Fetch live that bai ({exc}), dung snapshot: {settings.paths.raw_records_json}")
        records = load_raw_records(settings.paths.raw_records_json)
        print(f"Da tai {len(records)} bai bao (snapshot)")

    # 3-4. Cleaning + save
    df = build_clean_dataframe(records, now_utc())
    print(f"Clean thanh cong {len(df)} dong")
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))

    # 5. Chroma index (real neu du deps, fallback lexical neu khong)
    index = LocalEmbeddingIndex.build(df, settings)
    print(f"Index built: {index.collection_name} backend={index.embedding_backend}")

    # 6. Test set
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        testset = build_test_set(df, settings.paths.eval_testset)
    else:
        testset = read_json(settings.paths.eval_testset)
    print(f"Test set: {len(testset)} cau hoi")

    # 7. Evaluate
    bundle = evaluate_pipeline(
        settings, index, settings.paths.eval_testset,
        settings.paths.baseline_metrics, settings.paths.baseline_answers,
    )
    print(f"Metrics: hit_rate={bundle.summary['retrieval_hit_rate']:.3f} "
          f"f1={bundle.summary['mean_token_f1']:.3f} "
          f"judge_acc={bundle.summary['judge_accuracy']:.3f}")

    # 8. Quality + freshness
    quality = run_data_quality_checks(df, settings, "baseline_quality_report")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    print(f"Quality success={quality['success']} | Fresh is_fresh={freshness['is_fresh']}")

    # 9. Report
    generate_phase1_report(
        settings.paths.baseline_report,
        {"source": settings.source_api, "query": settings.source_query,
         "max_results": settings.max_results, "clean_rows": len(df)},
        bundle.summary, quality, freshness,
    )
    print(f"Report: {settings.paths.baseline_report}")

    # 10. Demo agent tren vai cau mau (rule-based, khong can LLM key)
    for item in testset[:3]:
        ans = answer_question(item["question"], settings=settings, index=index)
        print(f"Q: {item['question'][:80]}...\nA: {ans.answer[:160]}...")
