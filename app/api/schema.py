from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    texto: str

class AnalysisResponse(BaseModel):
    veredito: str
    confianca: str
    motivos: list
    fontes: list