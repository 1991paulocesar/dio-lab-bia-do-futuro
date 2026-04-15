# Base de Conhecimento

> [!TIP]
> **Prompt usado para esta etapa:**
> 
> Organize a base de conhecimento do agente "PCFinance" usando os 5 arquivos da pasta `data/`. Explique para que serve cada arquivo, implemente o carregamento dinâmico dos dados por usuário logado e monte um exemplo de contexto formatado focado em controle de gastos e metas financeiras pessoais. Preencha o template abaixo.
>
> [cole ou anexe o template `02-base-conhecimento.md` pra contexto]

## Dados Utilizados

| Arquivo | Formato | Para que serve no PCFinance? |
|---------|---------|---------------------|
| `historico_atendimento.csv` | CSV | Contextualizar interações anteriores do usuário com o agente, garantindo continuidade e personalização no atendimento. |
| `perfil_investidor.json` | JSON | Identificar o perfil financeiro do usuário logado para personalizar orientações sobre metas e controle de gastos. |
| `produtos_financeiros.json` | JSON | Base de conhecimento sobre produtos financeiros básicos para responder dúvidas educativas dos usuários. |
| `transacoes.csv` | CSV | Analisar o padrão de gastos do usuário logado por categoria e período, base principal para alertas e planejamento. |
| `metas_financeiras.json` | JSON | Acompanhar o progresso das metas financeiras do usuário e identificar desvios nos limites de gastos por categoria. |

---

## Adaptações nos Dados

> Você modificou ou expandiu os dados mockados? Descreva aqui.

A base de conhecimento foi expandida significativamente em relação ao projeto original:

- **5 usuários** com perfis financeiros distintos (conservador, moderado e arrojado) para simular diferentes realidades financeiras
- **Coluna `usuario_id`** adicionada nos CSVs para permitir filtragem dinâmica por usuário logado
- **`metas_financeiras.json`** criado como arquivo novo, contendo metas individuais e limites de gastos mensais por categoria — base principal para os alertas inteligentes do PCFinance
- O produto **Fundo Imobiliário (FII)** substituiu o Fundo Multimercado original, pois é um produto que permite validação mais assertiva das respostas do agente

---

## Estratégia de Integração

### Como os dados são carregados?
> Carregamento dinâmico por usuário logado.

O PCFinance carrega os dados **filtrando pelo `usuario_id` do usuário logado**, garantindo que cada pessoa veja apenas suas próprias informações. Isso torna a solução escalável para múltiplos usuários — exatamente o cenário do sistema PCFinance do Senac.

```python
import pandas as pd
import json

def carregar_dados_usuario(usuario_id: str) -> dict:
    """
    Carrega e filtra todos os dados do usuário logado.
    Retorna um dicionário com o contexto completo para o agente.
    """
    # Carrega todos os perfis e filtra pelo usuário logado
    perfis = json.load(open('./data/perfil_investidor.json'))
    perfil = next((p for p in perfis if p['id'] == usuario_id), None)

    # Carrega transações apenas do usuário logado
    df_transacoes = pd.read_csv('./data/transacoes.csv')
    transacoes = df_transacoes[df_transacoes['usuario_id'] == usuario_id]

    # Carrega histórico apenas do usuário logado
    df_historico = pd.read_csv('./data/historico_atendimento.csv')
    historico = df_historico[df_historico['usuario_id'] == usuario_id]

    # Carrega metas do usuário logado
    metas_todas = json.load(open('./data/metas_financeiras.json'))
    metas = next((m for m in metas_todas if m['usuario_id'] == usuario_id), None)

    # Produtos financeiros são compartilhados entre todos os usuários
    produtos = json.load(open('./data/produtos_financeiros.json'))

    return {
        'perfil': perfil,
        'transacoes': transacoes.to_dict(orient='records'),
        'historico': historico.to_dict(orient='records'),
        'metas': metas,
        'produtos': produtos
    }

# Exemplo de uso — usuário logado no sistema
usuario_logado = "USR001"
contexto = carregar_dados_usuario(usuario_logado)
```

