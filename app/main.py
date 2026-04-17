from __future__ import annotations
import time
from fastapi import FastAPI, HTTPException, Request
from app.api.schema import AnalysisRequest, AnalysisResponse
from app.core.graph import get_engine
import logging
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Aquecendo engine de agentes...")
    get_engine()
    yield
    logger.info("Encerrando aplicação.")


app = FastAPI(
    title="Fake News Detector",
    description="API de análise de desinformação com múltiplos agentes de IA",
    version="2.0.0",
    lifespan=lifespan,
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:8501"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "online", "docs": "/docs"}

@app.post("/analisar", response_model=AnalysisResponse, tags=["Análise"])
async def analisar_noticia(request: AnalysisRequest, req: Request):
    logger.info("Nova análise - IP: %s | chars: %d", req.client.host,len(request.texto))
    inicio = time.perf_counter()

    try:
        initial_state= {
            "texto_original": request.texto,
            "analises_agentes": [],
            "evidencias_web": [],
            "evidencias_csv": None,
            "veredito_final": None,
            "score": None,
        }
    
        resultado = await get_engine().ainvoke(initial_state)

    except Exception as exc:
        logger.exception("Falha no pipeline de agentes: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno no processamento dos agentes")
    
    tempo_total = round(time.perf_counter() - inicio, 2)
    logger.info(
        "Análise concluída - veredito: %s | score: %s | tempo: %ss",
        resultado.get("veredito_final"),
        resultado.get("score"),
        tempo_total,
    )
    
    fontes = [
        f.get("url", "")
        for f in (resultado.get("evidencias_web") or [])
        if isinstance(f, dict) and f.get("url")
    ]
    
    return AnalysisResponse (
            veredito = resultado.get("veredito_final", "IMPRECISO"),
            confianca = f"{resultado.get('score', 0)}%",
            justificativas = resultado.get("analises_agentes", []),
            fontes_verificadas = fontes,
            tempo_execucao = tempo_total,
    )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
