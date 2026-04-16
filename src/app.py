import json
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

# ============ CONFIGURAÇÃO ============
# Carrega variáveis de ambiente do arquivo .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODELO = "gemini-2.5-flash"

# Inicializa o cliente Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# ============ SELEÇÃO DE USUÁRIO ============
# Simula o usuário logado no sistema PCFinance
# Em versões futuras, isso será substituído pelo login real do sistema
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
    # Carrega todos os perfis e filtra pelo usuário logado
    perfis = json.load(open('./data/perfil_investidor.json', encoding='utf-8'))
    perfil = next((p for p in perfis if p['id'] == usuario_id), None)

    # Carrega transações apenas do usuário logado
    df_transacoes = pd.read_csv('./data/transacoes.csv')
    transacoes = df_transacoes[df_transacoes['usuario_id'] == usuario_id]

    # Carrega histórico apenas do usuário logado
    df_historico = pd.read_csv('./data/historico_atendimento.csv')
    historico = df_historico[df_historico['usuario_id'] == usuario_id]

    # Carrega metas do usuário logado
    metas_todas = json.load(open('./data/metas_financeiras.json', encoding='utf-8'))
    metas = next((m for m in metas_todas if m['usuario_id'] == usuario_id), None)

    # Produtos financeiros são compartilhados entre todos os usuários
    produtos = json.load(open('./data/produtos_financeiros.json', encoding='utf-8'))

    return {
        'perfil': perfil,
        'transacoes': transacoes,
        'historico': historico.to_dict(orient='records'),
        'metas': metas,
        'produtos': produtos
    }

# ============ MONTAR CONTEXTO DINÂMICO ============
def montar_contexto(usuario_id: str) -> str:
    """
    Monta o contexto formatado para injetar no system prompt.
    Técnica: RAG + Chain-of-Thought — calcula alertas automaticamente.
    """
    dados = carregar_dados_usuario(usuario_id)
    perfil = dados['perfil']
    metas = dados['metas']
    transacoes = dados['transacoes']

    # Calcula resumo de gastos por categoria
    gastos = transacoes[transacoes['tipo'] == 'saida']
    resumo_gastos = gastos.groupby('categoria')['valor'].sum().to_dict()

    # Calcula alertas de gastos (categoria acima do limite definido)
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

    # Formata metas com progresso
    metas_formatadas = []
    for m in metas['metas']:
        progresso = (m['valor_atual'] / m['valor_necessario']) * 100
        metas_formatadas.append(
            f"- {m['descricao']}: R$ {m['valor_atual']:.2f} / "
            f"R$ {m['valor_necessario']:.2f} ({progresso:.1f}%) | prazo: {m['prazo']}"
        )

    contexto = f"""
PERFIL DO USUÁRIO:
- Nome: {perfil['nome']}
- Idade: {perfil['idade']} anos
- Profissão: {perfil['profissao']}
- Renda mensal: R$ {perfil['renda_mensal']:.2f}
- Objetivo principal: {perfil['objetivo_principal']}

RESUMO DE GASTOS DO MÊS:
{chr(10).join([f'- {cat.capitalize()}: R$ {val:.2f}' for cat, val in resumo_gastos.items()])}

ALERTAS DE GASTOS:
{chr(10).join(alertas) if alertas else '- Nenhum alerta no momento.'}

METAS FINANCEIRAS:
{chr(10).join(metas_formatadas)}

ÚLTIMAS INTERAÇÕES:
{chr(10).join([f"- {h['data']} ({h['canal']}): {h['resumo']}" for h in dados['historico'][-3:]])}
"""
    return contexto

# ============ SYSTEM PROMPT ============
# Técnica: Role Prompting + Negative Prompting + Instruction Prompting
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

# ============ CHAMAR GEMINI ============
def perguntar(mensagem: str, usuario_id: str) -> str:
    """
    Envia a pergunta ao Gemini com o contexto do usuário logado.
    Técnica: RAG — contexto dinâmico injetado a cada chamada.
    """
    contexto = montar_contexto(usuario_id)

    prompt_completo = f"""
{SYSTEM_PROMPT}

CONTEXTO DO USUÁRIO LOGADO:
{contexto}

Pergunta: {mensagem}
"""
    response = client.models.generate_content(
        model=MODELO,
        contents=prompt_completo
    )
    return response.text

# ============ INTERFACE STREAMLIT ============
st.set_page_config(
    page_title="PCFinance - Assistente Financeiro",
    page_icon="💰",
    layout="centered"
)

st.title("💰 PCFinance")
st.caption("Assistente Financeiro Pessoal com IA Generativa")

# Seletor de usuário na barra lateral (simula login)
with st.sidebar:
    st.header("👤 Usuário")
    usuario_selecionado = st.selectbox(
        "Selecione o usuário:",
        options=list(USUARIOS_DISPONIVEIS.keys()),
        format_func=lambda x: f"{x} - {USUARIOS_DISPONIVEIS[x]}"
    )
    st.info(f"Logado como: **{USUARIOS_DISPONIVEIS[usuario_selecionado]}**")
    st.divider()
    st.caption("⚠️ Esta é uma versão de demonstração com dados fictícios.")

# Inicializa histórico de chat na sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Input do usuário
if pergunta := st.chat_input("Digite sua pergunta financeira..."):
    # Exibe mensagem do usuário
    st.chat_message("user").write(pergunta)
    st.session_state.messages.append({"role": "user", "content": pergunta})

    # Gera resposta do agente
    with st.spinner("Analisando seus dados..."):
        resposta = perguntar(pergunta, usuario_selecionado)

    # Exibe resposta do agente
    st.chat_message("assistant").write(resposta)
    st.session_state.messages.append({"role": "assistant", "content": resposta})