from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injeta um request_id único em cada request e o expõe no header de resposta."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Registra latência de cada request no header X-Process-Time."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        elapsed = round((time.monotonic() - start) * 1000, 1)
        response.headers["X-Process-Time-Ms"] = str(elapsed)
        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Autenticação simples via header X-API-Key.
    Em produção, substituir por OAuth2 / JWT.
    Rotas /health e /docs são públicas.
    """

    PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, api_key: str):
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        provided = request.headers.get("X-API-Key", "")
        if not self._api_key or provided == self._api_key:
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "API key inválida ou ausente."},
        )
