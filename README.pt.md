# QE Copilot

**Quality Engineering Copilot** — assistente com IA para análise de User Stories, design de casos de teste, geração de RTM bidirecional e criação de novas User Stories do zero. Construído sobre Clean Architecture com o provider B3GPT, camada REST FastAPI, frontend Streamlit e base de conhecimento RAG opcional.

---

## Arquitetura

O projeto segue **Clean Architecture** de forma estrita. As dependências sempre apontam para dentro — o domínio nunca conhece a infraestrutura.

```
app/
├── domain/                    # Domínio puro — sem dependências externas
│   ├── entities/
│   │   ├── requirement.py     # Requirement (entidade de entrada, alias UserStory)
│   │   ├── test_case.py       # TestCase + enums
│   │   └── rtm.py             # RTMEntry + QAArtefact
│   ├── ports/                 # Abstrações (ABCs — interfaces)
│   │   ├── llm_port.py        # LLMPort → qualquer provider LLM
│   │   ├── knowledge_port.py  # RetrievalPort + IngestionPort → RAG
│   │   └── vector_store_port.py # VectorStorePort → Chroma/FAISS/Qdrant
│   └── use_cases/
│       ├── analyze_user_story.py
│       ├── design_tests.py
│       ├── generate_rtm.py
│       └── create_user_story.py
│
├── adapters/                  # Tradutores entre domínio e infraestrutura
│   ├── agents/
│   │   └── qa_agent.py        # Roteia intent → use case
│   ├── orchestration/
│   │   ├── orchestrator.py    # Coordena o pipeline completo
│   │   └── failure_handler.py # Retry + backoff + dead letter
│   ├── context/
│   │   └── prompt_builder.py  # Constrói mensagens LLM por use case
│   ├── validators/
│   │   └── validator_chain.py # Completude · Rastreabilidade · Tamanho
│   └── response/
│       ├── response_builder.py    # Monta DTO tipado do artefato validado
│       ├── confidence_aggregator.py # Score ponderado por tipo de artefato
│       ├── channel_formatter.py    # Markdown · JSON · CSV · Robot
│       └── schemas/               # DTOs tipados de saída
│           ├── requirement_response.py
│           ├── design_tests_response.py
│           ├── rtm_response.py
│           └── test_case_response.py
│
├── infrastructure/            # Frameworks & Drivers (camada mais externa)
│   ├── api/                   # FastAPI — ponto de entrada REST
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
│   │   └── b3gpt_provider.py  # Implementa LLMPort para o endpoint B3GPT
│   ├── rag/
│   │   └── rag_service.py     # Orquestra retrieval + ingestão
│   └── vectorstores/
│       ├── chroma_store.py
│       ├── faiss_store.py
│       └── qdrant_store.py
│
├── container/
│   └── container.py           # DI Container (singletons via cached_property)
├── config/
│   └── settings.py            # Configurações Pydantic via .env
├── observability/
│   └── logger.py              # Logger estruturado JSON
│
└── qa_copilot.py              # Facade pública — compatível com Robot Framework

frontend/
└── app.py                     # Interface Streamlit (5 abas, conecta à API)
```

---

## Pipeline completo

```
Caller (Robot Framework / API / CLI / Streamlit)
  → Facade QACopilot
    → Container (DI, monta todas as dependências uma vez)
      → Orchestrator
        → QAAgent  →  Use Case  →  LLMPort  →  B3GPTProvider
        ← artefato gerado
      → ValidatorChain  (Completude · Rastreabilidade · Tamanho)
      → ResponseBuilder → DTO tipado (por tipo de artefato)
      → ChannelFormatter → Markdown | JSON | CSV | string Robot
      → OrchestratorResult
```

**Caminho de falha:** se o validator rejeitar, o `FailureHandler` tenta novamente com backoff exponencial. Tentativas falhas são registradas no `dead_letter` para auditoria.

---

## Início rápido

### 1. Configuração

```bash
cp .env.example .env
# Preencha B3GPT_TOKEN e B3GPT_MODEL_NAME
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Subir a API

```bash
uvicorn app.infrastructure.api.main:create_app --factory --reload --port 8000
```

Swagger disponível em `http://localhost:8000/docs`.

### 4. Subir o frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

### 5. Usar como biblioteca Robot Framework

