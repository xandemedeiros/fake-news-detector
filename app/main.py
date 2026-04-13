from fastapi import FastAPI
from app.api.schema import AnalysisRequest, AnalysisResponse
from app.core.graph import engine_detect

app = FastAPI(title="Fake News Detector")

@app.post("/analisar", response_model=AnalysisResponse)
async def analisar(request: AnalysisRequest):
    inputs = {"texto_original": request.texto, "analise_xyz": []}
    resultado = await engine_detect.ainvoke(inputs)
    
    return {
        "veredito": resultado["veredito_final"],
        "confianca": f"{resultado['score']}%",
        "motivos": resultado["analise_xyz"],
        "fontes": [f["url"] for f in resultado.get("evidencias_web", [])]
    }