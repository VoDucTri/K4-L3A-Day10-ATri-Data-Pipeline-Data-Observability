from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import read_json, safe_slug, write_json
from retrieval.embeddings import MiniLMEmbeddings

try:
    import chromadb

    _CHROMA_OK = True
except Exception:
    chromadb = None  # type: ignore
    _CHROMA_OK = False


# Backend vector store. "numpy" (mac dinh): cosine brute-force bang numpy
# tren vector MiniLM that - chinh xac, khong can native hnswlib (von gay
# segfault tren may thieu VC++ runtime moi). Dat VECTOR_BACKEND=chroma de
# dung ChromaDB that tren may khoe.
VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "numpy").strip().lower() or "numpy"


@dataclass(frozen=True)
class SearchResult:
    paper_id: str
    title: str
    score: float
    content: str
    metadata: dict[str, Any]


def _token_overlap_score(query: str, doc: str) -> float:
    qt = set(re.findall(r"[a-z0-9]+", query.lower()))
    dt = set(re.findall(r"[a-z0-9]+", doc.lower()))
    if not qt or not dt:
        return 0.0
    return len(qt & dt) / len(qt | dt)


def _cosine_search(
    query_vec: list[float], doc_vecs: list[list[float]], k: int
) -> list[tuple[int, float]]:
    import numpy as np

    q = np.asarray(query_vec, dtype=np.float64)
    qn = np.linalg.norm(q) or 1.0
    M = np.asarray(doc_vecs, dtype=np.float64)
    norms = np.linalg.norm(M, axis=1)
    norms[norms == 0] = 1.0
    sims = (M @ q) / (norms * qn)
    order = np.argsort(-sims, kind="stable")[:k]
    return [(int(i), max(0.0, float(sims[i]))) for i in order]


