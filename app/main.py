import time
from fastapi import FastAPI, HTTPException
from app.api.schema import AnalysisRequest, AnalysisResponse
from app.core.graph import engine_detect

app = FastAPI(
    title="Fake News Detector",
    description="API de análise de desinformação baseada em múltiplos agentes de IA",
    version="1.0.0"
    )

@app.get("/")
def read_root():
    return {"message": "Fake News Detector API is online", "docs": "/docs"}

@app.post("/analisar", response_model=AnalysisResponse)
async def analisar_noticia(request: AnalysisRequest):
    inicio_processamento = time.time()

    try:
        initial_state= {
            "texto_original": request.texto,
            "analise_xyz": [],
            "evidencias_web": [],
            "passo_atual": "inicio"
        }
    
        resultado = await engine_detect.ainvoke(initial_state)
        tempo_total = round(time.time() - inicio_processamento, 2)
    
        return {
            "veredito": resultado.get("veredito_final", "NÃO IDENTIFICADO"),
            "confianca": f"{resultado.get('score', 0)}%",
            "motivos_xyz": resultado.get("analise_xyz", []),
            "fontes_verificadas": [f.get('url') for f in resultado.get('evidencias_web', []) if isinstance(f, dict) and f.get('url')],
            "tempo_execucao": tempo_total
        }
    
    except Exception as e:
        print(f"Erro interno: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento dos agentes.")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
