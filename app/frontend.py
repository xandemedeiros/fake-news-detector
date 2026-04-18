from __future__ import annotations
import streamlit as st
import requests
import os

#API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/analisar")
API_URL = os.getenv("API_URL", "https://fake-news-detector-cala.onrender.com/analisar")

st.set_page_config(
    page_title="Fake News Detector",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
    <style>
        .verdict-box { padding: 1.5rem; border-radius: 12px; text-align: center; }
        .stTextArea textarea { font-size: 0.95rem; }
    </style>
""", unsafe_allow_html=True)
st.title("Fake News Detector")
st.caption("Análise de desinformação com múltiplos agentes de IA • FastAPI + LangGraph + Streamlit")
st.divider()

col_input, col_result = st.columns([3, 2], gap="large")

with col_input:
    texto_input = st.text_area(
        "Insira o texto da notícia:",
        placeholder="Cole ou digite o texto aqui...",
        height=320,
        max_chars=5000,
    )
    char_count = len(texto_input)
    st.caption(f"{char_count}/5000 caracteres")

    botao = st.button("Analisar Notícia", use_container_width=True, type="primary")

if botao:
    if char_count < 20:
        st.error("O texto precisa ter pelo menos 20 caracteres.")
        st.stop()

    with st.spinner("Agentes investigando... isso pode levar alguns segundos."):
        try:
            response = requests.post(API_URL, json={"texto": texto_input}, timeout=120)
            response.raise_for_status()
            data: dict = response.json()
        except requests.exceptions.ConnectionError:
            st.error("Não foi possível conectar à API. Verifique se o backend está rodando.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("A análise demorou muito. Tente novamente.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"Erro na API: {e.response.status_code} — {e.response.text}")
            st.stop()
        except Exception as e:
            st.error(f"Erro inesperado: {e}")
            st.stop()

    veredito = data.get("veredito", "IMPRECISO").upper()
    score_raw = data.get("confianca", "0%").replace("%", "")
    score = int(score_raw) if score_raw.isdigit() else 0

    COR_MAP = {"REAL": "#2ecc71", "FAKE": "#e74c3c", "IMPRECISO": "#f39c12"}
    EMOJI_MAP = {"REAL": "✅", "FAKE": "🚨", "IMPRECISO": "⚠️"}
    cor = COR_MAP.get(veredito, "#95a5a6")
    emoji = EMOJI_MAP.get(veredito, "❓")

    with col_result:
        st.markdown(f"""
            <div class="verdict-box" style="background-color:{cor}22; border: 2px solid {cor};">
                <h1 style="color:{cor}; margin:0;">{emoji} {veredito}</h1>
                <p style="color:{cor}; font-size:1.1rem; margin:0.5rem 0 0 0;">
                    Confiança: <strong>{data.get('confianca', 'N/A')}</strong>
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.progress(score / 100, text=f"\nScore de veracidade: {score}%")
        st.caption(f"Processado em {data.get('tempo_execucao', '?')}s")

    st.divider()

    st.subheader("Análise Detalhada dos Agentes")
    justificativas = data.get("justificativas", [])
    for i, motivo in enumerate(justificativas):
                header = "Análise Adicional"
                if "DEFENSOR" in motivo: header = "Agente Defensor"
                if "JUIZ" in motivo: header = "Veredito do Juiz"
                
                with st.expander(header, expanded=(header == "Veredito do Juiz")):
                    st.markdown(f'<div class="justification-text">{motivo}</div>', unsafe_allow_html=True)

    fontes = data.get("fontes_verificadas", [])
    with st.expander(f"Fontes Consultadas ({len(fontes)})", expanded=False):
        if fontes:
            for fonte in fontes:
                st.markdown(f"- [{fonte}]({fonte})")
        else:
            st.info("Nenhuma fonte externa retornada.")

st.divider()
st.caption("Desenvolvido com FastAPI · LangGraph · Streamlit · Groq · Tavily")