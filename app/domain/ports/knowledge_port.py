from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class KnowledgeChunk:
    """Fragmento de conhecimento recuperado do repositório."""
    conteudo: str
    fonte: str
    score: float = 0.0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RetrievalPort(ABC):
    """
    Porta de saída para recuperação de conhecimento (RAG).
    Separada de IngestionPort — quem busca não precisa saber como indexar.
    Implementação concreta fica em infrastructure/rag/.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[KnowledgeChunk]:
        """
        Busca semântica no repositório de conhecimento.
        Retorna chunks ordenados por relevância decrescente.
        """
        ...


class IngestionPort(ABC):
    """
    Porta de entrada para indexação de novos documentos.
    Separada de RetrievalPort — quem faz retrieval não precisa saber sobre ingestão.
    """

    @abstractmethod
    def ingest(self, conteudo: str, metadata: dict) -> bool:
        """
        Indexa um documento no repositório.
        Retorna True se a ingestão foi bem-sucedida.
        """
        ...

    @abstractmethod
    def ingest_batch(self, documentos: list[dict]) -> int:
        """
        Indexa múltiplos documentos. Retorna quantos foram indexados com sucesso.
        Cada dict deve ter 'conteudo' e 'metadata'.
        """
        ...
