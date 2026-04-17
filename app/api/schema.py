from pydantic import BaseModel, Field, model_validator
from typing import List

class AnalysisRequest(BaseModel):
    texto: str = Field(
        ...,
        min_length=20,
        max_length=5000,
        description="Texto integral da noticia a ser analisada",
        examples=["O governo anunciou que o BNDES perdoou todas as dívidas de Cuba..."],
    )

    @model_validator(mode="after")
    def sanitize_texto(self) -> "AnalysisRequest":
        self.texto = self.texto.strip()
        return self

class AnalysisResponse(BaseModel):
    veredito: str = Field(..., description="Veredito final (REAL, FAKE ou IMPRECISO)")
    confianca: str = Field(..., description="Percentual de confiança da análise")
    justificativas: List[str] = Field(..., description="Lista de motivos técnicos da análise")
    fontes_verificadas: List[str] = Field(..., description="URLs consultados durante a investigação")
    tempo_execucao: float = Field(..., description="Tempo total de processamento em segundos")

    model_config = {"json_schema_extra": {
        "example": {
            "veredito": "FAKE",
            "confianca": "87%",
            "justificativas": ["Nenhuma fonte oficial confirma a notícia."],
            "fontes_verificadas": ["https://exemplo.com"],
            "tempo_execucao": 4.32,
        }
    }}