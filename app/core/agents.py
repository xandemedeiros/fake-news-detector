import os
import re
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from app.core.state import AgentState
from __future__ import annotations
import logging
from functools import lru_cache

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_DATASET_URL = (
    "https://raw.githubusercontent.com/roneysco/Fake.br-Corpus/"
    "master/preprocessed/pre-processed.csv"
)

_SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
_LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

@lru_cache(maxsize=1)
def _get_llm() -> ChatGroq:
    return ChatGroq(model=_LLM_MODEL, temperature=0)

@lru_cache(maxsize=1)
def _get_search() -> TavilySearch:
    return TavilySearch(max_results=_SEARCH_MAX_RESULTS)

@lru_cache(maxsize=1)
def _get_dataset() -> pd.DataFrame:
    try:
        df = pd.read_csv(_DATASET_URL).dropna()
        logger.info("Dataset Fake.br carregado — %d registros.", len(df))
        return df
    except Exception as exc:
        logger.warning("Falha ao carregar dataset histórico: %s", exc)
        return pd.DataFrame()
    
def _extrair_keywords(texto: str, n: int = 5) -> list[str]:
    palavras = [w.strip(".,!?\"'") for w in texto.split() if len(w) > 5]
    return list(dict.fromkeys(palavras)) [:n]

def _buscar_historico(texto: str) -> str:
    df = _get_dataset()
    if df.empty or "preprocessed_news" not in df.columns:
        return ""
    
    keywords = _extrair_keywords(texto)
    for kw in keywords:
        mascara = df["preprocessed_news"].str.contains(kw, case=False, na=False, regex=False)
        if mascara.any():
            return (
                f"Padrão semelhante detectado na base Fake.br "
                f"(keyword: '{kw}', {mascara.sum()} ocorrência(s))."
            )
        return ""
    
# AGENTE INVESTIGADOR - Coleta evidências externas e verifica o hostório local
def investigador(state: AgentState) -> AgentState:
    texto = state["texto_original"]
    logger.info("INVESTIGADOR - Iniciando apuração...")

    historico = _buscar_historico(texto)

    query = f"fact check verificação notícia: {texto[:200]}"
    try:
        resultados_web = list[dict] = _get_search().invoke({"query": query})
    except Exception as exc:
        logger.error("Falha na busca web: %s", exc)
        resultados_web = [{"url": "", "content": f"Busca indisponível: {exc}"}]

    logger.info(
        "INVESTIGADOR - Concluído. Web: %d resultado(s). Histórico: %s",
        len(resultados_web),
        "encontrado" if historico else "sem match",
    )

    return {
        **state,
        "evidencias_csv": historico,
        "evidencias_web": resultados_web,
        "passo_atual": "investigacao_concluida"
    }

# AGENTE DEFENSOR - Analisa se existem fontes que contextualizam/ validam a notícia
def defensor(state: AgentState) -> AgentState:

    logger.info("DEFENSOR - Buscando fontes de validação...")

    evidencias_formatadas = "\n".join(
        f"- [{r.get('url', 'sem url')}]: {r.get('content', '')[:300]}"
        for r in (state.get("evidencias_web") or [])
    )
    
    prompt = f"""Você é um jornalista sênior especializado em verificação de fatos.

    NOTÍCIA ANALISADA:
    {state['texto_original']}

    EVIDÊNCIAS COLETADAS NA WEB:
    {evidencias_formatadas or 'Nenhuma evidência coletada.'}

    TAREFA:
    1. Identifique APENAS fatos verificáveis e fontes oficiais que confirmem ou contextualizem a notícia.
    2. Se não houver nenhuma, responda exatamente: "Nenhuma fonte oficial encontrada."
    3. Não invente, extrapole ou suponha informações ausentes.
    4. Seja objetivo e conciso (máximo 5 linhas).
    """

    
    resposta = _get_llm().invoke(prompt)
    logger.info("DEFENSOR - Análise concluída.")

    return {
    **state, 
    "analise_agentes": [f"[DEFENSOR]\n{resposta.content}"]
    }

# AGENTE JUIZ - Emite o veredito final com score de confiança e justificativa
def juiz(state: AgentState) -> AgentState:
    logger.infor("JUIZ - Analisando provas para veredito final...")

    evidencias_web_fmt = "\n".join(
        f"- [{r.get('url', '')}]: {r.get('content', '')[:300]}"
        for r in (state.get("evidencias_web") or [])
    )

    prompt = f"""Você é o Verificador-Chefe de uma agência de checagem de fatos de alto rigor.

    ═══════════════════════════════════════
    NOTÍCIA:
    {state['texto_original']}

    PESQUISA WEB:
    {evidencias_web_fmt or 'Sem resultados.'}

    HISTÓRICO LOCAL (Fake.br):
    {state.get('evidencias_csv') or 'Sem correspondência histórica.'}

    ANÁLISE DO DEFENSOR:
    {chr(10).join(state.get('analises_agentes') or ['Sem análise prévia.'])}
    ═══════════════════════════════════════

    INSTRUÇÃO:
    Com base exclusivamente nas evidências acima, emita um veredito seguindo RIGOROSAMENTE o formato abaixo.
    Não adicione texto fora deste formato.

    VEREDITO: [REAL | FAKE | IMPRECISO]
    SCORE: [0-100, onde 100 = certeza absoluta de veracidade]
    JUSTIFICATIVA: [Exatamente 2 frases objetivas explicando a decisão]
    """
    
    resposta = _get_llm().invoke(prompt)
    conteudo = str(resposta.content)

    score_match = re.search(r"SCORE:\s*(\d{1,3})", conteudo)
    score_final = max(0, min(100, int(score_match.group(1)))) if score_match else 50

    veredito_match = re.search(r"VEREDITO:\s*(REAL|FAKE|IMPRECISO)", conteudo, re.IGNORECASE)
    veredito_final = veredito_match.group(1).upper() if veredito_match else "IMPRECISO"

    logger.info("JUIZ - Veredito: %s | score: %d", veredito_final, score_final)

    return {
        **state, 
        "veredito_final": veredito_final, 
        "score": score_final,
        "analise_agentes": [f"[JUIZ]\n{conteudo}"],
        "passo_atual": "veredito_emitido"
    }