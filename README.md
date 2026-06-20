# QE Copilot

**Quality Engineering Copilot** — AI-powered assistant for analyzing User Stories, designing test cases, generating bidirectional RTMs, and creating new User Stories from scratch. Built on Clean Architecture with a B3GPT LLM provider, FastAPI REST layer, Streamlit frontend, and optional RAG knowledge base.

---

## Architecture

The project follows **Clean Architecture** strictly. Dependencies always point inward — the domain never knows about infrastructure.

```
app/
├── domain/                    # Pure domain — no external dependencies
│   ├── entities/
│   │   ├── requirement.py     # Requirement (input entity, alias UserStory)
│   │   ├── test_case.py       # TestCase + enums
│   │   └── rtm.py             # RTMEntry + QAArtefact
│   ├── ports/                 # Abstractions (ABCs)
│   │   ├── llm_port.py        # LLMPort → any LLM provider
│   │   ├── knowledge_port.py  # RetrievalPort + IngestionPort → RAG
│   │   └── vector_store_port.py # VectorStorePort → Chroma/FAISS/Qdrant
│   └── use_cases/
│       ├── analyze_user_story.py
│       ├── design_tests.py
│       ├── generate_rtm.py
│       └── create_user_story.py
│
├── adapters/                  # Translators between domain and infrastructure
│   ├── agents/
│   │   └── qa_agent.py        # Routes intent → use case
│   ├── orchestration/
│   │   ├── orchestrator.py    # Coordinates the full pipeline
│   │   └── failure_handler.py # Retry + backoff + dead letter
│   ├── context/
│   │   └── prompt_builder.py  # Builds LLM messages per use case
│   ├── validators/
│   │   └── validator_chain.py # Completeness · Traceability · Length
│   └── response/
│       ├── response_builder.py    # Builds typed DTO from validated artefact
│       ├── confidence_aggregator.py # Weighted score per artefact type
│       ├── channel_formatter.py    # Markdown · JSON · CSV · Robot
│       └── schemas/               # Typed output DTOs
│           ├── requirement_response.py
│           ├── design_tests_response.py
│           ├── rtm_response.py
│           └── test_case_response.py
│
├── infrastructure/            # Frameworks & Drivers (outermost layer)
│   ├── api/                   # FastAPI — entry point
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── qa_routes.py
│   │   │   └── system_routes.py
│   │   ├── schemas/
│   │   │   ├── api_schemas.py
│   │   │   └── converters.py
│   │   └── middleware/
│   │       └── auth.py
│   ├── llm/
│   │   └── b3gpt_provider.py  # Implements LLMPort for B3GPT endpoint
│   ├── rag/
│   │   └── rag_service.py     # Orchestrates retrieval + ingestion
│   └── vectorstores/
│       ├── chroma_store.py
│       ├── faiss_store.py
│       └── qdrant_store.py
│
├── container/
│   └── container.py           # DI Container (cached_property singletons)
├── config/
│   └── settings.py            # Pydantic settings from .env
├── observability/
│   └── logger.py              # Structured JSON logger
│
└── qa_copilot.py              # Public facade — Robot Framework compatible

frontend/
└── app.py                     # Streamlit UI (5 tabs, connects to API)
```

---

## Pipeline

```
Caller (Robot Framework / API / CLI / Streamlit)
  → QACopilot facade
    → Container (DI, builds all dependencies once)
      → Orchestrator
        → QAAgent  →  Use Case  →  LLMPort  →  B3GPTProvider
        ← artefact
      → ValidatorChain  (Completeness · Traceability · Length)
      → ResponseBuilder → typed DTO (per artefact type)
      → ChannelFormatter → Markdown | JSON | CSV | Robot string
      → OrchestratorResult
```

**Failure path:** if the validator rejects, `FailureHandler` retries with exponential backoff. Failed attempts are recorded in `dead_letter` for audit.

---

## Quick Start

### 1. Configuration

```bash
cp .env.example .env
# Fill in B3GPT_TOKEN and B3GPT_MODEL_NAME
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the API

```bash
uvicorn app.infrastructure.api.main:create_app --factory --reload --port 8000
```

Swagger UI available at `http://localhost:8000/docs`.

### 4. Run the frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

### 5. Use as Robot Framework library