### Como os dados são usados no prompt?
> Os dados são carregados dinamicamente e injetados no system prompt a cada sessão.

Os dados do usuário logado são carregados via função `carregar_dados_usuario()` e injetados automaticamente no system prompt, garantindo que o agente sempre tenha o contexto atualizado de quem está sendo atendido. Em versões futuras integradas ao PCFinance com banco de dados MySQL, essa função será substituída por consultas diretas ao banco.

```python
def montar_contexto_prompt(usuario_id: str) -> str:
    """
    Monta o contexto formatado para injetar no system prompt do agente.
    """
    dados = carregar_dados_usuario(usuario_id)
    perfil = dados['perfil']
    metas = dados['metas']

    # Calcula resumo de gastos por categoria
    transacoes = pd.DataFrame(dados['transacoes'])
    gastos = transacoes[transacoes['tipo'] == 'saida']
    resumo_gastos = gastos.groupby('categoria')['valor'].sum().to_dict()

    # Calcula alertas de gastos (categoria acima do limite definido)
    alertas = []
    limites = metas.get('limite_gastos_mensais', {})
    for categoria, total in resumo_gastos.items():
        limite = limites.get(categoria, 0)
        if limite > 0 and total > limite:
            percentual = round(((total - limite) / limite) * 100)
            alertas.append(f"{categoria}: R$ {total:.2f} (limite: R$ {limite:.2f}, +{percentual}% acima)")

    contexto = f"""
PERFIL DO USUÁRIO:
- Nome: {perfil['nome']}
- Renda mensal: R$ {perfil['renda_mensal']:.2f}
- Objetivo principal: {perfil['objetivo_principal']}

RESUMO DE GASTOS DO MÊS:
{chr(10).join([f'- {cat.capitalize()}: R$ {val:.2f}' for cat, val in resumo_gastos.items()])}

ALERTAS DE GASTOS:
{chr(10).join(alertas) if alertas else 'Nenhum alerta no momento.'}

METAS FINANCEIRAS:
{chr(10).join([f"- {m['descricao']}: R$ {m['valor_atual']:.2f} / R$ {m['valor_necessario']:.2f} (prazo: {m['prazo']})" for m in metas['metas']])}
"""
    return contexto
```

---

## Exemplo de Contexto Montado

> Contexto focado em controle de gastos e metas financeiras — alinhado ao PCFinance.

O exemplo abaixo mostra como o agente recebe o contexto de um usuário com dívidas ativas (Maria - USR002), priorizando as informações mais relevantes para orientação financeira pessoal.

```
PERFIL DO USUÁRIO:
- Nome: Maria Oliveira
- Renda mensal: R$ 3.200,00
- Objetivo principal: Organizar finanças e quitar dívidas

RESUMO DE GASTOS DO MÊS (outubro/2025):
- Moradia: R$ 960,00
- Alimentação: R$ 475,00
- Transporte: R$ 110,00
- Saúde: R$ 55,00
- Lazer: R$ 234,90
- Dívida (cartão): R$ 450,00
- Total de saídas: R$ 2.284,90

ALERTAS DE GASTOS:
- alimentacao: R$ 475,00 (limite: R$ 350,00, +36% acima)
- lazer: R$ 234,90 (limite: R$ 100,00, +135% acima)

METAS FINANCEIRAS:
- Quitar cartão de crédito: R$ 1.200,00 / R$ 4.500,00 (prazo: 2026-03)
- Criar reserva de emergência: R$ 500,00 / R$ 9.600,00 (prazo: 2027-06)

ÚLTIMAS INTERAÇÕES:
- 2025-11-28 (chat): Agente sugeriu redução de gastos com iFood para acelerar quitação da dívida
- 2025-11-02 (chat): Cliente revisou prazo para quitar cartão de crédito
```

> **Nota sobre escalabilidade:** Em versões futuras integradas ao banco de dados MySQL do PCFinance (Senac), o carregamento dinâmico será feito via consultas SQL diretas, substituindo os arquivos CSV/JSON mockados por dados reais persistidos no banco.