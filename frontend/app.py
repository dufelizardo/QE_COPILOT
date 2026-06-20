"""
QE Copilot — Frontend Streamlit
Conecta diretamente à API FastAPI via HTTP.

Rodar:
    streamlit run frontend/app.py

Variáveis de ambiente (ou .env na raiz):
    QE_API_URL   = http://localhost:8000   (padrão)
    QE_API_KEY   = sua-api-key             (opcional)
"""
from __future__ import annotations

import os
import json
import time
from typing import Any

import requests
import streamlit as st

# ── Configuração ────────────────────────────────────────────────────────────

API_URL = os.getenv("QE_API_URL", "http://localhost:8000")
API_KEY = os.getenv("QE_API_KEY", "")

st.set_page_config(
    page_title="QE Copilot",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Fonte e base */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f1117;
    border-right: 1px solid #1e2130;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: #8b949e !important; font-size: 12px; }

/* Header badge */
.qe-badge {
    display: inline-block;
    background: #1a3a5c;
    color: #58a6ff;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

/* Metric cards */
.metric-row {
    display: flex;
    gap: 12px;
    margin: 16px 0;
}
.metric-card {
    flex: 1;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 14px 16px;
}
.metric-card .label {
    font-size: 11px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.metric-card .value {
    font-size: 22px;
    font-weight: 600;
    color: #e6edf3;
}
.metric-card .value.green { color: #3fb950; }
.metric-card .value.yellow { color: #d29922; }
.metric-card .value.red { color: #f85149; }
.metric-card .value.blue { color: #58a6ff; }
.metric-card .sub {
    font-size: 11px;
    color: #6e7681;
    margin-top: 2px;
}

/* Score bar */
.score-bar-bg {
    background: #21262d;
    border-radius: 4px;
    height: 6px;
    margin-top: 6px;
}
.score-bar-fill {
    height: 6px;
    border-radius: 4px;
    transition: width 0.4s ease;
}

/* Validator pills */
.pill {
    display: inline-block;
    font-size: 11px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 20px;
    margin: 2px;
}
.pill-ok { background: #0d4429; color: #3fb950; }
.pill-fail { background: #4d1414; color: #f85149; }

/* Section tag */
.section-tag {
    display: inline-block;
    background: #0d2137;
    color: #58a6ff;
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 4px;
    margin: 2px;
    font-family: 'JetBrains Mono', monospace;
}

/* Output area */
.output-box {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 20px 24px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    line-height: 1.7;
    color: #c9d1d9;
    max-height: 600px;
    overflow-y: auto;
}

/* Status strip */
.status-strip {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 13px;
    margin-bottom: 16px;
}
.status-ok { background: #0d2119; border: 1px solid #1a4731; color: #3fb950; }
.status-err { background: #2d0f0f; border: 1px solid #4d1414; color: #f85149; }
.status-warn { background: #2a1f00; border: 1px solid #4a3800; color: #d29922; }

/* Divider */
.qdiv { border: none; border-top: 1px solid #21262d; margin: 20px 0; }

/* Tab custom */
button[data-baseweb="tab"] {
    font-size: 13px !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)


# ── HTTP Client ─────────────────────────────────────────────────────────────

def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def api_post(endpoint: str, payload: dict) -> tuple[dict | None, str | None, float]:
    """Chama a API e retorna (data, error, latencia_ms)."""
    url = f"{API_URL}{endpoint}"
    start = time.monotonic()
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=120)
        latencia = (time.monotonic() - start) * 1000
        if resp.status_code == 200:
            return resp.json(), None, latencia
        return None, f"HTTP {resp.status_code}: {resp.text[:300]}", latencia
    except requests.Timeout:
        return None, "Timeout — o modelo demorou mais de 120s.", (time.monotonic() - start) * 1000
    except requests.ConnectionError:
        return None, f"Não foi possível conectar em {API_URL}. A API está rodando?", 0.0
    except Exception as e:
        return None, str(e), 0.0


def api_get(endpoint: str) -> tuple[dict | None, str | None]:
    try:
        resp = requests.get(f"{API_URL}{endpoint}", headers=_headers(), timeout=10)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"HTTP {resp.status_code}"
    except Exception as e:
        return None, str(e)


# ── Componentes reutilizáveis ───────────────────────────────────────────────

def render_metrics(data: dict) -> None:
    score = data.get("confidence_score", 0)
    color = "green" if score >= 0.8 else "yellow" if score >= 0.6 else "red"
    tokens = data.get("tokens_consumidos") or 0
    latencia = data.get("latencia_ms") or 0
    modelo = data.get("modelo_usado") or "—"

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="label">Confidence Score</div>
            <div class="value {color}">{score:.0%}</div>
            <div class="score-bar-bg">
                <div class="score-bar-fill" style="width:{score*100:.0f}%;background:{'#3fb950' if color=='green' else '#d29922' if color=='yellow' else '#f85149'}"></div>
            </div>
        </div>
        <div class="metric-card">
            <div class="label">Tokens</div>
            <div class="value blue">{tokens:,}</div>
            <div class="sub">consumidos</div>
        </div>
        <div class="metric-card">
            <div class="label">Latência</div>
            <div class="value">{latencia/1000:.1f}s</div>
            <div class="sub">tempo de resposta</div>
        </div>
        <div class="metric-card">
            <div class="label">Modelo</div>
            <div class="value" style="font-size:14px;padding-top:4px">{modelo}</div>
            <div class="sub">request: {(data.get('request_id') or '')[:8]}...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_validators(validacoes: list) -> None:
    if not validacoes:
        return
    pills = ""
    for v in validacoes:
        cls = "pill-ok" if v["passed"] else "pill-fail"
        icon = "✓" if v["passed"] else "✗"
        label = v["validator"].replace("_", " ")
        score_str = f" {v['score']:.0%}"
        pills += f'<span class="pill {cls}">{icon} {label}{score_str}</span>'
    st.markdown(f"<div style='margin:8px 0'>{pills}</div>", unsafe_allow_html=True)
    with st.expander("Detalhe das validações", expanded=False):
        for v in validacoes:
            icon = "✅" if v["passed"] else "❌"
            st.markdown(f"{icon} **{v['validator']}** — score `{v['score']:.3f}` — {v['message']}")


def render_output(data: dict) -> None:
    """Renderiza o conteúdo Markdown e os metadados de auditoria."""
    if not data.get("success"):
        st.markdown(f'<div class="status-strip status-err">❌ {data.get("error_message", "Erro desconhecido")}</div>', unsafe_allow_html=True)
        return

    render_metrics(data)
    render_validators(data.get("validacoes", []))

    st.markdown('<hr class="qdiv">', unsafe_allow_html=True)

    tab_md, tab_json, tab_audit = st.tabs(["📄 Resultado", "{ } JSON", "🔍 Auditoria"])

    with tab_md:
        md = data.get("conteudo_markdown", "")
        st.markdown(md)
        st.download_button(
            "⬇ Baixar Markdown",
            data=md,
            file_name=f"qe_copilot_{data.get('tipo','output')}.md",
            mime="text/markdown",
        )

    with tab_json:
        st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
        st.download_button(
            "⬇ Baixar JSON",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name=f"qe_copilot_{data.get('tipo','output')}.json",
            mime="application/json",
        )

    with tab_audit:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Pipeline**")
            st.markdown(f"- Tipo: `{data.get('tipo')}`")
            st.markdown(f"- Request ID: `{data.get('request_id')}`")
            st.markdown(f"- Timestamp: `{data.get('timestamp')}`")
            st.markdown(f"- Completo: `{data.get('completo', '—')}`")

        with col2:
            st.markdown("**Rastreabilidade**")
            if "secoes_presentes" in data:
                for s in data["secoes_presentes"]:
                    st.markdown(f'<span class="section-tag">✓ {s}</span>', unsafe_allow_html=True)
            if "rns_cobertas" in data and data["rns_cobertas"]:
                st.markdown(f"- RNs: `{', '.join(data['rns_cobertas'])}`")
            if "cas_cobertos" in data and data["cas_cobertos"]:
                st.markdown(f"- CAs: `{', '.join(data['cas_cobertos'])}`")
            if "total_tcs" in data and data["total_tcs"]:
                st.markdown(f"- Total TCs: `{data['total_tcs']}`")
            if "total_casos" in data and data["total_casos"]:
                st.markdown(f"- Casos gerados: `{data['total_casos']}` (✓ {data.get('casos_positivos',0)} pos / ✗ {data.get('casos_negativos',0)} neg)")


def us_form_fields(key_prefix: str) -> tuple[str, str, str, str]:
    """Campos comuns de User Story. Retorna (nome, descricao, rns, cas)."""
    nome = st.text_input("Nome da User Story *", placeholder="Ex: Login com autenticação multifator", key=f"{key_prefix}_nome")
    descricao = st.text_area("Descrição *", placeholder="Como usuário autenticado, quero...", height=80, key=f"{key_prefix}_desc")
    col1, col2 = st.columns(2)
    with col1:
        rns = st.text_area("Regras de Negócio (RN) *", placeholder="RN-01: O sistema deve suportar TOTP.\nRN-02: Token expira em 30 segundos.", height=120, key=f"{key_prefix}_rns")
    with col2:
        cas = st.text_area("Critérios de Aceite (CA) *", placeholder="CA-01: Token válido autentica o usuário.\nCA-02: Token inválido exibe mensagem de erro.", height=120, key=f"{key_prefix}_cas")
    return nome, descricao, rns, cas


def validate_us_fields(nome, descricao, rns, cas) -> bool:
    if not all([nome.strip(), descricao.strip(), rns.strip(), cas.strip()]):
        st.warning("Preencha todos os campos obrigatórios (*) antes de continuar.")
        return False
    return True


# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="qe-badge">QE COPILOT</div>', unsafe_allow_html=True)
    st.markdown("### Quality Engineering")
    st.markdown("Análise de User Stories com IA")
    st.markdown('<hr class="qdiv">', unsafe_allow_html=True)

    st.markdown("**Conexão**")
    api_url_input = st.text_input("API URL", value=API_URL, key="api_url")
    api_key_input = st.text_input("API Key", value=API_KEY, type="password", key="api_key_input")

    if st.button("🔌 Verificar conexão", use_container_width=True):
        data, err = api_get("/health")
        if data:
            llm_status = "✅ Online" if data.get("llm_ok") else "⚠️ Degradado"
            rag_status = "✅ Ativo" if data.get("rag_enabled") else "○ Desabilitado"
            st.success(f"API conectada v{data.get('version','?')}")
            st.markdown(f"- LLM: {llm_status}")
            st.markdown(f"- RAG: {rag_status}")
        else:
            st.error(f"Sem conexão: {err}")

    st.markdown('<hr class="qdiv">', unsafe_allow_html=True)
    st.markdown("**Parâmetros avançados**")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05, key="temperature_global")
    include_gherkin = st.toggle("Incluir Gherkin", value=False, key="gherkin_global")
    include_automation = st.toggle("Sugestões de automação", value=True, key="automation_global")

    st.markdown('<hr class="qdiv">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#6e7681">Powered by B3GPT · Clean Architecture</div>', unsafe_allow_html=True)

# Atualizar globais com valores da sidebar
API_URL = api_url_input
API_KEY = api_key_input

# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:8px">
    <span style="font-size:32px">🧪</span>
    <div>
        <div style="font-size:24px;font-weight:600;color:#e6edf3;line-height:1.2">QE Copilot</div>
        <div style="font-size:13px;color:#8b949e">Quality Engineering Assistant · Análise de User Stories com IA</div>
    </div>
</div>
<hr class="qdiv">
""", unsafe_allow_html=True)

# ── Abas principais ──────────────────────────────────────────────────────────

tab_analyze, tab_design, tab_rtm, tab_create, tab_rag = st.tabs([
    "📋 Analisar US",
    "🧩 Design de Testes",
    "📊 Gerar RTM",
    "✨ Nova User Story",
    "📚 Base de Conhecimento",
])

# ─────────────────────────────────────────────────────────────────────────────
# ABA 1 — Analisar User Story
# ─────────────────────────────────────────────────────────────────────────────

with tab_analyze:
    st.markdown("#### Análise completa de User Story")
    st.markdown('<div style="font-size:13px;color:#8b949e;margin-bottom:16px">Gera análise de negócio, requisitos, testabilidade, riscos, dependências, rastreabilidade e recomendações para sprint.</div>', unsafe_allow_html=True)

    with st.form("form_analyze"):
        nome, descricao, rns, cas = us_form_fields("analyze")

        submitted = st.form_submit_button("🔍 Analisar User Story", use_container_width=True, type="primary")

    if submitted:
        if validate_us_fields(nome, descricao, rns, cas):
            with st.spinner("Analisando User Story..."):
                data, err, lat = api_post("/api/v1/qa/analyze", {
                    "user_story": {"nome": nome, "descricao": descricao, "rns": rns, "cas": cas},
                    "include_gherkin": include_gherkin,
                    "temperature": temperature,
                    "channel": "json",
                })
            if err:
                st.markdown(f'<div class="status-strip status-err">❌ {err}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-strip status-ok">✓ Análise concluída em {lat/1000:.1f}s</div>', unsafe_allow_html=True)
                render_output(data)

# ─────────────────────────────────────────────────────────────────────────────
# ABA 2 — Design de Testes
# ─────────────────────────────────────────────────────────────────────────────

with tab_design:
    st.markdown("#### Design detalhado de casos de teste")
    st.markdown('<div style="font-size:13px;color:#8b949e;margin-bottom:16px">Gera casos de teste com passos numerados, pré-condições, dados de teste, resultado esperado e sugestões de automação.</div>', unsafe_allow_html=True)

    with st.form("form_design"):
        nome_d, descricao_d, rns_d, cas_d = us_form_fields("design")

        submitted_d = st.form_submit_button("🧩 Gerar Casos de Teste", use_container_width=True, type="primary")

    if submitted_d:
        if validate_us_fields(nome_d, descricao_d, rns_d, cas_d):
            with st.spinner("Projetando casos de teste..."):
                data_d, err_d, lat_d = api_post("/api/v1/qa/design-tests", {
                    "user_story": {"nome": nome_d, "descricao": descricao_d, "rns": rns_d, "cas": cas_d},
                    "include_automation_hints": include_automation,
                    "temperature": temperature,
                    "channel": "json",
                })
            if err_d:
                st.markdown(f'<div class="status-strip status-err">❌ {err_d}</div>', unsafe_allow_html=True)
            else:
                # Sumário específico de design tests
                total = data_d.get("total_casos")
                pos = data_d.get("casos_positivos", 0)
                neg = data_d.get("casos_negativos", 0)
                if total:
                    st.markdown(f'<div class="status-strip status-ok">✓ {total} casos gerados — {pos} positivos · {neg} negativos · em {lat_d/1000:.1f}s</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="status-strip status-ok">✓ Concluído em {lat_d/1000:.1f}s</div>', unsafe_allow_html=True)
                render_output(data_d)

# ─────────────────────────────────────────────────────────────────────────────
# ABA 3 — RTM Bidirecional
# ─────────────────────────────────────────────────────────────────────────────

with tab_rtm:
    st.markdown("#### RTM Bidirecional · RN → CA → CT")
    st.markdown('<div style="font-size:13px;color:#8b949e;margin-bottom:16px">Gera Tabela de Cenários de Teste e Matriz de Rastreabilidade bidirecional com cobertura completa.</div>', unsafe_allow_html=True)

    with st.form("form_rtm"):
        nome_r, descricao_r, rns_r, cas_r = us_form_fields("rtm")

        submitted_r = st.form_submit_button("📊 Gerar RTM", use_container_width=True, type="primary")

    if submitted_r:
        if validate_us_fields(nome_r, descricao_r, rns_r, cas_r):
            with st.spinner("Gerando RTM bidirecional..."):
                data_r, err_r, lat_r = api_post("/api/v1/qa/generate-rtm", {
                    "user_story": {"nome": nome_r, "descricao": descricao_r, "rns": rns_r, "cas": cas_r},
                    "temperature": temperature,
                    "channel": "json",
                })
            if err_r:
                st.markdown(f'<div class="status-strip status-err">❌ {err_r}</div>', unsafe_allow_html=True)
            else:
                tcs = data_r.get("total_tcs")
                rns_cob = data_r.get("rns_cobertas", [])
                cas_cob = data_r.get("cas_cobertos", [])
                msg_parts = []
                if tcs:
                    msg_parts.append(f"{tcs} casos")
                if rns_cob:
                    msg_parts.append(f"{len(rns_cob)} RNs")
                if cas_cob:
                    msg_parts.append(f"{len(cas_cob)} CAs")
                summary = " · ".join(msg_parts) if msg_parts else "Concluído"
                st.markdown(f'<div class="status-strip status-ok">✓ {summary} em {lat_r/1000:.1f}s</div>', unsafe_allow_html=True)
                render_output(data_r)

# ─────────────────────────────────────────────────────────────────────────────
# ABA 4 — Nova User Story
# ─────────────────────────────────────────────────────────────────────────────

with tab_create:
    st.markdown("#### Criar nova User Story + análise completa")
    st.markdown('<div style="font-size:13px;color:#8b949e;margin-bottom:16px">Gera uma nova User Story do zero (Parte A: Como/Quero/Para + RN + CA) e análise completa (Parte B: seções 1–9 + Recomendações).</div>', unsafe_allow_html=True)

    with st.form("form_create"):
        col_a, col_b = st.columns(2)
        with col_a:
            feature_titulo = st.text_input("Feature / Título *", placeholder="Ex: Recuperação de senha via e-mail", key="create_titulo")
            persona = st.text_input("Persona (Como) *", placeholder="usuário com acesso bloqueado", key="create_persona")
            objetivo = st.text_input("Objetivo (Quero) *", placeholder="redefinir minha senha pelo e-mail cadastrado", key="create_objetivo")
            beneficio = st.text_input("Benefício (Para) *", placeholder="recuperar acesso sem contato com suporte", key="create_beneficio")

        with col_b:
            contexto = st.text_area("Contexto", placeholder="Informações adicionais sobre o contexto...", height=80, key="create_contexto")
            restricoes = st.text_area("Restrições / Políticas", placeholder="Ex: LGPD, limite de tentativas...", height=80, key="create_restricoes")
            nfr = st.text_area("Requisitos Não Funcionais", placeholder="Performance, segurança, acessibilidade...", height=80, key="create_nfr")

        with st.expander("Campos opcionais — integrações, riscos, dependências"):
            col_c, col_d = st.columns(2)
            with col_c:
                integracoes = st.text_area("Integrações", placeholder="APIs, serviços externos...", height=70, key="create_integracoes")
                dependencias = st.text_area("Dependências", placeholder="Outros times, features...", height=70, key="create_deps")
                dados_exemplo = st.text_area("Dados / Edge Cases", placeholder="Exemplos de dados, casos extremos...", height=70, key="create_dados")
            with col_d:
                riscos = st.text_area("Riscos conhecidos", placeholder="Riscos técnicos ou de negócio...", height=70, key="create_riscos")
                perguntas = st.text_area("Perguntas em aberto", placeholder="Dúvidas para o PO...", height=70, key="create_perguntas")
                rns_existentes = st.text_area("RNs existentes (se houver)", placeholder="RN-01: ...", height=70, key="create_rns")
            cas_existentes = st.text_area("CAs existentes (se houver)", placeholder="CA-01: ...", height=70, key="create_cas")

        submitted_c = st.form_submit_button("✨ Criar User Story + Análise", use_container_width=True, type="primary")

    if submitted_c:
        if not all([feature_titulo.strip(), persona.strip(), objetivo.strip(), beneficio.strip()]):
            st.warning("Preencha Feature, Persona, Objetivo e Benefício antes de continuar.")
        else:
            with st.spinner("Criando User Story e gerando análise completa..."):
                data_c, err_c, lat_c = api_post("/api/v1/qa/create-user-story", {
                    "feature_titulo": feature_titulo,
                    "persona": persona,
                    "objetivo_usuario": objetivo,
                    "beneficio": beneficio,
                    "contexto": contexto,
                    "regras_negocio": rns_existentes if 'rns_existentes' in dir() else "",
                    "criterios_aceite": cas_existentes if 'cas_existentes' in dir() else "",
                    "restricoes": restricoes,
                    "nfr": nfr,
                    "integracoes": integracoes if 'integracoes' in dir() else "",
                    "dados_exemplo": dados_exemplo if 'dados_exemplo' in dir() else "",
                    "dependencias": dependencias if 'dependencias' in dir() else "",
                    "riscos": riscos if 'riscos' in dir() else "",
                    "perguntas_abertas": perguntas if 'perguntas' in dir() else "",
                    "include_gherkin": include_gherkin,
                    "temperature": temperature,
                    "channel": "json",
                })
            if err_c:
                st.markdown(f'<div class="status-strip status-err">❌ {err_c}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-strip status-ok">✓ User Story criada em {lat_c/1000:.1f}s</div>', unsafe_allow_html=True)

                # Mostrar Parte A e Parte B em abas separadas
                parte_a = data_c.get("parte_a_user_story", "")
                parte_b = data_c.get("parte_b_analise", "")

                if parte_a or parte_b:
                    render_metrics(data_c)
                    render_validators(data_c.get("validacoes", []))
                    st.markdown('<hr class="qdiv">', unsafe_allow_html=True)
                    tab_a, tab_b, tab_full, tab_json_c = st.tabs(["📝 Parte A — User Story", "📋 Parte B — Análise", "📄 Completo", "{ } JSON"])
                    with tab_a:
                        st.markdown(parte_a or data_c.get("conteudo_markdown", ""))
                    with tab_b:
                        st.markdown(parte_b or "*(análise integrada no conteúdo completo)*")
                    with tab_full:
                        st.markdown(data_c.get("conteudo_markdown", ""))
                        st.download_button("⬇ Baixar Markdown", data=data_c.get("conteudo_markdown",""),
                            file_name=f"us_{feature_titulo[:30].replace(' ','_')}.md", mime="text/markdown")
                    with tab_json_c:
                        st.code(json.dumps(data_c, ensure_ascii=False, indent=2), language="json")
                else:
                    render_output(data_c)

# ─────────────────────────────────────────────────────────────────────────────
# ABA 5 — Base de Conhecimento (RAG)
# ─────────────────────────────────────────────────────────────────────────────

with tab_rag:
    st.markdown("#### Base de Conhecimento")
    st.markdown('<div style="font-size:13px;color:#8b949e;margin-bottom:16px">Indexe documentos de referência (padrões QA, RTMs anteriores, US existentes) para enriquecer as análises com contexto da sua organização.</div>', unsafe_allow_html=True)

    data_h, _ = api_get("/health")
    rag_ok = data_h and data_h.get("rag_enabled")

    if not rag_ok:
        st.markdown('<div class="status-strip status-warn">⚠️ RAG desabilitado. Configure <code>RAG_ENABLED=true</code> no .env e reinicie a API.</div>', unsafe_allow_html=True)

    with st.form("form_rag"):
        col_rag1, col_rag2 = st.columns([3, 1])
        with col_rag1:
            fonte = st.text_input("Fonte / Identificador", placeholder="Ex: standard/iso-29119, us/login-mfa", key="rag_fonte")
        with col_rag2:
            tipo_doc = st.selectbox("Tipo", ["documento", "user_story", "standard", "rtm"], key="rag_tipo")

        conteudo_rag = st.text_area(
            "Conteúdo do documento",
            placeholder="Cole aqui o conteúdo a indexar — padrões QA, critérios de aceite de referência, RTMs anteriores...",
            height=200,
            key="rag_conteudo",
        )

        submitted_rag = st.form_submit_button(
            "📥 Indexar documento" if rag_ok else "📥 Indexar (RAG desabilitado)",
            use_container_width=True,
            disabled=not rag_ok,
        )

    if submitted_rag and rag_ok:
        if not fonte.strip() or not conteudo_rag.strip():
            st.warning("Preencha a fonte e o conteúdo antes de indexar.")
        else:
            with st.spinner("Indexando documento..."):
                data_rag, err_rag, _ = api_post("/rag/ingest", {
                    "conteudo": conteudo_rag,
                    "fonte": fonte,
                    "tipo": tipo_doc,
                })
            if err_rag:
                st.markdown(f'<div class="status-strip status-err">❌ {err_rag}</div>', unsafe_allow_html=True)
            elif data_rag and data_rag.get("success"):
                st.markdown(f'<div class="status-strip status-ok">✓ {data_rag.get("message", "Indexado com sucesso.")}</div>', unsafe_allow_html=True)
            else:
                msg = data_rag.get("message","") if data_rag else "Falha"
                st.markdown(f'<div class="status-strip status-err">❌ {msg}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="qdiv">', unsafe_allow_html=True)
    st.markdown("**Indexação em lote**")
    st.markdown('<div style="font-size:13px;color:#8b949e;margin-bottom:12px">Cole um JSON com lista de documentos para indexar vários de uma vez.</div>', unsafe_allow_html=True)

    batch_json = st.text_area(
        "JSON de documentos",
        placeholder='[{"conteudo": "...", "fonte": "standard/iso-1", "tipo": "standard"}, ...]',
        height=120,
        key="rag_batch",
    )
    if st.button("📥 Indexar lote", disabled=not rag_ok, key="rag_batch_btn"):
        if batch_json.strip():
            try:
                docs = json.loads(batch_json)
                if not isinstance(docs, list):
                    st.error("O JSON deve ser uma lista de documentos.")
                else:
                    with st.spinner(f"Indexando {len(docs)} documentos..."):
                        data_b, err_b, _ = api_post("/rag/ingest-batch", {"documentos": docs})
                    if err_b:
                        st.error(err_b)
                    else:
                        st.success(f"{data_b.get('indexed',0)} documentos indexados.")
            except json.JSONDecodeError as e:
                st.error(f"JSON inválido: {e}")
