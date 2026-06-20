from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VectorDocument:
    """
    Documento indexado no vector store.
    Separado de KnowledgeChunk (que é o resultado do retrieval)
    para deixar claro que ingestão e busca têm contratos distintos.
    """
    conteudo: str
    fonte: str
    metadata: dict
    embedding: list[float] | None = None


@dataclass
class SearchResult:
    """Resultado de uma busca semântica no vector store."""
    conteudo: str
    fonte: str
    score: float
    metadata: dict


class VectorStorePort(ABC):
    """
    Port para qualquer implementação de vector store.
    Abstrai ChromaDB, FAISS, Qdrant — o domínio não conhece nenhum deles.

    Separado de KnowledgePort (que é a abstração de alto nível do RAG)
    porque o VectorStore é uma preocupação de infraestrutura:
    - VectorStorePort → ChromaStore, FAISSStore, QdrantStore
    - KnowledgePort   → RAGService (usa VectorStorePort internamente)

    Os use cases dependem de KnowledgePort, não de VectorStorePort.
    O Container injeta as implementações concretas.
    """

    @abstractmethod
    def add(self, documents: list[VectorDocument]) -> int:
        """
        Indexa documentos. Retorna quantos foram indexados com sucesso.
        Implementações devem usar upsert (evitar duplicatas por ID/hash).
        """
        ...

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        """
        Busca semântica. Retorna resultados ordenados por score decrescente.
        """
        ...

    @abstractmethod
    def count(self) -> int:
        """Retorna o total de documentos indexados."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verifica se o store está acessível."""
        ...
