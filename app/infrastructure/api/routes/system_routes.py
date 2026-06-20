from __future__ import annotations

from fastapi import APIRouter, Request
from app.infrastructure.api.schemas.api_schemas import HealthResponse, IngestDocumentRequest, IngestBatchRequest, IngestResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health(request: Request):
    container = request.app.state.container
    llm_ok = container.llm.health_check()
    rag_enabled = container.rag_service is not None
    return HealthResponse(status="ok" if llm_ok else "degraded", llm_ok=llm_ok, rag_enabled=rag_enabled)


# ── RAG Ingestion ──────────────────────────────────────────────────────────

rag_router = APIRouter(prefix="/rag", tags=["RAG"])


@rag_router.post("/ingest", response_model=IngestResponse, summary="Indexa um documento no RAG")
async def ingest_document(body: IngestDocumentRequest, request: Request):
    container = request.app.state.container
    if not container.rag_service:
        return IngestResponse(success=False, indexed=0, message="RAG não está habilitado (rag_enabled=false).")
    ok = container.rag_service.ingest_document(
        conteudo=body.conteudo,
        fonte=body.fonte,
        tipo=body.tipo,
        extra_metadata=body.metadata,
    )
    return IngestResponse(success=ok, indexed=1 if ok else 0, message="ok" if ok else "Falha na ingestão.")


@rag_router.post("/ingest-batch", response_model=IngestResponse, summary="Indexa múltiplos documentos")
async def ingest_batch(body: IngestBatchRequest, request: Request):
    container = request.app.state.container
    if not container.rag_service:
        return IngestResponse(success=False, indexed=0, message="RAG não está habilitado.")
    documentos = [
        {"conteudo": d.conteudo, "metadata": {"fonte": d.fonte, "tipo": d.tipo, **d.metadata}}
        for d in body.documentos
    ]
    indexed = container.rag_service.ingest_batch(documentos)
    return IngestResponse(success=indexed > 0, indexed=indexed, message=f"{indexed} documento(s) indexados.")
