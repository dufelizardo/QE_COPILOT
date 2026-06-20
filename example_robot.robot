*** Settings ***
Library    app.qa_copilot.QACopilot
...        token=%{B3GPT_TOKEN}
...        model_name=%{B3GPT_MODEL_NAME}

*** Variables ***
${US_NOME}          Login com autenticação multifator
${US_DESC}          Como usuário autenticado, quero fazer login com MFA para aumentar a segurança
${US_RNS}           RN-01: O sistema deve suportar TOTP. RN-02: O token expira em 30 segundos.
${US_CAS}           CA-01: Token válido autentica. CA-02: Token inválido exibe mensagem de erro.

*** Test Cases ***

Health Check
    ${ok}=    Health Check
    Should Be True    ${ok}    msg=Provider B3GPT inacessível

Análise de User Story
    ${md}=    Gerar Analise User Story
    ...    nome=${US_NOME}    descricao=${US_DESC}    rns=${US_RNS}    cas=${US_CAS}
    Should Contain    ${md}    Análise de Negócio
    Should Contain    ${md}    Recomendações Finais
    Log    ${md}    level=INFO

Design de Casos de Teste
    ${md}=    Gerar Design De Testes
    ...    nome=${US_NOME}    descricao=${US_DESC}    rns=${US_RNS}    cas=${US_CAS}
    Should Contain    ${md}    CT-01
    Log    ${md}    level=INFO

RTM Bidirecional
    ${md}=    Gerar Rtm E Cenarios De Testes
    ...    nome=${US_NOME}    descricao=${US_DESC}    rns=${US_RNS}    cas=${US_CAS}
    Should Contain    ${md}    RTM
    Log    ${md}    level=INFO

Nova User Story com Análise
    ${md}=    Gerar User Story Nova Com Analise
    ...    feature_titulo=Recuperação de senha via e-mail
    ...    persona=usuário com acesso bloqueado
    ...    objetivo_usuario=redefinir minha senha pelo e-mail cadastrado
    ...    beneficio=recuperar acesso sem contato com suporte
    Should Contain    ${md}    Parte A
    Log    ${md}    level=INFO
