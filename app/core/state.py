from typing import TypedDict, Optional, List, Annotated
import operator

class AgentState(TypedDict):
    texto_original: str
    evidencias_csv: Optional[str]
    evidencias_web: Optional[List[dict]]
    analise_xyz: Annotated[List[str], operator.add]
    veredito_final: Optional[str]
    score: int
    passo_atual: str