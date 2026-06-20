"""
domain/ports — Interfaces (abstrações) do domínio QA.
Use cases dependem apenas destes ports — nunca de implementações concretas.

- llm_port.py          → LLMPort (qualquer provider LLM)
- knowledge_port.py    → RetrievalPort + IngestionPort (RAG de alto nível)
- vector_store_port.py → VectorStorePort (infraestrutura de embedding)
"""
from app.domain.ports.llm_port import LLMPort, LLMMessage, LLMResponse, LLMError
from app.domain.ports.knowledge_port import RetrievalPort, IngestionPort, KnowledgeChunk
from app.domain.ports.vector_store_port import VectorStorePort, VectorDocument, SearchResult

__all__ = [
    "LLMPort", "LLMMessage", "LLMResponse", "LLMError",
    "RetrievalPort", "IngestionPort", "KnowledgeChunk",
    "VectorStorePort", "VectorDocument", "SearchResult",
]
