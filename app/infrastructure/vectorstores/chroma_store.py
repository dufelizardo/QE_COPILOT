from __future__ import annotations

from app.domain.ports.knowledge_port import RetrievalPort, IngestionPort, KnowledgeChunk


class ChromaStore(RetrievalPort, IngestionPort):
    """
    Implementação concreta de RetrievalPort + IngestionPort usando ChromaDB.
    Lazy import — chromadb só é importado se esta classe for instanciada.
    """

    def __init__(self, persist_path: str = "./data/vectorstore/chroma", collection_name: str = "qe_copilot"):
        self._persist_path = persist_path
        self._collection_name = collection_name
        self._client = None
        self._collection = None

    def _ensure_connected(self) -> None:
        if self._client is not None:
            return
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=self._persist_path)
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except ImportError:
            raise RuntimeError(
                "chromadb não está instalado. Execute: pip install chromadb"
            )

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[KnowledgeChunk]:
        self._ensure_connected()
        where = filter_metadata or None
        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self._collection.count() or 1),
            where=where,
        )
        chunks = []
        if not results["documents"] or not results["documents"][0]:
            return chunks
        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append(KnowledgeChunk(
                conteudo=doc,
                fonte=meta.get("fonte", "unknown"),
                score=1.0 - float(distance),
                metadata=meta,
            ))
        return sorted(chunks, key=lambda c: c.score, reverse=True)

    def ingest(self, conteudo: str, metadata: dict) -> bool:
        self._ensure_connected()
        import hashlib
        doc_id = hashlib.md5(conteudo.encode()).hexdigest()
        try:
            self._collection.upsert(
                ids=[doc_id],
                documents=[conteudo],
                metadatas=[metadata],
            )
            return True
        except Exception:
            return False

    def ingest_batch(self, documentos: list[dict]) -> int:
        self._ensure_connected()
        import hashlib
        ids, docs, metas = [], [], []
        for d in documentos:
            conteudo = d.get("conteudo", "")
            meta = d.get("metadata", {})
            ids.append(hashlib.md5(conteudo.encode()).hexdigest())
            docs.append(conteudo)
            metas.append(meta)
        try:
            self._collection.upsert(ids=ids, documents=docs, metadatas=metas)
            return len(ids)
        except Exception:
            return 0

    def count(self) -> int:
        self._ensure_connected()
        return self._collection.count()