class LocalEmbeddingIndex:
    def __init__(
        self,
        settings: Settings,
        collection_name: str,
        documents: list[dict[str, Any]],
        persist_path: Path,
        vectors: list[list[float]] | None = None,
    ):
        self.settings = settings
        self.collection_name = collection_name
        self.documents = documents
        self.persist_path = persist_path
        self.embedding_model = MiniLMEmbeddings(settings.embedding_model)
        self.embedding_backend = "local-fallback"
        self.client = None
        self.collection = None
        self.vectors: list[list[float]] | None = vectors
        if VECTOR_BACKEND == "chroma" and _CHROMA_OK:
            try:
                self.client = chromadb.PersistentClient(path=str(persist_path))
                self.collection = self.client.get_collection(name=collection_name)
                self.embedding_backend = f"chroma-{self.embedding_model.backend}"
            except Exception:
                self.collection = None
        if self.collection is None and self.vectors:
            self.embedding_backend = f"numpy-{self.embedding_model.backend}"
        self.documents_by_paper_id = {document["paper_id"].lower(): document for document in documents}
        self.documents_by_title = {document["title"].lower(): document for document in documents}

    @staticmethod
    def _build_documents(df: pd.DataFrame) -> list[dict[str, Any]]:
        df = df.fillna("")
        records = df.to_dict(orient="records")
        documents: list[dict[str, Any]] = []
        for index, row in enumerate(records):
            documents.append(
                {
                    "record_id": f"{row['paper_id']}::{index}",
                    "paper_id": str(row["paper_id"]),
                    "title": str(row["title"]),
                    "content": str(row["text_for_embedding"]),
                    "metadata": {
                        "paper_id": str(row["paper_id"]),
                        "title": str(row["title"]),
                        "published": str(row["published"]),
                        "authors_joined": str(row["authors_joined"]),
                        "categories_joined": str(row["categories_joined"]),
                        "summary": str(row["summary"]),
                        "abs_url": str(row["abs_url"]),
                        "pdf_url": str(row["pdf_url"]),
                    },
                }
            )
        return documents

    @staticmethod
    def _derive_collection_name(settings: Settings, embeddings_output_path: Path | None) -> str:
        if embeddings_output_path is None:
            return settings.baseline_collection_name

        name_map = {
            settings.paths.embeddings_json.resolve(): settings.baseline_collection_name,
            settings.paths.corrupted_embeddings_json.resolve(): settings.corrupted_collection_name,
            settings.paths.repaired_embeddings_json.resolve(): settings.repaired_collection_name,
        }
        resolved_path = embeddings_output_path.resolve()
        if resolved_path in name_map:
            return name_map[resolved_path]
        return safe_slug(embeddings_output_path.stem)

    @classmethod
    def build(
        cls,
        df: pd.DataFrame,
        settings: Settings,
        embeddings_output_path: Path | None = None,
    ) -> "LocalEmbeddingIndex":
        collection_name = cls._derive_collection_name(settings, embeddings_output_path)
        documents = cls._build_documents(df)
        persist_path = settings.paths.chroma_dir
        persist_path.mkdir(parents=True, exist_ok=True)

        embedding_model = MiniLMEmbeddings(settings.embedding_model)
        vectors = embedding_model.embed_documents([d["content"] for d in documents])

        backend = f"numpy-{embedding_model.backend}"
        collection = None
        client = None
        if VECTOR_BACKEND == "chroma" and _CHROMA_OK:
            try:
                client = chromadb.PersistentClient(path=str(persist_path))
                try:
                    client.delete_collection(name=collection_name)
                except Exception:
                    pass
                collection = client.create_collection(
                    name=collection_name,
                    configuration={"hnsw": {"space": "cosine"}},
                )
                collection.add(
                    ids=[document["record_id"] for document in documents],
                    embeddings=vectors,
                    documents=[document["content"] for document in documents],
                    metadatas=[document["metadata"] for document in documents],
                )
                backend = f"chroma-{embedding_model.backend}"
            except Exception:
                collection = None
                client = None
                backend = f"numpy-{embedding_model.backend}"

        manifest_path = embeddings_output_path or settings.paths.embeddings_json
        write_json(
            manifest_path,
            {
                "backend": backend,
                "vector_backend": VECTOR_BACKEND,
                "embedding_model": settings.embedding_model,
                "embedding_dim": len(vectors[0]) if vectors else 0,
                "persist_path": str(persist_path),
                "collection_name": collection_name,
                "documents": documents,
                "vectors": vectors,
            },
        )
        return cls(
            settings=settings,
            collection_name=collection_name,
            documents=documents,
            persist_path=persist_path,
            vectors=vectors,
        )

    @classmethod
    def load(cls, settings: Settings, embeddings_path: Path | None = None) -> "LocalEmbeddingIndex":
        payload = read_json(embeddings_path or settings.paths.embeddings_json)
        return cls(
            settings=settings,
            collection_name=payload["collection_name"],
            documents=payload["documents"],
            persist_path=Path(payload["persist_path"]),
            vectors=payload.get("vectors"),
        )

    def _search_numpy(self, query: str, k: int) -> list[SearchResult]:
        if not self.vectors:
            return []
        try:
            qv = self.embedding_model.embed_query(query)
            hits = _cosine_search(qv, self.vectors, k)
            return [
                SearchResult(
                    paper_id=self.documents[i]["paper_id"],
                    title=self.documents[i]["title"],
                    score=score,
                    content=self.documents[i]["content"],
                    metadata=self.documents[i]["metadata"],
                )
                for i, score in hits
            ]
        except Exception:
            return []

    def _search_lexical(self, query: str, k: int) -> list[SearchResult]:
        ranked = sorted(
            self.documents,
            key=lambda d: _token_overlap_score(query, f"{d['title']} {d['content']}"),
            reverse=True,
        )[:k]
        return [
            SearchResult(
                paper_id=d["paper_id"],
                title=d["title"],
                score=_token_overlap_score(query, f"{d['title']} {d['content']}"),
                content=d["content"],
                metadata=d["metadata"],
            )
            for d in ranked
        ]

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        k = top_k or self.settings.top_k
        if self.collection is not None:
            try:
                query_embedding = self.embedding_model.embed_query(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    include=["documents", "metadatas", "distances"],
                )
                ids = results.get("ids", [[]])[0]
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]

                scored: list[SearchResult] = []
                for record_id, content, metadata, distance in zip(ids, documents, metadatas, distances, strict=False):
                    if not record_id or not metadata or not content:
                        continue
                    scored.append(
                        SearchResult(
                            paper_id=str(metadata["paper_id"]),
                            title=str(metadata["title"]),
                            score=max(0.0, 1.0 - float(distance or 0.0)),
                            content=str(content),
                            metadata=dict(metadata),
                        )
                    )
                if scored:
                    return scored
            except Exception:
                pass
        if VECTOR_BACKEND != "lexical":
            hits = self._search_numpy(query, k)
            if hits:
                return hits
        return self._search_lexical(query, k)

    def lookup(self, value: str) -> dict[str, Any] | None:
        needle = value.strip().lower()
        if needle in self.documents_by_paper_id:
            return self.documents_by_paper_id[needle]
        if needle in self.documents_by_title:
            return self.documents_by_title[needle]
        return None
