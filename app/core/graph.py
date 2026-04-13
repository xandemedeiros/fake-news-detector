from langgraph.graph import StateGraph, END
from app.core.agents import investigador, defensor, juiz
from app.core.state import AgentState

def build_engine():
    workflow = StateGraph(AgentState)
    workflow.add_node("investigador", investigador)
    workflow.add_node("defensor", defensor)
    workflow.add_node("juiz", juiz)
    
    workflow.set_entry_point("investigador")
    workflow.add_edge("investigador", "defensor")
    workflow.add_edge("defensor", "juiz")
    workflow.add_edge("juiz", END)
    
    return workflow.compile()

engine_detect = build_engine()