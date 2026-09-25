# Phase 1 — Baseline Report

## 1. Source
| Metric | Value |
|---|---|
| source | Crossref REST API |
| query | agentic retrieval augmented generation large language model |
| max_results | 24 |
| clean_rows | 24 |

## 2. RAG Metrics
| Metric | Value |
|---|---|
| samples | 32 |
| retrieval_hit_rate | 1.0 |
| mean_token_f1 | 0.75 |
| judge_accuracy | 0.75 |
| mean_judge_score | 4 |
| ragas | {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'} |

## 3. Data Quality Gate
- success: True
- engine: great_expectations
- rows: 24

## 4. Freshness
| Metric | Value |
|---|---|
| latest_published | 2026-09-15 |
| oldest_published | 2026-04-01 |
| stale_rows | 0 |
| total_rows | 24 |
| stale_rate | 0.0 |
| threshold_days | 180 |
| is_fresh | True |
| generated_at | 2026-09-25T16:40:52.540504 |

## 5. Conclusion
Baseline pipeline chay end-to-end: ingestion -> cleaning -> quality gate -> Chroma index -> evaluation.