```robotframework
Library    app.qa_copilot.QACopilot
...        token=%{B3GPT_TOKEN}
...        model_name=%{B3GPT_MODEL_NAME}

*** Test Cases ***
Analyze User Story
    ${markdown}=    Gerar Analise User Story
    ...    nome=Login MFA
    ...    descricao=As an authenticated user, I want to log in with MFA
    ...    rns=RN-01: TOTP support required. RN-02: Token expires in 30s.
    ...    cas=CA-01: Valid token authenticates. CA-02: Invalid token shows error.
    Should Contain    ${markdown}    Análise de Negócio
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check — LLM + RAG status |
| POST | `/api/v1/qa/analyze` | Full User Story analysis (8 sections + recommendations) |
| POST | `/api/v1/qa/design-tests` | Detailed test cases with steps and automation hints |
| POST | `/api/v1/qa/generate-rtm` | Bidirectional RTM (RN → CA → CT) + test scenario table |
| POST | `/api/v1/qa/create-user-story` | New US from scratch (Part A: US + Part B: full analysis) |
| POST | `/rag/ingest` | Index a document in the knowledge base |
| POST | `/rag/ingest-batch` | Index multiple documents |

### Request body example (`/api/v1/qa/analyze`):

```json
{
  "user_story": {
    "nome": "Login with MFA",
    "descricao": "As an authenticated user, I want to log in with MFA",
    "rns": "RN-01: TOTP support. RN-02: Token expires in 30s.",
    "cas": "CA-01: Valid token authenticates. CA-02: Invalid shows error."
  },
  "include_gherkin": false,
  "temperature": 0.2,
  "channel": "json"
}
```

---

## Enabling RAG

RAG is disabled by default. To enable:

```env
RAG_ENABLED=true
VECTOR_STORE_TYPE=chroma   # chroma | faiss | qdrant
VECTOR_STORE_PATH=./data/vectorstore
```

Install the chosen vector store:

```bash
pip install chromadb                       # for Chroma
pip install faiss-cpu sentence-transformers  # for FAISS
pip install qdrant-client sentence-transformers  # for Qdrant
```

Index documents via API (`POST /rag/ingest`) or directly:

```python
copilot.indexar_documento(
    conteudo="ISO 29119 — Software Testing Standard...",
    fonte="standard/iso-29119",
    tipo="standard",
)
```

---

## Response structure

Every endpoint returns a typed DTO with full auditability:

```json
{
  "success": true,
  "tipo": "analise_us",
  "confidence_score": 0.872,
  "completo": true,
  "secoes_presentes": ["Análise de Negócio", "..."],
  "secoes_ausentes": [],
  "validacoes": [
    {"validator": "completeness", "passed": true, "score": 1.0, "message": "..."},
    {"validator": "traceability", "passed": true, "score": 1.0, "message": "..."},
    {"validator": "content_length", "passed": true, "score": 1.0, "message": "..."}
  ],
  "modelo_usado": "gpt-4o",
  "tokens_consumidos": 1842,
  "latencia_ms": 4312.1,
  "request_id": "a3f1b2c4-...",
  "timestamp": "2026-06-17T11:00:00Z",
  "conteudo_markdown": "## Análise de Negócio\n..."
}
```

---

## Project structure decisions

| Decision | Reason |
|----------|--------|
| `Requirement` entity (not `UserStory`) | Domain models requirements broadly — US is one format |
| `VectorStorePort` separate from `KnowledgePort` | Different concerns: storage vs retrieval strategy |
| `infrastructure/api/` inside infrastructure | FastAPI is a framework driver — outermost layer |
| `ConfidenceAggregator` separate from validators | Aggregation is a different responsibility than pass/fail |
| `ChannelFormatter` in adapters | Knows external formats (JSON/CSV/Markdown) — not domain |
| `FailureHandler` with dead letter | Every failure is auditable — not silently swallowed |

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `B3GPT_TOKEN` | ✅ | — | B3GPT API key |
| `B3GPT_MODEL_NAME` | ✅ | — | Deployment/model name |
| `B3GPT_BASE_URL` | | B3 default URL | Override for other OpenAI-compatible endpoints |
| `B3GPT_TIMEOUT` | | `60` | HTTP timeout in seconds |
| `API_KEY` | | `""` | X-API-Key header auth. Empty = no auth |
| `RAG_ENABLED` | | `false` | Enable RAG pipeline |
| `VECTOR_STORE_TYPE` | | `chroma` | `chroma` · `faiss` · `qdrant` |
| `VECTOR_STORE_PATH` | | `./data/vectorstore` | Local persistence path |
| `LOG_LEVEL` | | `INFO` | `DEBUG` · `INFO` · `WARNING` · `ERROR` |
| `APP_ENV` | | `development` | `development` · `staging` · `production` |
| `MAX_RETRIES` | | `2` | LLM retry attempts on failure |
