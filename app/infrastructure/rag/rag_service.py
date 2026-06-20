from __future__ import annotations

from app.domain.ports.knowledge_port import RetrievalPort, IngestionPort, KnowledgeChunk


class RAGService:
    """
    Serviço RAG que combina RetrievalPort + IngestionPort.
    Responsável por:
    - Busca semântica com reranking leve por relevância
    - Ingestão de documentos QA (standards, RTMs, test cases, docs)
    - Seleção de contexto por top-k com score mínimo

    É um adapter — conhece o mundo externo (vector stores),
    mas expõe a interface que os use cases conhecem (RetrievalPort).
    """

    def __init__(
        self,
        retrieval: RetrievalPort,
        ingestion: IngestionPort,
        min_score: float = 0.3,
    ):
        self._retrieval = retrieval
        self._ingestion = ingestion
        self._min_score = min_score

    # ── Retrieval ──────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[KnowledgeChunk]:
        """
        Busca com filtro por score mínimo.
        Chunks com score abaixo de min_score são descartados.
        """
        raw = self._retrieval.search(query=query, top_k=top_k * 2, filter_metadata=filter_metadata)
        filtered = [c for c in raw if c.score >= self._min_score]
        return filtered[:top_k]

    def search_for_context(self, query: str, top_k: int = 3) -> list[KnowledgeChunk]:
        """
        Versão otimizada para montagem de contexto LLM.
        Retorna top-k chunks com score mais alto, já ordenados.
        """
        chunks = self.search(query=query, top_k=top_k)
        return sorted(chunks, key=lambda c: c.score, reverse=True)

    # ── Ingestion ──────────────────────────────────────────────────────────

    def ingest_document(
        self,
        conteudo: str,
        fonte: str,
        tipo: str = "documento",
        extra_metadata: dict | None = None,
    ) -> bool:
        metadata = {"fonte": fonte, "tipo": tipo, **(extra_metadata or {})}
        return self._ingestion.ingest(conteudo=conteudo, metadata=metadata)

    def ingest_batch(self, documentos: list[dict]) -> int:
        """
        Ingere múltiplos documentos.
        Cada dict deve ter: conteudo, fonte, tipo (opcional), metadata (opcional).
        """
        normalized = []
        for d in documentos:
            meta = d.get("metadata", {})
            meta.setdefault("fonte", d.get("fonte", "unknown"))
            meta.setdefault("tipo", d.get("tipo", "documento"))
            normalized.append({"conteudo": d["conteudo"], "metadata": meta})
        return self._ingestion.ingest_batch(normalized)

    def ingest_user_story(self, us_nome: str, conteudo: str) -> bool:
        """Atalho para indexar uma User Story como documento de referência."""
        return self.ingest_document(
            conteudo=conteudo,
            fonte=f"us/{us_nome}",
            tipo="user_story",
            extra_metadata={"us_nome": us_nome},
        )

    def ingest_standard(self, nome: str, conteudo: str) -> bool:
        """Atalho para indexar um padrão/norma QA."""
        return self.ingest_document(
            conteudo=conteudo,
            fonte=f"standard/{nome}",
            tipo="standard",
            extra_metadata={"standard_nome": nome},
        )
