from __future__ import annotations
import os
import re
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from app.core.state import AgentState
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

def _formatar_evidencias(evidencias: list) -> str:
    linhas = []
    for r in evidencias or []:
        if isinstance(r, dict):
            url = r.get("url", "sem url")
            content = r.get("content", "")[:300]
            linhas.append(f"- [{url}]: {content}")
        elif isinstance(r, str):
            linhas.append(f"- {r[:300]}")
    return "\n".join(linhas) or "Nenhuma evidência coletada."
    
# AGENTE INVESTIGADOR - Coleta evidências externas e verifica o hostório local
def investigador(state: AgentState) -> AgentState:
    texto = state["texto_original"]
    logger.info("INVESTIGADOR — iniciando apuração.")

    historico = _buscar_historico(texto)

    query = f"{texto[:150]} notícia oficial hoje"
    try:
        resultados_brutos = _get_search().invoke({"query": query})
        resultados_normalizados = []

        lista_final = []
        if isinstance(resultados_brutos, dict):
            lista_final = resultados_brutos.get("results", [])
        elif isinstance(resultados_brutos, list):
            lista_final = resultados_brutos

        for r in lista_final:
            if isinstance(r, dict):
                resultados_normalizados.append({
                    "url": r.get("url", ""),
                    "content": r.get("content", r.get("snippet", ""))
                })
        
        logger.info(f"INVESTIGADOR — Sucesso: {len(resultados_normalizados)} fontes reais encontradas.")

    except Exception as exc:
        logger.error(f"FALHA REAL NA BUSCA: {str(exc)}")
        resultados_normalizados = []

    logger.info(
        "INVESTIGADOR — concluído. Web: %d resultado(s). Histórico: %s",
        len(resultados_normalizados),
        "encontrado" if historico else "sem match",
    )

    return {
        **state,
        "evidencias_csv": historico,
        "evidencias_web": resultados_normalizados,
    }

# AGENTE DEFENSOR - Analisa se existem fontes que contextualizam/ validam a notícia
def defensor(state: AgentState) -> AgentState:

    logger.info("DEFENSOR - Buscando fontes de validação...")

    evidencias_formatadas = _formatar_evidencias(state.get("evidencias_web"))
    
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
    "analises_agentes":[f"AGENTE DEFENSOR - {resposta.content}"]
    }

# AGENTE JUIZ - Emite o veredito final com score de confiança e justificativa
def juiz(state: AgentState) -> AgentState:
    logger.info("JUIZ - Analisando provas para veredito final...")

    evidencias_web_fmt = _formatar_evidencias(state.get("evidencias_web"))

    prompt = f"""Você é o Verificador-Chefe de uma agência de checagem de fatos de alto rigor.

    ═══════════════════════════════════════
    NOTÍCIA:
    {state['texto_original']}

    PESQUISA WEB:
    {evidencias_web_fmt or 'Sem resultados.'}

    HISTÓRICO LOCAL (Fake.br):
    {state.get['evidencias_csv'] or 'Sem correspondência histórica.'}
    ATENÇÃO: O histórico local é apenas um sinal auxiliar. Coincidência de palavras
    não é prova de falsidade. Priorize SEMPRE as evidências da web.

    ANÁLISE DO DEFENSOR:
    {chr(10).join(state.get('analises_agentes') or ['Sem análise prévia.'])}
    ═══════════════════════════════════════

    INSTRUÇÃO:
    Com base exclusivamente nas evidências acima, emita um veredito seguindo RIGOROSAMENTE o formato abaixo.
    Não adicione texto fora deste formato.

    VEREDITO: [REAL | FAKE | IMPRECISO]
    SCORE: [0-100, onde 100 = certeza absoluta de veracidade]
    JUSTIFICATIVA: [Exatamente 2 frases objetivas explicando a decisão]

    ⚠️ REGRA CRÍTICA DE DECISÃO:
    1. Se 'PESQUISA WEB' retornar 'Sem resultados' ou 0 fontes, NÃO classifique como FAKE.
    2. Nestes casos, o veredito DEVE ser 'IMPRECISO'. 
    3. JUSTIFICATIVA deve ser: 'Não foram encontradas fontes oficiais até o momento para confirmar ou negar o fato.'
    4. Atribua SCORE: 50 para casos sem evidências.
    """
    
    resposta = _get_llm().invoke(prompt)
    conteudo = str(resposta.content)

    score_match = re.search(r"SCORE:\s*(\d{1,3})", conteudo)
    score_final = max(0, min(100, int(score_match.group(1)))) if score_match else 50

    veredito_match = re.search(r"VEREDITO:\s*(REAL|FAKE|IMPRECISO)", conteudo, re.IGNORECASE)
    veredito_final = veredito_match.group(1).upper() if veredito_match else "IMPRECISO"

    logger.info("JUIZ - Veredito: %s | score: %d", veredito_final, score_final)

    texto_formatado = (
        f"VEREDITO FINAL: {veredito_final}\n\n"
        f"SCORE DE VERACIDADE: {score_final}%\n\n"
        f"JUSTIFICATIVA: {conteudo.split('JUSTIFICATIVA:')[-1].strip()}"
    )

    return {
        **state, 
        "veredito_final": veredito_final, 
        "score": score_final,
        "analises_agentes":[f"DECISÃO DO JUIZ -\n{texto_formatado}"],
    }