```robotframework
Library    app.qa_copilot.QACopilot
...        token=%{B3GPT_TOKEN}
...        model_name=%{B3GPT_MODEL_NAME}

*** Test Cases ***
Analisar User Story
    ${markdown}=    Gerar Analise User Story
    ...    nome=Login com MFA
    ...    descricao=Como usuário autenticado, quero fazer login com MFA
    ...    rns=RN-01: suporte a TOTP. RN-02: Token expira em 30s.
    ...    cas=CA-01: Token válido autentica. CA-02: Inválido exibe erro.
    Should Contain    ${markdown}    Análise de Negócio
```

---

## Endpoints da API

| Método | Caminho | Descrição |
|--------|---------|-----------|
| GET | `/health` | Health check — status LLM + RAG |
| POST | `/api/v1/qa/analyze` | Análise completa de US (8 seções + recomendações) |
| POST | `/api/v1/qa/design-tests` | Casos de teste detalhados com passos e automação |
| POST | `/api/v1/qa/generate-rtm` | RTM bidirecional (RN → CA → CT) + tabela de cenários |
| POST | `/api/v1/qa/create-user-story` | Nova US do zero (Parte A: US + Parte B: análise completa) |
| POST | `/rag/ingest` | Indexa documento na base de conhecimento |
| POST | `/rag/ingest-batch` | Indexa múltiplos documentos |

### Exemplo de body (`/api/v1/qa/analyze`):

```json
{
  "user_story": {
    "nome": "Login com MFA",
    "descricao": "Como usuário autenticado, quero fazer login com MFA",
    "rns": "RN-01: suporte a TOTP. RN-02: Token expira em 30s.",
    "cas": "CA-01: Token válido autentica. CA-02: Inválido exibe erro."
  },
  "include_gherkin": false,
  "temperature": 0.2,
  "channel": "json"
}
```

---

## Habilitando o RAG

O RAG vem desabilitado por padrão. Para ativar:

```env
RAG_ENABLED=true
VECTOR_STORE_TYPE=chroma   # chroma | faiss | qdrant
VECTOR_STORE_PATH=./data/vectorstore
```

Instale o vector store escolhido:

```bash
pip install chromadb                              # Chroma
pip install faiss-cpu sentence-transformers       # FAISS
pip install qdrant-client sentence-transformers   # Qdrant
```

Indexe documentos via API (`POST /rag/ingest`) ou diretamente:

```python
copilot.indexar_documento(
    conteudo="ISO 29119 — Padrão de Testes de Software...",
    fonte="standard/iso-29119",
    tipo="standard",
)
```

---

## Estrutura da resposta

Todos os endpoints retornam um DTO tipado com rastreabilidade completa:

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

## Decisões de arquitetura

| Decisão | Motivo |
|---------|--------|
| Entidade `Requirement` (não `UserStory`) | O domínio modela requisitos amplamente — US é um formato específico |
| `VectorStorePort` separado de `KnowledgePort` | Responsabilidades distintas: armazenamento vs estratégia de retrieval |
| `infrastructure/api/` dentro de infrastructure | FastAPI é um Framework Driver — pertence à camada mais externa |
| `ConfidenceAggregator` separado dos validators | Agregar scores é responsabilidade diferente de decidir pass/fail |
| `ChannelFormatter` em adapters | Conhece formatos externos (JSON/CSV/Markdown) — não é domínio |
| `FailureHandler` com dead letter | Toda falha é auditável — não engolida silenciosamente |

---

## Variáveis de ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `B3GPT_TOKEN` | ✅ | — | API key do B3GPT |
| `B3GPT_MODEL_NAME` | ✅ | — | Nome do deployment/modelo |
| `B3GPT_BASE_URL` | | URL padrão B3 | Override para outros endpoints compatíveis com OpenAI |
| `B3GPT_TIMEOUT` | | `60` | Timeout HTTP em segundos |
| `API_KEY` | | `""` | Autenticação via header X-API-Key. Vazio = sem auth |
| `RAG_ENABLED` | | `false` | Habilita pipeline RAG |
| `VECTOR_STORE_TYPE` | | `chroma` | `chroma` · `faiss` · `qdrant` |
| `VECTOR_STORE_PATH` | | `./data/vectorstore` | Caminho de persistência local |
| `LOG_LEVEL` | | `INFO` | `DEBUG` · `INFO` · `WARNING` · `ERROR` |
| `APP_ENV` | | `development` | `development` · `staging` · `production` |
| `MAX_RETRIES` | | `2` | Tentativas de retry do LLM em caso de falha |
