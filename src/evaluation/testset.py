from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import ensure_parent, first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tao bo evaluation set tu cleaned dataframe."""
    if len(df) < 5:
        raise ValueError(f"Need >=5 documents, got {len(df)}")
    out = Path(output_path)
    # Chon toi da 8 paper dai dien, cach deu de phu thoi gian
    n_pick = min(8, len(df))
    step = max(1, len(df) // n_pick)
    picks = df.iloc[::step].head(n_pick)

    items: list[dict[str, Any]] = []
    qid = 0
    for _, row in picks.iterrows():
        pid = str(row["paper_id"])
        title = str(row["title"])
        truth_summary = first_sentence(str(row["summary"]))
        truth_authors = str(row["authors_joined"] or "Unknown")
        truth_date = str(row["published"])
        truth_cats = str(row["categories_joined"] or row.get("primary_category", ""))

        cands = [
            ("summary", f"What is the paper '{title}' about?", truth_summary),
            ("authors", f"Who authored '{title}'? List the authors.", truth_authors),
            ("date", f"When was '{title}' published? Give the publication date.", truth_date),
            ("categories", f"What categories does '{title}' belong to?", truth_cats or truth_summary),
        ]
        for qtype, q, truth in cands:
            if not truth or not truth.strip():
                continue
            qid += 1
            items.append(
                {
                    "id": f"q{qid:03d}_{qtype}",
                    "question_type": qtype,
                    "question": q,
                    "ground_truth": truth,
                    "ground_truth_doc_ids": [pid],
                }
            )
    ensure_parent(out)
    write_json(out, items)
    return items
