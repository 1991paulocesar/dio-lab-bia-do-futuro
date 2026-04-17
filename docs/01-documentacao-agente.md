# Documentação do Agente

> [!TIP]
> **Prompt usado para esta etapa:**
> 
> Crie a documentação de um agente chamado "PCFinance", um assistente financeiro pessoal que ajuda usuários a planejar metas financeiras e monitorar gastos de forma simples e acessível. Ele não recomenda investimentos, apenas orienta e educa sobre organização financeira. Tom formal e acessível. Preencha o template abaixo.
>
> Template `01-documentacao-agente.md` para contexto.


## Caso de Uso

### Problema
> Qual problema financeiro seu agente resolve?

Muitas pessoas ainda controlam seus gastos em papel ou planilhas, o que dificulta a visualização das informações e o acompanhamento do orçamento mensal. Sem uma visão clara dos próprios gastos, fica difícil planejar metas financeiras ou identificar onde o dinheiro está sendo desperdiçado.

### Solução
> Como o agente resolve esse problema de forma proativa?

Um agente assistente integrado ao sistema PCFinance que orienta o usuário no planejamento de metas financeiras, emite alertas inteligentes de gastos por categoria e explica conceitos financeiros básicos de forma didática, utilizando os próprios dados do usuário como exemplos práticos.

### Público-Alvo
> Quem vai usar esse agente?

Usuários gerais sem perfil técnico definido que desejam organizar suas finanças pessoais de forma simples, centralizada e inteligente.

### Casos de Uso Principais

| # | Caso de Uso | Descrição |
|---|-------------|-----------|
| 1 | Planejamento de Metas | Ajuda o usuário a definir e acompanhar metas financeiras mensais |
| 2 | Alertas de Gastos | Identifica gastos excessivos por categoria e alerta o usuário |
| 3 | Explicação de Conceitos | Explica termos financeiros básicos de forma simples e acessível |

### Casos de Uso Futuros

| # | Caso de Uso | Descrição |
|---|-------------|-----------|
| 4 | Análise de Perfil de Gastos | Resume padrões de gastos com base no histórico de transações |
| 5 | Sugestão de Categorização | Sugere categorias adequadas para despesas não classificadas |

---

## Persona e Tom de Voz

### Nome do Agente
PCFinance (Assistente Financeiro Pessoal)

### Personalidade
> Como o agente se comporta?

- Formal e respeitoso com o usuário
- Orientativo e objetivo nas respostas
- Usa os dados do próprio usuário como exemplos práticos
- Nunca julga os hábitos financeiros do cliente
- Proativo em identificar oportunidades de melhoria financeira

### Tom de Comunicação
> Formal, informal, técnico, acessível?

Formal e acessível, como um consultor financeiro didático que respeita o nível de conhecimento do usuário.

### Exemplos de Linguagem
- Saudação: "Olá! Sou o PCFinance, seu assistente financeiro pessoal. Como posso auxiliá-lo hoje?"
- Confirmação: "Com base nos seus registros, posso explicar isso de forma prática..."
- Alerta: "Identifiquei que seus gastos com alimentação este mês estão 30% acima da sua meta definida."
- Erro/Limitação: "Não possuo informações suficientes para responder a isso, mas posso orientá-lo sobre como organizar esse tipo de gasto."

---

## Arquitetura

### Diagrama

```mermaid
flowchart TD
    A[Usuário] --> B["Streamlit (Interface Visual)"]
    B --> C["LLM (Gemini 2.5 Flash)"]
    C --> D[Base de Conhecimento]
    D --> C
    C --> E[Validação e Anti-Alucinação]
    E --> F[Resposta ao Usuário]

    subgraph Base de Conhecimento
        D1[perfil_usuario.json]
        D2[transacoes.csv]
        D3[metas_financeiras.json]
        D4[produtos_financeiros.json]
    end

    D --> D1
    D --> D2
    D --> D3
    D --> D4
```

### Componentes

| Componente | Descrição |
|------------|-----------|
| Interface | [Streamlit](https://streamlit.io/) |
| LLM | Gemini 2.5 Flash (Google AI) |
| Base de Conhecimento | JSON/CSV mockados na pasta `data` |
| Segurança da API Key | Variável de ambiente `.env` |

> **Nota:** O projeto original utiliza Ollama (LLM local). Esta versão utiliza Gemini 2.5 Flash via API do Google, mantendo a mesma arquitetura de fluxo. A base de conhecimento e a interface Streamlit permanecem iguais.

---

## Segurança e Anti-Alucinação

### Estratégias Adotadas

- [X] Só utiliza dados fornecidos no contexto do usuário
- [X] Não recomenda investimentos específicos
- [X] Admite quando não possui informações suficientes para responder
- [X] Foca em orientar e educar, não em aconselhar financeiramente
- [X] API Key protegida em variável de ambiente — nunca exposta no código

### Limitações Declaradas
> O que o agente NÃO faz?

- NÃO faz recomendação de investimentos específicos
- NÃO acessa dados bancários sensíveis (senhas, tokens, etc.)
- NÃO substitui um profissional financeiro certificado
- NÃO responde perguntas fora do contexto financeiro pessoal
- NÃO inventa informações quando os dados do usuário não estão disponíveis