from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from core.utils import ensure_parent, write_json


def _rebuild_text(row: pd.Series) -> str:
    return (
        f"Title: {row['title']}\n"
        f"Authors: {row['authors_joined']}\n"
        f"Published: {row['published']}\n"
        f"Categories: {row['categories_joined'] or row.get('primary_category', '')}\n"
        f"Summary: {row['summary']}"
    )


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate 6 dang data corruption tren ban copy."""
    log: dict = {"corruptions": []}
    corrupted = df.copy().reset_index(drop=True)
    if corrupted.empty:
        return corrupted

    # 1. Drop latest records (2 bai moi nhat theo published desc)
    n_drop = min(2, len(corrupted))
    dropped_ids = corrupted.iloc[:n_drop]["paper_id"].tolist()
    corrupted = corrupted.iloc[n_drop:].reset_index(drop=True)
    log["corruptions"].append({"type": "drop_latest", "count": n_drop, "paper_ids": dropped_ids})

    # Cac index muc tieu (an toan voi df nho)
    def idxs(*cands: int) -> list[int]:
        return [i for i in cands if 0 <= i < len(corrupted)]

    # 2. Blank summary (3 dong)
    blank_idx = idxs(1, 2, 3)[: min(3, len(corrupted))]
    for i in blank_idx:
        corrupted.at[i, "summary"] = ""
        corrupted.at[i, "summary_chars"] = 0
        corrupted.at[i, "text_for_embedding"] = _rebuild_text(corrupted.iloc[i])
    log["corruptions"].append({"type": "blank_summary", "count": len(blank_idx), "rows": blank_idx})

    # 3. Inject noise
    noise_idx = idxs(0, 4, 5)[: min(3, len(corrupted))]
    for i in noise_idx:
        corrupted.at[i, "summary"] = str(corrupted.at[i, "summary"]) + " @@@###XXX_noise_noise"
        corrupted.at[i, "summary_chars"] = len(str(corrupted.at[i, "summary"]))
        corrupted.at[i, "text_for_embedding"] = _rebuild_text(corrupted.iloc[i])
    log["corruptions"].append({"type": "inject_noise", "count": len(noise_idx), "rows": noise_idx})

    # 4. Truncate title (3 dong -> 30 ky tu)
    trunc_idx = idxs(0, 1, 6)[: min(3, len(corrupted))]
    for i in trunc_idx:
        corrupted.at[i, "title"] = str(corrupted.at[i, "title"])[:30]
        corrupted.at[i, "text_for_embedding"] = _rebuild_text(corrupted.iloc[i])
    log["corruptions"].append({"type": "truncate_title_30", "count": len(trunc_idx), "rows": trunc_idx})

    # 5. Lam cu ngay (8 dong -> 2020-01-01 de stale_rate >25% -> is_fresh=False)
    stale_idx = idxs(0, 1, 2, 3, 4, 5, 6, 7)[: min(8, len(corrupted))]
    now_d = datetime.now(UTC).date()
    for i in stale_idx:
        corrupted.at[i, "published"] = "2020-01-01"
        try:
            corrupted.at[i, "age_days"] = (now_d - datetime(2020, 1, 1).date()).days
        except Exception:
            pass
        corrupted.at[i, "text_for_embedding"] = _rebuild_text(corrupted.iloc[i])
    log["corruptions"].append({"type": "stale_date_2020", "count": len(stale_idx), "rows": stale_idx})

    # 6. Duplicate rows (2 dong dau)
    dup_n = min(2, len(corrupted))
    dupes = corrupted.iloc[:dup_n].copy()
    corrupted = pd.concat([corrupted, dupes], ignore_index=True)
    log["corruptions"].append({"type": "duplicate_rows", "count": int(dup_n)})

    log["result_rows"] = int(len(corrupted))
    log["generated_at"] = datetime.now(UTC).isoformat()
    lp = Path(output_log_path)
    ensure_parent(lp)
    write_json(lp, log)
    return corrupted
