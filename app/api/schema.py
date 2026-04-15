from pydantic import BaseModel, Field
from typing import List, Optional

class AnalysisRequest(BaseModel):
    texto: str = Field(
        ...,
        min_length=20,
        description="O texto integral da noticia a ser analisada",
        example="O governo acaba de anunciar que o BNDES perdoou todas as dívidas de Cuba..."
    )

class AnalysisResponse(BaseModel):
    veredito: str = Field(..., description="Veredito final (REAL, FAKE ou IMPRECISO)")
    confianca: str = Field(..., description="Percentual de confiança da análise")
    motivos_xyz: List[str] = Field(..., description="Lista de motivos técnicos da análise")
    fontes_verificadas: List[str] = Field(..., description="URLs encontrados durante a investigação")
    tempo_execucao: float = Field(..., description="Tempo total em segundos")