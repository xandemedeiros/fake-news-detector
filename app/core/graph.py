from __future__ import annotations
from functools import lru_cache
from langgraph.graph import StateGraph, END
from app.core.agents import investigador, defensor, juiz
from app.core.state import AgentState
import logging

logger = logging.getLogger(__name__)

def _build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    workflow.add_node("investigador", investigador)
    workflow.add_node("defensor", defensor)
    workflow.add_node("juiz", juiz)
    
    workflow.set_entry_point("investigador")
    workflow.add_edge("investigador", "defensor")
    workflow.add_edge("defensor", "juiz")
    workflow.add_edge("juiz", END)
    
    return workflow.compile()

@lru_cache(maxsize=1)
def get_engine():
    logger.info("Compilando grafo de agentes...")
    engine = _build_graph()
    logger.info("Grafo compilado com sucesso.")
    return engine