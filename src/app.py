import json
import time
import pandas as pd
import streamlit as st
from google import genai
from dotenv import load_dotenv
import os

# ============ CONFIGURAÇÃO ============
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODELO = "gemini-2.5-flash"
client = genai.Client(api_key=GEMINI_API_KEY)

# ============ USUÁRIOS DISPONÍVEIS ============
USUARIOS_DISPONIVEIS = {
    "USR001": "João Silva",
    "USR002": "Maria Oliveira",
    "USR003": "Carlos Souza",
    "USR004": "Ana Ferreira",
    "USR005": "Roberto Lima"
}

# ============ CARREGAR DADOS DO USUÁRIO ============
def carregar_dados_usuario(usuario_id: str) -> dict:
    """
    Carrega e filtra todos os dados do usuário logado.
    Técnica: RAG — injeta os dados reais do usuário como contexto.
    """
    perfis = json.load(open('./data/perfil_investidor.json', encoding='utf-8'))
    perfil = next((p for p in perfis if p['id'] == usuario_id), None)

    df_transacoes = pd.read_csv('./data/transacoes.csv')
    transacoes = df_transacoes[df_transacoes['usuario_id'] == usuario_id]

    df_historico = pd.read_csv('./data/historico_atendimento.csv')
    historico = df_historico[df_historico['usuario_id'] == usuario_id]

    metas_todas = json.load(open('./data/metas_financeiras.json', encoding='utf-8'))
    metas = next((m for m in metas_todas if m['usuario_id'] == usuario_id), None)

    produtos = json.load(open('./data/produtos_financeiros.json', encoding='utf-8'))

    return {
        'perfil': perfil,
        'transacoes': transacoes,
        'historico': historico.to_dict(orient='records'),
        'metas': metas,
        'produtos': produtos
    }

# ============ MONTAR CONTEXTO DINÂMICO ============
def montar_contexto(usuario_id: str):
    """
    Monta o contexto e retorna também métricas de volumetria.
    Técnica: RAG + Chain-of-Thought — calcula alertas automaticamente.
    """
    dados = carregar_dados_usuario(usuario_id)
    perfil = dados['perfil']
    metas = dados['metas']
    transacoes = dados['transacoes']

    gastos = transacoes[transacoes['tipo'] == 'saida']
    receitas = transacoes[transacoes['tipo'] == 'entrada']
    resumo_gastos = gastos.groupby('categoria')['valor'].sum().to_dict()
    total_gastos = gastos['valor'].sum()
    total_receitas = receitas['valor'].sum()
    saldo_mes = total_receitas - total_gastos

    alertas = []
    limites = metas.get('limite_gastos_mensais', {})
    for categoria, total in resumo_gastos.items():
        limite = limites.get(categoria, 0)
        if limite > 0 and total > limite:
            percentual = round(((total - limite) / limite) * 100)
            alertas.append(
                f"- {categoria.capitalize()}: R$ {total:.2f} "
                f"(limite: R$ {limite:.2f}, +{percentual}% acima)"
            )

    metas_formatadas = []
    for m in metas['metas']:
        progresso = (m['valor_atual'] / m['valor_necessario']) * 100
        metas_formatadas.append(
            f"- {m['descricao']}: R$ {m['valor_atual']:.2f} / "
            f"R$ {m['valor_necessario']:.2f} ({progresso:.1f}%) | prazo: {m['prazo']}"
        )

    contexto_texto = f"""
PERFIL DO USUÁRIO:
- Nome: {perfil['nome']}
- Idade: {perfil['idade']} anos
- Profissão: {perfil['profissao']}
- Renda mensal: R$ {perfil['renda_mensal']:.2f}
- Objetivo principal: {perfil['objetivo_principal']}

RESUMO FINANCEIRO DO MÊS:
- Total de receitas: R$ {total_receitas:.2f}
- Total de gastos: R$ {total_gastos:.2f}
- Saldo do mês: R$ {saldo_mes:.2f}

GASTOS POR CATEGORIA:
{chr(10).join([f'- {cat.capitalize()}: R$ {val:.2f}' for cat, val in resumo_gastos.items()])}

ALERTAS DE GASTOS:
{chr(10).join(alertas) if alertas else '- Nenhum alerta no momento.'}

METAS FINANCEIRAS:
{chr(10).join(metas_formatadas)}

ÚLTIMAS INTERAÇÕES:
{chr(10).join([f"- {h['data']} ({h['canal']}): {h['resumo']}" for h in dados['historico'][-3:]])}
"""
    metricas = {
        'total_transacoes': len(transacoes),
        'total_gastos': total_gastos,
        'total_receitas': total_receitas,
        'saldo_mes': saldo_mes,
        'num_alertas': len(alertas),
        'num_metas': len(metas['metas'])
    }

    return contexto_texto, metricas

# ============ SYSTEM PROMPT ============
SYSTEM_PROMPT = """Você é o PCFinance, um assistente financeiro pessoal formal e objetivo.

OBJETIVO:
Orientar o usuário no controle de gastos, planejamento de metas financeiras e 
educação financeira básica, utilizando exclusivamente os dados fornecidos no 
contexto abaixo como base para suas respostas.

REGRAS DE COMPORTAMENTO:
- Utilize APENAS os dados fornecidos no contexto. Nunca invente valores ou informações;
- Mantenha tom formal e respeitoso em todas as interações;
- NUNCA recomende investimentos específicos. Explique como funcionam, mas a decisão é do usuário;
- JAMAIS responda perguntas fora do escopo de finanças pessoais;
- Ao identificar gastos acima do limite, alerte de forma clara e sem julgamentos;
- Se não tiver a informação necessária, admita: "Não possuo essa informação no momento";
- Respostas diretas e objetivas, com no máximo 3 parágrafos;
- Sempre verifique se o usuário compreendeu antes de encerrar.

O QUE VOCÊ NÃO FAZ:
- Não recomenda produtos financeiros específicos;
- Não acessa nem solicita senhas ou dados bancários sensíveis;
- Não responde sobre outros usuários do sistema;
- Não substitui um profissional financeiro certificado;
- Não responde perguntas fora do contexto de finanças pessoais.
"""

