from typing import TypedDict, Optional, List, Annotated
import operator

class AgentState(TypedDict):
    texto_original: str
    evidencias_csv: Optional[str]
    evidencias_web: Optional[List[dict]]
    analises_agentes: Annotated[List[str], operator.add]
    veredito_final: Optional[str]
    score: Optional[int]