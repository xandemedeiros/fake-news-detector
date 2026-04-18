# Fake News Detector

Sistema de detecção de desinformação baseado em **múltiplos agentes de IA** com busca web em tempo real, verificação histórica e veredito fundamentado em evidências.

---

## Visão Geral

O Fake News Detector analisa textos jornalísticos através de um pipeline de três agentes especializados orquestrados pelo **LangGraph**. Cada agente tem uma responsabilidade distinta: coletar evidências, contextualizar e emitir um veredito final com score de confiança.

```
Texto de entrada → [Investigador] → [Defensor] → [Juiz] → Veredito + Score
```

---

## Stack

| Camada | Tecnologia |
|---|---|
| Orquestração de agentes | LangGraph |
| LLM | Groq (llama-3.3-70b-versatile) |
| Busca web | Tavily Search API |
| Base histórica | Fake.br Corpus (7.200 notícias) |
| API | FastAPI |
| Frontend | Streamlit |

---

## Arquitetura

```
fake-news-detector/
├── .env                  # Variáveis de ambiente
├── .gitignore
├── README.md             # Esse arquivo
├── start.sh              # Script de inicialização
├── requirements.txt
└── app/
    ├── main.py           # Entrypoint FastAPI
    ├── frontend.py       # Interface Streamlit
    ├── api/
    │   └── schema.py     # Modelos Pydantic
    └── core/
        ├── state.py      # Contrato de estado entre agentes
        ├── agents.py     # Lógica dos agentes
        └── graph.py      # Pipeline LangGraph
```

### Agentes

**Investigador** — Realiza busca web via Tavily e verifica correspondência na base Fake.br. Normaliza todas as evidências para um formato estruturado.

**Defensor** — Analisa as evidências coletadas em busca de fontes oficiais que confirmem ou contextualizem a notícia. Instrui o modelo a não inventar fatos.

**Juiz** — Consolida todas as evidências e emite o veredito final (`REAL`, `FAKE` ou `IMPRECISO`) com score de 0 a 100 e justificativa em frases objetivas. Prioriza evidências web sobre o histórico local.

---

## Instalação

**Pré-requisitos:** Python 3.10+

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/fake-news-detector.git
cd fake-news-detector

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves de API
```

---

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```dotenv
GROQ_API_KEY=sua_chave_aqui
TAVILY_API_KEY=sua_chave_aqui

```

Obtenha suas chaves em:
- Groq: https://console.groq.com
- Tavily: https://app.tavily.com

---

## Execução

```bash
./start.sh
```

O script inicia o backend, aguarda ele estar disponível e sobe o frontend automaticamente.

---

## API

### `POST /analisar`

Analisa um texto e retorna o veredito.

**Request:**
```json
{
  "texto": "Texto da notícia com pelo menos 20 caracteres..."
}
```

**Response:**
```json
{
  "veredito": "FAKE",
  "confianca": "85%",
  "justificativas": [
    "AGENTE DEFENSOR - Nenhuma fonte oficial encontrada.",
    "DECISÃO DO JUIZ - VEREDITO FINAL: FAKE\n\nSCORE: 85%\n\nJUSTIFICATIVA: ..."
  ],
  "fontes_verificadas": [
    "https://fonte1.com.br",
    "https://fonte2.com.br"
  ],
  "tempo_execucao": 4.21
}
```

**Vereditos possíveis:**

| Veredito | Significado |
|---|---|
| `REAL` | Evidências confirmam a notícia |
| `FAKE` | Evidências contradizem a notícia |
| `IMPRECISO` | Evidências insuficientes para conclusão |

---

## Dependências

```
fastapi
uvicorn[standard]
streamlit
langchain-groq
langchain-tavily
langgraph
pandas
python-dotenv
pydantic
requests
```

---

## Limitações

- A qualidade do veredito depende diretamente da disponibilidade de resultados na busca web (Tavily).
- Notícias muito recentes podem ter menos cobertura indexada e resultar em veredito `IMPRECISO`.
- O dataset Fake.br é auxiliar — coincidência de palavras não é prova de falsidade.
- O modelo LLM pode ter vieses inerentes ao seu treinamento.

---