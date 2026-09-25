# Corruption & Repair — 3-State Comparison

| Metric | Baseline (sach) | Corrupted (loi) | Repaired (sua) |
|---|---|---|---|
| samples | 32 | 32 | 32 |
| retrieval_hit_rate | 1.0000 | 0.7500 | 1.0000 |
| mean_token_f1 | 0.7500 | 0.5106 | 0.7500 |
| judge_accuracy | 0.7500 | 0.5000 | 0.7500 |
| mean_judge_score | 4 | 3 | 4 |

## Quality gate
- Corrupted: success=False engine=great_expectations
- Repaired: success=True engine=great_expectations

## Freshness
- Corrupted: is_fresh=False stale=10/24
- Repaired: is_fresh=True stale=0/24

## Conclusion
Du lieu loi lam chi so giam va bi Quality Gate bat; repair tu raw khoi phuc gan baseline (idempotent).
