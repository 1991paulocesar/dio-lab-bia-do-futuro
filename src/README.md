# Passo a Passo de Execução

## Pré-requisitos

- Python 3.10 ou superior
- Conta Google com API Key do Gemini ([aistudio.google.com](https://aistudio.google.com))

## Configuração da API Key

> ⚠️ **Nunca suba sua API Key para o repositório!**

Crie um arquivo `.env` na raiz do projeto:

```
GEMINI_API_KEY=sua_key_aqui
```

O arquivo `.gitignore` já está configurado para ignorar o `.env`.

## Instalação das Dependências

```bash
pip install streamlit pandas google-genai python-dotenv
```

## Como Rodar

```bash
# Na raiz do projeto
streamlit run src/app.py
```

## Estrutura do Projeto

```
dio-lab-bia-do-futuro/
│
├── data/
│   ├── perfil_investidor.json      # Perfis dos 5 usuários
│   ├── transacoes.csv              # Transações por usuário
│   ├── historico_atendimento.csv   # Histórico de atendimento
│   ├── metas_financeiras.json      # Metas e limites por usuário
│   └── produtos_financeiros.json   # Produtos financeiros disponíveis
│
├── docs/
│   ├── 01-documentacao-agente.md
│   ├── 02-base-conhecimento.md
│   ├── 03-prompts.md
│   ├── 04-metricas.md
│   └── 05-pitch.md
│
├── src/
│   ├── app.py                      # Aplicação Streamlit
│   └── README.md                   # Este arquivo
│
├── .env                            # API Key (não sobe para o git!)
├── .gitignore
└── README.md
```

## Diferenciais em Relação ao Projeto Original

| Item | Original (Edu) | PCFinance |
|---|---|---|
| LLM | Ollama (local) | Gemini 2.5 Flash (API) |
| Usuários | 1 usuário fixo | 5 usuários selecionáveis |
| Metas | Não tinha | `metas_financeiras.json` |
| Alertas | Manual | Calculado automaticamente |
| Foco | Educação financeira | Controle de gastos e metas |
| Tom | Informal | Formal |

## Evidência de Execução

> Adicione aqui um print da aplicação funcionando após os testes.