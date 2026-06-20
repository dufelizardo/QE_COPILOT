from __future__ import annotations

import uuid
from app.domain.ports.knowledge_port import RetrievalPort, IngestionPort, KnowledgeChunk


class QdrantStore(RetrievalPort, IngestionPort):
    """
    Implementação concreta usando Qdrant (local ou servidor remoto).
    Requer: pip install qdrant-client sentence-transformers
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "qe_copilot",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        in_memory: bool = False,
    ):
        self._host = host
        self._port = port
        self._collection_name = collection_name
        self._embedding_model_name = embedding_model
        self._in_memory = in_memory
        self._client = None
        self._embedder = None

    def _ensure_ready(self) -> None:
        if self._client is not None:
            return
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError(
                "qdrant-client e sentence-transformers são necessários. "
                "Execute: pip install qdrant-client sentence-transformers"
            )

        if self._in_memory:
            self._client = QdrantClient(":memory:")
        else:
            self._client = QdrantClient(host=self._host, port=self._port)

        self._embedder = SentenceTransformer(self._embedding_model_name)
        dim = self._embedder.get_sentence_embedding_dimension()

        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection_name not in existing:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.encode(texts, normalize_embeddings=True).tolist()

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[KnowledgeChunk]:
        self._ensure_ready()
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        q_vec = self._embed([query])[0]
        qdrant_filter = None
        if filter_metadata:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_metadata.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = self._client.search(
            collection_name=self._collection_name,
            query_vector=q_vec,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [
            KnowledgeChunk(
                conteudo=r.payload.get("conteudo", ""),
                fonte=r.payload.get("fonte", "unknown"),
                score=float(r.score),
                metadata={k: v for k, v in r.payload.items() if k not in ("conteudo", "fonte")},
            )
            for r in results
        ]

    def ingest(self, conteudo: str, metadata: dict) -> bool:
        self._ensure_ready()
        from qdrant_client.models import PointStruct
        try:
            vec = self._embed([conteudo])[0]
            self._client.upsert(
                collection_name=self._collection_name,
                points=[PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload={"conteudo": conteudo, "fonte": metadata.get("fonte", "unknown"), **metadata},
                )],
            )
            return True
        except Exception:
            return False

    def ingest_batch(self, documentos: list[dict]) -> int:
        self._ensure_ready()
        from qdrant_client.models import PointStruct
        try:
            texts = [d["conteudo"] for d in documentos]
            vecs = self._embed(texts)
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload={
                        "conteudo": d["conteudo"],
                        "fonte": d.get("metadata", {}).get("fonte", "unknown"),
                        **d.get("metadata", {}),
                    },
                )
                for d, vec in zip(documentos, vecs)
            ]
            self._client.upsert(collection_name=self._collection_name, points=points)
            return len(points)
        except Exception:
            return 0
