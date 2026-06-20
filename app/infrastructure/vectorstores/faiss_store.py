from __future__ import annotations

import json
import os
import pickle
from pathlib import Path

from app.domain.ports.knowledge_port import RetrievalPort, IngestionPort, KnowledgeChunk


class FAISSStore(RetrievalPort, IngestionPort):
    """
    Implementação concreta usando FAISS (Facebook AI Similarity Search).
    Mantém índice em memória com persistência em disco via pickle.
    Requer: pip install faiss-cpu sentence-transformers
    """

    def __init__(
        self,
        persist_path: str = "./data/vectorstore/faiss",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ):
        self._persist_path = Path(persist_path)
        self._embedding_model_name = embedding_model
        self._index = None
        self._documents: list[dict] = []   # [{conteudo, fonte, metadata}]
        self._embedder = None
        self._loaded = False

    def _ensure_ready(self) -> None:
        if self._loaded:
            return
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError(
                "faiss-cpu e sentence-transformers são necessários. "
                "Execute: pip install faiss-cpu sentence-transformers"
            )
        self._faiss = faiss
        self._embedder = SentenceTransformer(self._embedding_model_name)
        self._dim = self._embedder.get_sentence_embedding_dimension()

        index_path = self._persist_path / "index.faiss"
        docs_path = self._persist_path / "documents.pkl"

        if index_path.exists() and docs_path.exists():
            self._index = self._faiss.read_index(str(index_path))
            with open(docs_path, "rb") as f:
                self._documents = pickle.load(f)
        else:
            self._index = self._faiss.IndexFlatIP(self._dim)   # Inner Product = cosine após normalização

        self._loaded = True

    def _embed(self, texts: list[str]):
        import numpy as np
        vecs = self._embedder.encode(texts, normalize_embeddings=True)
        return np.array(vecs, dtype="float32")

    def _save(self) -> None:
        self._persist_path.mkdir(parents=True, exist_ok=True)
        self._faiss.write_index(self._index, str(self._persist_path / "index.faiss"))
        with open(self._persist_path / "documents.pkl", "wb") as f:
            pickle.dump(self._documents, f)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[KnowledgeChunk]:
        self._ensure_ready()
        if self._index.ntotal == 0:
            return []

        q_vec = self._embed([query])
        k = min(top_k * 3, self._index.ntotal)  # busca mais para filtrar
        scores, indices = self._index.search(q_vec, k)

        chunks = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue
            doc = self._documents[idx]
            if filter_metadata:
                if not all(doc["metadata"].get(k) == v for k, v in filter_metadata.items()):
                    continue
            chunks.append(KnowledgeChunk(
                conteudo=doc["conteudo"],
                fonte=doc["fonte"],
                score=float(score),
                metadata=doc["metadata"],
            ))
            if len(chunks) >= top_k:
                break

        return chunks

    def ingest(self, conteudo: str, metadata: dict) -> bool:
        self._ensure_ready()
        try:
            vec = self._embed([conteudo])
            self._index.add(vec)
            self._documents.append({
                "conteudo": conteudo,
                "fonte": metadata.get("fonte", "unknown"),
                "metadata": metadata,
            })
            self._save()
            return True
        except Exception:
            return False

    def ingest_batch(self, documentos: list[dict]) -> int:
        self._ensure_ready()
        try:
            texts = [d["conteudo"] for d in documentos]
            vecs = self._embed(texts)
            self._index.add(vecs)
            for d in documentos:
                self._documents.append({
                    "conteudo": d["conteudo"],
                    "fonte": d.get("metadata", {}).get("fonte", "unknown"),
                    "metadata": d.get("metadata", {}),
                })
            self._save()
            return len(documentos)
        except Exception:
            return 0

    def count(self) -> int:
        self._ensure_ready()
        return self._index.ntotal
