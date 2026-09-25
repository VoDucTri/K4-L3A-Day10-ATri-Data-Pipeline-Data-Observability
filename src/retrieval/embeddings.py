from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache


def _hash_vector(text: str, dim: int = 128) -> list[float]:
    """Fallback deterministic embedding khi thieu moi backend nang."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    vec = [0.0] * dim
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


try:
    from langchain_core.embeddings import Embeddings as _BaseEmbeddings
except Exception:  # minimal stub neu thieu langchain_core

    class _BaseEmbeddings:  # type: ignore
        pass


try:
    from sentence_transformers import SentenceTransformer

    _ST_OK = True
except Exception:
    SentenceTransformer = None  # type: ignore
    _ST_OK = False


try:
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2 as _OnnxEF

    _ONNX_OK = True
except Exception:
    _OnnxEF = None  # type: ignore
    _ONNX_OK = False


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    if not _ST_OK:
        raise RuntimeError("sentence_transformers unavailable")
    return SentenceTransformer(model_name)


@lru_cache(maxsize=4)
def _load_onnx():
    if not _ONNX_OK:
        raise RuntimeError("chromadb ONNX embedding unavailable")
    return _OnnxEF()


class MiniLMEmbeddings(_BaseEmbeddings):
    """Uu tien: sentence_transformers -> Chroma ONNX MiniLM -> hash fallback.

    Interface giu nguyen (embed_documents / embed_query) nen index.py,
    metrics.py khong can doi. Thuoc tinh `backend` cho biet dang dung gi:
    'st' | 'onnx' | 'hash'.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.backend = "hash"
        self.model = None
        if _ST_OK:
            try:
                self.model = _load_model(model_name)
                self.backend = "st"
                return
            except Exception:
                self.model = None
        if _ONNX_OK:
            try:
                self.model = _load_onnx()
                self.backend = "onnx"
            except Exception:
                self.model = None
                self.backend = "hash"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.backend == "st" and self.model is not None:
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        if self.backend == "onnx" and self.model is not None:
            return [list(map(float, v)) for v in self.model(list(texts))]
        return [_hash_vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        if self.backend == "st" and self.model is not None:
            embedding = self.model.encode([text], normalize_embeddings=True)
            return embedding[0].tolist()
        if self.backend == "onnx" and self.model is not None:
            return list(map(float, self.model([text])[0]))
        return _hash_vector(text)
