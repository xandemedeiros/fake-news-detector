import os
import pandas as pd
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from app.core.state import AgentState

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
search_tool = TavilySearch(max_results=3)

URL_DATASET = "https://raw.githubusercontent.com/roneysco/Fake.br-Corpus/master/preprocessed/pre-processed.csv"
try:
    df_historico = pd.read_csv(URL_DATASET).dropna()
except Exception as e:
    print(f"Erro ao carregar dataset: {e}")
    df_historico = pd.DataFrame()

# AGENTE INVESTIGADOR
def investigador(state: AgentState) -> AgentState:
    texto = state["texto_original"]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] INVESTIGADOR: Iniciando apuração...")

    palavras_chave = [w for w in texto.split() if len(w) > 5][:3]
    match_historico = ""
    
    if not df_historico.empty and palavras_chave:
        mascara = df_historico['preprocessed_news'].str.contains(palavras_chave[0], case=False, na=False)
        similaridade = df_historico[mascara].head(1)
        
        if not similaridade.empty:
            match_historico = "Padrão detectado em base de desinformação histórica (Fake.br)."

    query_busca = f"fact check: {texto[:150]}"
    try:
        resultados_web = search_tool.invoke({"query": query_busca})
    except Exception as e:
        resultados_web = [{"url": "erro", "content": f"Falha na busca web: {e}"}]

    return {
        **state,
        "evidencias_csv": match_historico,
        "evidencias_web": resultados_web,
        "passo_atual": "investigacao_concluida"
    }

# AGENTE DEFENSOR
def defensor(state: AgentState) -> AgentState:

    print(f"[{datetime.now().strftime('%H:%M:%S')}] DEFENSOR: Buscando fontes de validação...")
    
    prompt = f"""
    Você é um jornalista sênior verificador de fatos imparcial. Sua missão é buscar QUALQUER evidência 
    que confirme ou contextualize positivamente a seguinte notícia.
    
    Notícia: {state['texto_original']}
    Evidências coletadas: {state['evidencias_web']}
    
    Liste apenas fontes oficiais ou fatos confirmados que apoiem a notícia. 
    Se não houver nada, apenas indique 'Nenhuma fonte oficial encontrada', não inventando fatos.
    """
    
    resposta = llm.invoke(prompt)
    return {**state, "analise_xyz": [f"Defesa: {resposta.content}"]}

# AGENTE JUIZ
def juiz(state: AgentState) -> AgentState:

    print(f"[{datetime.now().strftime('%H:%M:%S')}] JUIZ: Analisando provas e emitindo veredito...")
    
    prompt = f"""
    Com base nas investigações:
    - Histórico: {state['evidencias_csv']}
    - Web: {state['evidencias_web']}
    - Defesa: {state['analise_xyz']}
    
    Emita um veredito sobre a notícia: "{state['texto_original']}"
    Use o formato:
    VEREDITO: [REAL/FAKE/IMPRECISO]
    SCORE: [0-100]
    MOTIVOS: [Liste X, Y, Z com base nas provas]
    """
    
    resposta = llm.invoke(prompt)
    return {**state, "veredito_final": resposta.content, "score": 100}