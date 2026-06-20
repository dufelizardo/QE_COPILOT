from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ── Provider B3GPT ────────────────────────────────────────────────────
    b3gpt_token: str = Field(..., description="API key para o B3GPT")
    b3gpt_model_name: str = Field(..., description="Nome do deployment/modelo B3GPT")
    b3gpt_base_url: str = Field(
        default="https://api-b3gpt.b3.com.br/internal-api/b3gpt-llms/v1/openai",
    )
    b3gpt_timeout: int = Field(default=60)

    # ── API ───────────────────────────────────────────────────────────────
    api_key: str = Field(default="", description="X-API-Key para autenticação. Vazio = sem auth.")

    # ── RAG ───────────────────────────────────────────────────────────────
    rag_enabled: bool = Field(default=False, description="Habilita RAG no pipeline")
    vector_store_type: str = Field(default="chroma", description="chroma | faiss | qdrant")
    vector_store_path: str = Field(default="./data/vectorstore")
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)

    # ── Observabilidade ───────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # ── App ───────────────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    max_retries: int = Field(default=2)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
