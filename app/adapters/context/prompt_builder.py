from app.domain.entities.requirement import Requirement
from app.domain.ports.llm_port import LLMMessage
from app.domain.ports.knowledge_port import KnowledgeChunk


class PromptBuilder:
    """
    Constrói as mensagens (system + user) para cada caso de uso QA.
    Centraliza todos os prompts — nenhum use case ou agent conhece strings de prompt.

    Os prompts foram migrados do código legado (b3gpt_keywords.py) e organizados
    por responsabilidade. Modificar um prompt não afeta outros.
    """

    _SYSTEM_QA = LLMMessage(
        role="system",
        content=(
            "Você é especialista em QA, requisitos e análise de negócio. "
            "Responda em pt-BR e use Markdown organizado."
        ),
    )

    # ── Helpers ────────────────────────────────────────────────────────────

    def _format_context(self, chunks: list[KnowledgeChunk]) -> str:
        """Formata chunks do RAG como contexto adicional no prompt."""
        if not chunks:
            return ""
        parts = ["\n\n**Contexto relevante do repositório de conhecimento:**"]
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"\n[{i}] (fonte: {chunk.fonte})\n{chunk.conteudo}")
        return "\n".join(parts)

    def _gherkin_rule(self, include: bool) -> str:
        if include:
            return (
                "- Inclua **apenas Gherkin** se solicitado explicitamente.\n"
                "- 2–4 cenários no máximo.\n"
            )
        return "- **Não inclua Gherkin nesta resposta.**\n"

    # ── Builders públicos ──────────────────────────────────────────────────

    def build_analise_completa(
        self,
        requirement: Requirement,
        include_gherkin: bool = False,
        context_chunks: list[KnowledgeChunk] | None = None,
    ) -> list[LLMMessage]:
        """
        Prompt para AnalyzeUserStory use case.
        Migrado de _build_messages_analise_completa().
        """
        context = self._format_context(context_chunks or [])
        gherkin = self._gherkin_rule(include_gherkin)

        user_content = f"""
Você é especialista em QA, requisitos e análise de negócio. Responda em **pt-BR**, em **Markdown**, seguindo estritamente a estrutura abaixo. Seja objetivo, técnico e completo. Proponha [SUGESTÃO] quando faltar algo, sem inventar implementação.
{context}
**Insumos**
- Nome da User Story: {requirement.nome}
- Descrição: {requirement.descricao}
- Regras de Negócio (RN): {requirement.regras_negocio}
- Critérios de Aceite (CA): {requirement.criterios_aceite}

## 1️⃣ Análise de Negócio (Business Analysis)
- **O "por quê"**: 2–4 linhas (valor/propósito).
- **Valor de negócio**: bullets (3–5).
- **Alinhamento ao produto/sistema**: bullets (2–4).
- **Possíveis conflitos**: bullets (2–4).
- **Perguntas-chave (para Product/Negócio)**: lista enumerada (3–6).

## 2️⃣ Análise de Requisitos
- **Clareza do escopo**: 2–4 linhas.
- **Requisitos funcionais (refinados)**: RF-01… (5–12 itens, concisos).
- **Requisitos não funcionais (adicionados)**: RNF-01… (5–10 itens, concisos).
- **Campos/Fluxos/Exceções**: bullets (3–6).
- **Ambiguidades a remover**: bullets (3–5).

## 3️⃣ Análise de Critérios de Aceite
- **Clareza e mensurabilidade**: observações + sugestões (bullets).
- **Cobertura de fluxos**: breve resumo (feliz/alternativos/erro).

## 4️⃣ Análise de Testabilidade (QA)
- **É testável?** Sim/Não + justificativa breve.
- **Automação**: propostas (UI/API/A11y/Visual).
- **Massa de teste**: bullets.
- **Ambientes/Permissões**: bullets.
- **Perguntas de QA**: bullets.

## 5️⃣ Análise Técnica (Impacto)
- **Onde mexe**: FE/BE/Dados (bullets).
- **Integrações afetadas**: bullets.
- **Performance/Security**: bullets.
- **Recomendações técnicas**: bullets.

## 6️⃣ Análise de Riscos
- **Negócio**: bullets.
- **Técnico**: bullets.
- **Qualidade**: bullets.
- **Mitigações**: bullets.

## 7️⃣ Análise de Dependências
- Bullets (fontes de dados, design system, APIs, analytics, feature flags, permissões).

## 8️⃣ Análise de Rastreabilidade
- **Épico/Objetivo**: 1 linha.
- **Linkagem**: US ↔ RF/RNF ↔ CA-XX ↔ (Casos de Teste).
- **Qualidade**: como evidenciar cobertura (Xray/RTM).
- **Automação**: tags/suites.
- **Métricas**: bullets.

## Recomendações Finais (para deixar a US "pronta para sprint")
- **Backlog/Refino**: itens objetivos.
- **Definição de Pronto (DoR)**: checklist.
- **Definição de Pronto (DoD)**: checklist.

## (Opcional) Gherkin de exemplo (para CAs principais)
{gherkin}

**Regras de Formatação**
- Use títulos `##` e subtítulos `**negrito**` conforme a estrutura acima (não crie seções extras).
- Use linguagem objetiva. Marque suposições como **[SUGESTÃO]**.
- Mantenha rastreabilidade explícita a **RN** e **CA** quando fizer sentido.
- **Prioridade de conclusão:** finalize todas as seções até "Recomendações Finais"; Gherkin é opcional.
- **Devolva a resposta completa.**
""".strip()

        return [self._SYSTEM_QA, LLMMessage(role="user", content=user_content)]

    def build_rtm_e_cenarios(
        self,
        requirement: Requirement,
        context_chunks: list[KnowledgeChunk] | None = None,
    ) -> list[LLMMessage]:
        """
        Prompt para GenerateRTM use case.
        Migrado de gerar_rtm_e_cenarios_de_testes().
        """
        context = self._format_context(context_chunks or [])

        user_content = f"""
Você é especialista em QA e análise de User Stories. Responda em **pt-BR**, usando **Markdown** com seções e tabelas.
{context}
**Insumos**
- Nome da User Story: {requirement.nome}
- Descrição: {requirement.descricao}
- Regras de Negócio (RN): {requirement.regras_negocio}
- Critérios de Aceite (CA): {requirement.criterios_aceite}

**Tarefas (em ordem)**
1. Reescreva a User Story de forma clara, sem alterar o sentido.
2. Gere **Casos de Teste** numerados como **TC-001, TC-002, ...**
   - Agrupe por seções relevantes (Navegação, Layout, Cenários Negativos, etc.)
   - Cada caso: título + descrição de 1-2 linhas + Mapeamento: RN-XX, CA-XX
   - Ao final, checklist: total de casos, seções cobertas, RNs e CAs cobertas
3. **Tabela de Cenários de Teste** (Markdown):
   ID | Nome | Descrição | Relacionamento CA | Relacionamento RN | Tipo | Prioridade | Categoria | Classificação | Tipo de Execução
4. **Tabela RTM Bidirecional** (Markdown) — **NÃO omita**:
   CA-ID | Critério de Aceite | RN-ID | Regra de Negócio | Cenários Relacionados | Tipo | Prioridade | Classificação | Tipo de Execução | Ambiente | Categoria | Status

**Regras de Formatação**
- Use cabeçalhos (##, ###) para cada etapa.
- Proponha com [SUGESTÃO] o que estiver ausente.
- Mantenha rastreabilidade clara entre RN, CA e TC.
- Seja conciso, mas completo. Devolva a resposta completa.
""".strip()

        return [self._SYSTEM_QA, LLMMessage(role="user", content=user_content)]

    def build_us_nova_com_analise(
        self,
        requirement: Requirement,
        include_gherkin: bool = False,
        context_chunks: list[KnowledgeChunk] | None = None,
    ) -> list[LLMMessage]:
        """
        Prompt para CreateUserStory use case.
        Migrado de gerar_user_story_nova_com_analise().
        """
        context = self._format_context(context_chunks or [])
        gherkin = self._gherkin_rule(include_gherkin)

        user_content = f"""
Você vai EXECUTAR DUAS PARTES em uma única resposta, em **pt-BR** e **Markdown**:
- **Parte A — User Story (nova)**: gere a história do zero com a estrutura pedida.
- **Parte B — Análise completa**: gere as seções 1–9 + Recomendações (e Gherkin opcional).
{context}
**Insumos de alto nível**:
- Título/Feature: {requirement.feature_titulo}
- Persona (Como): {requirement.persona}
- Objetivo do usuário (Quero): {requirement.objetivo_usuario}
- Benefício (Para): {requirement.beneficio}
- Contexto: {requirement.contexto}
- Regras de Negócio (se já houver): {requirement.regras_negocio}
- Critérios de Aceite (se já houver): {requirement.criterios_aceite}
- Restrições/Políticas: {requirement.restricoes}
- Requisitos não funcionais (NFR): {requirement.nfr}
- Integrações: {requirement.integracoes}
- Dados de exemplo/edge cases: {requirement.dados_exemplo}
- Dependências: {requirement.dependencias}
- Riscos: {requirement.riscos}
- Perguntas em aberto: {requirement.perguntas_abertas}

---

## Parte A — User Story (Nova)

### Feature: {requirement.feature_titulo}
**Como:** <persona>
**Quero:** <objetivo>
**Para:** <benefício>

Crie: **Regras de Negócio** (RN-01, RN-02...) e **Critérios de Aceite** (CA-01, CA-02...).
Marque sugestões com **[SUGESTÃO]**.

---

## Parte B — Análise Completa

Siga exatamente: seções 1️⃣ Análise de Negócio, 2️⃣ Análise de Requisitos, 3️⃣ Análise de Critérios de Aceite, 4️⃣ Análise de Testabilidade (QA), 5️⃣ Análise Técnica (Impacto), 6️⃣ Análise de Riscos, 7️⃣ Análise de Dependências, 8️⃣ Análise de Rastreabilidade, 9️⃣ Flow (Happy Path + exceções), Recomendações Finais (DoR + DoD).

## (Opcional) Gherkin
{gherkin}

**Regras**: Use `##` para seções. Marque suposições como **[SUGESTÃO]**. Rastreabilidade explícita RN ↔ CA. Devolva a resposta completa.
""".strip()

        return [self._SYSTEM_QA, LLMMessage(role="user", content=user_content)]

    def build_design_tests(
        self,
        requirement: Requirement,
        include_automation_hints: bool = True,
        context_chunks: list[KnowledgeChunk] | None = None,
    ) -> list[LLMMessage]:
        """
        Prompt para DesignTests use case.
        Foco em casos de teste detalhados: passos numerados, dados, automação.
        Distinto do build_rtm_e_cenarios que gera a tabela bidirecional.
        """
        context = self._format_context(context_chunks or [])
        automation_block = (
            "\n- **Sugestão de Automação**: framework recomendado, tipo (UI/API/unitário), complexidade."
            if include_automation_hints else ""
        )

        user_content = f"""
Você é especialista em QA e design de casos de teste. Responda em **pt-BR**, usando **Markdown**.
{context}
**Insumos**
- Nome da User Story: {requirement.nome}
- Descrição: {requirement.descricao}
- Regras de Negócio (RN): {requirement.regras_negocio}
- Critérios de Aceite (CA): {requirement.criterios_aceite}

**Gere Casos de Teste detalhados**, numerados como **CT-01, CT-02, ...**, com o seguinte formato para cada um:

### CT-XX — Nome do Caso de Teste

- **Objetivo**: o que este teste valida
- **Pré-condições**: estado necessário antes de executar
- **Dados de teste**: valores, perfis, configurações necessárias (se aplicável)
- **Passos**:
  1. Passo numerado
  2. Passo numerado
  3. ...
- **Resultado esperado**: o que deve acontecer
- **Prioridade**: Alta / Média / Baixa
- **Severidade**: Crítica / Alta / Média / Baixa
- **Tipo**: Positivo / Negativo / Limite / Exploratorio
- **Categoria**: Smoke / Regressivo / Sanidade / Exploratório
- **Classificação**: Funcional / Não Funcional / Acessibilidade / Performance / Segurança
- **Tipo de Execução**: Pendente de Automação / Não Automatizável{automation_block}
- **Rastreabilidade**: RN(s) e CA(s) cobertos

**Inclua obrigatoriamente:**
- Casos do fluxo feliz (happy path)
- Casos de fluxo alternativo
- Casos negativos (dados inválidos, permissões, limites)
- Ao menos 1 caso de borda/limite
- Ao menos 1 caso de segurança ou não-funcional (se aplicável)

**Ao final**, inclua um **resumo**:
- Total de casos gerados
- Cobertura: RNs cobertas, CAs cobertos
- Sugestão de prioridade de execução (quais rodar primeiro)

**Regras de Formatação**
- Use `###` para cada caso de teste.
- Mantenha rastreabilidade explícita em cada caso.
- Se algum insumo estiver ausente, marque como **[SUGESTÃO]**.
- Seja objetivo e completo. Devolva a resposta completa.
""".strip()

        return [self._SYSTEM_QA, LLMMessage(role="user", content=user_content)]

    def build_continuacao(
        self,
        markdown_parcial: str,
        include_gherkin: bool = False,
    ) -> list[LLMMessage]:
        """
        Prompt de continuação — quando a resposta foi truncada.
        Migrado de _build_messages_continuacao().
        """
        ultimo_alvo = "## (Opcional) Gherkin" if include_gherkin else "## Recomendações Finais"
        system = LLMMessage(
            role="system",
            content="Você é especialista em QA. Continue em pt-BR, somente o Markdown faltante.",
        )
        user = LLMMessage(
            role="user",
            content=(
                "Abaixo está a resposta parcial. NÃO repita nada já escrito. "
                "Continue a partir da **primeira seção faltante** seguindo a mesma estrutura e ordem, "
                f"até concluir a seção '{ultimo_alvo}'. Resuma bullets se necessário, mas finalize todas as seções.\n\n"
                "--- RESPOSTA PARCIAL ---\n"
                f"{markdown_parcial}\n"
                "--- FIM ---"
            ),
        )
        return [system, user]
