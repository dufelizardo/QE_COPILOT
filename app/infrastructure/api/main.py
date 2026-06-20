from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.container.container import Container
from app.infrastructure.api.middleware.auth import APIKeyMiddleware, RequestIDMiddleware, TimingMiddleware
from app.infrastructure.api.routes.qa_routes import router as qa_router
from app.infrastructure.api.routes.system_routes import router as system_router, rag_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicializa o Container na startup e o expõe via app.state.
    Todas as rotas acessam dependências via request.app.state.container.
    """
    settings = get_settings()
    app.state.container = Container(settings)
    app.state.container.logger.info("api_startup", env=settings.app_env)
    yield
    app.state.container.logger.info("api_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="QE Copilot API",
        description=(
            "Quality Engineering Copilot — geração de análises de User Story, "
            "design de casos de teste, RTM bidirecional e criação de novas US."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middlewares ────────────────────────────────────────────────────────
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    api_key = getattr(settings, "api_key", "")
    if api_key:
        app.add_middleware(APIKeyMiddleware, api_key=api_key)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Rotas ─────────────────────────────────────────────────────────────
    app.include_router(system_router)
    app.include_router(rag_router)
    app.include_router(qa_router, prefix="/api/v1")

    return app


def get_app() -> FastAPI:
    """Entry point para uvicorn: uvicorn app.api.main:get_app --factory"""
    return create_app()


# Entry point direto (apenas quando .env estiver configurado)
try:
    app = create_app()
except Exception:
    app = None  # type: ignore  # não bloqueia imports em testes sem .env