# ============ CHAMAR GEMINI COM MÉTRICAS ============
def perguntar(mensagem: str, usuario_id: str) -> dict:
    """
    Envia a pergunta ao Gemini e retorna resposta + métricas de latência e tokens.
    """
    contexto, metricas_usuario = montar_contexto(usuario_id)

    prompt_completo = f"""
{SYSTEM_PROMPT}

CONTEXTO DO USUÁRIO LOGADO:
{contexto}

Pergunta: {mensagem}
"""
    inicio = time.time()
    response = client.models.generate_content(
        model=MODELO,
        contents=prompt_completo
    )
    latencia = round((time.time() - inicio) * 1000)

    tokens_entrada = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
    tokens_saida = response.usage_metadata.candidates_token_count if response.usage_metadata else 0

    return {
        'resposta': response.text,
        'latencia_ms': latencia,
        'tokens_entrada': tokens_entrada,
        'tokens_saida': tokens_saida,
        'total_tokens': tokens_entrada + tokens_saida,
        'metricas_usuario': metricas_usuario
    }

# ============ INTERFACE STREAMLIT ============
st.set_page_config(
    page_title="PCFinance - Assistente Financeiro",
    page_icon="💰",
    layout="wide"
)

st.title("💰 PCFinance")
st.caption("Assistente Financeiro Pessoal com IA Generativa | Bootcamp Bradesco - GENAI & Dados | DIO")

# ============ SIDEBAR ============
with st.sidebar:
    st.header("👤 Usuário")
    usuario_selecionado = st.selectbox(
        "Selecione o usuário:",
        options=list(USUARIOS_DISPONIVEIS.keys()),
        format_func=lambda x: f"{USUARIOS_DISPONIVEIS[x]}"
    )

    # CORREÇÃO: Reseta histórico ao trocar de usuário
    if "usuario_atual" not in st.session_state:
        st.session_state.usuario_atual = usuario_selecionado
        st.session_state.messages = []
        st.session_state.logs = []

    if st.session_state.usuario_atual != usuario_selecionado:
        st.session_state.messages = []
        st.session_state.logs = []
        st.session_state.usuario_atual = usuario_selecionado
        st.rerun()

    st.info(f"Logado como: **{USUARIOS_DISPONIVEIS[usuario_selecionado]}**")
    st.divider()

    # Métricas do usuário na sidebar
    try:
        _, metricas = montar_contexto(usuario_selecionado)
        st.subheader("📊 Resumo do Mês")
        col1, col2 = st.columns(2)
        col1.metric("Receitas", f"R$ {metricas['total_receitas']:.0f}")
        col2.metric("Gastos", f"R$ {metricas['total_gastos']:.0f}")
        delta_color = "normal" if metricas['saldo_mes'] >= 0 else "inverse"
        st.metric("Saldo", f"R$ {metricas['saldo_mes']:.0f}")
        if metricas['num_alertas'] > 0:
            st.warning(f"⚠️ {metricas['num_alertas']} alerta(s) de gasto")
        else:
            st.success("✅ Gastos dentro dos limites")
        st.caption(f"📋 {metricas['total_transacoes']} transações | {metricas['num_metas']} metas")
    except Exception as e:
        st.error(f"Erro ao carregar métricas: {e}")

    st.divider()
    st.caption("⚠️ Dados fictícios para demonstração.")

# ============ INICIALIZA SESSION STATE ============
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logs" not in st.session_state:
    st.session_state.logs = []

# ============ LAYOUT CHAT + MÉTRICAS ============
col_chat, col_logs = st.columns([2, 1])

with col_chat:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if pergunta := st.chat_input("Digite sua pergunta financeira..."):
        st.chat_message("user").write(pergunta)
        st.session_state.messages.append({"role": "user", "content": pergunta})

        with st.spinner("Analisando seus dados financeiros..."):
            resultado = perguntar(pergunta, usuario_selecionado)

        st.chat_message("assistant").write(resultado['resposta'])
        st.session_state.messages.append({"role": "assistant", "content": resultado['resposta']})

        st.session_state.logs.append({
            'usuario': USUARIOS_DISPONIVEIS[usuario_selecionado],
            'pergunta': pergunta[:50] + '...' if len(pergunta) > 50 else pergunta,
            'latencia_ms': resultado['latencia_ms'],
            'tokens_entrada': resultado['tokens_entrada'],
            'tokens_saida': resultado['tokens_saida'],
            'total_tokens': resultado['total_tokens']
        })

with col_logs:
    st.subheader("📈 Métricas de Execução")
    if st.session_state.logs:
        ultimo = st.session_state.logs[-1]
        st.metric("⏱️ Latência", f"{ultimo['latencia_ms']} ms")
        st.metric("📥 Tokens entrada", ultimo['tokens_entrada'])
        st.metric("📤 Tokens saída", ultimo['tokens_saida'])
        st.metric("🔢 Total tokens", ultimo['total_tokens'])
        st.divider()
        st.caption("📋 Histórico de requisições:")
        for log in reversed(st.session_state.logs):
            st.caption(
                f"👤 {log['usuario']} | "
                f"⏱️ {log['latencia_ms']}ms | "
                f"🔢 {log['total_tokens']} tokens"
            )
    else:
        st.info("As métricas aparecerão após a primeira pergunta.")