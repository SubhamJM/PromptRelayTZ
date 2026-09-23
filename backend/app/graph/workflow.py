from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, START, END

from backend.app.graph.nodes import (
    agent_1_extractor,
    agent_2_reconstructor,
    agent_3_detective,
    agent_evaluator,
)
from backend.app.graph.state import GameState


def create_relay_graph(llm: Optional[BaseChatModel] = None):
    """
    Constructs and compiles the 4-stage LangGraph workflow for Prompt Relay:
    START -> agent_1_extractor -> agent_2_reconstructor -> agent_3_detective -> agent_evaluator -> END
    """
    graph = StateGraph(GameState)

    # Wrap nodes with optional custom LLM (e.g. for testing)
    def run_node_1(state: GameState):
        return agent_1_extractor(state, llm=llm)

    def run_node_2(state: GameState):
        return agent_2_reconstructor(state, llm=llm)

    def run_node_3(state: GameState):
        return agent_3_detective(state, llm=llm)

    def run_node_4(state: GameState):
        return agent_evaluator(state)

    # Register Nodes
    graph.add_node("extractor", run_node_1)
    graph.add_node("reconstructor", run_node_2)
    graph.add_node("detective", run_node_3)
    graph.add_node("evaluator", run_node_4)

    # Sequential Edges
    graph.add_edge(START, "extractor")
    graph.add_edge("extractor", "reconstructor")
    graph.add_edge("reconstructor", "detective")
    graph.add_edge("detective", "evaluator")
    graph.add_edge("evaluator", END)

    return graph.compile()
