import streamlit as st
import requests
import time

st.set_page_config(page_title="Fake News Detector", page_icon="🛡️", layout="wide")

API_URL = "http://127.0.0.1:8000/analisar"

st.title("Fake News Detector")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    texto_input = st.text_area("Insira a notícia para análise:", placeholder="Cole o texto aqui...", height=300)
    botao = st.button("Iniciar Análise")

if botao:
    if len(texto_input) < 20:
        st.error("Por favor, insira um texto com pelo menos 20 caracteres.")
    else:
        with st.spinner("Analisando..."):
            try:
                response = requests.post(API_URL, json={"texto": texto_input})
                data = response.json()
                
                with col2:
                    st.subheader("Veredito Final")
                    veredito = data.get("veredito", "ERRO")
                    
                    cor = {"REAL": "green", "FAKE": "red", "IMPRECISO": "orange"}.get(veredito, "gray")
                    st.markdown(f"<h1 style='text-align: center; color: {cor};'>{veredito}</h1>", unsafe_allow_html=True)
                    
                    st.metric("Confiança da IA", data.get("confianca"))
                    st.caption(f"Tempo de processamento: {data.get('tempo_execucao')}s")

                st.markdown("---")
                
                st.subheader("Justificativa Detalhada")
                for motivo in data.get("motivos_xyz", []):
                    st.write(motivo)

                with st.expander("Fontes Web Consultadas"):
                    for fonte in data.get("fontes_verificadas", []):
                        st.write(f"- {fonte}")

            except Exception as e:
                st.error(f"Erro ao conectar com o backend: {e}")

st.markdown("---")
st.caption("Desenvolvido com FastAPI, LangGraph e Streamlit.")