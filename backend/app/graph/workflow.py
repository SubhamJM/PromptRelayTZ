from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, START, END

from backend.app.graph.nodes import (
    node_extractor,
    node_reconstructor,
    node_solver,
    node_evaluator,
)
from backend.app.graph.state import RelayState


def create_relay_workflow(llm: Optional[BaseChatModel] = None):
    """
    Builds and compiles the full sequential LangGraph StateGraph:
    START -> extractor -> reconstructor -> solver -> evaluator -> END
    """
    graph = StateGraph(RelayState)

    def run_extractor(state: RelayState):
        return node_extractor(state, llm=llm)

    def run_reconstructor(state: RelayState):
        return node_reconstructor(state, llm=llm)

    def run_solver(state: RelayState):
        return node_solver(state, llm=llm)

    def run_evaluator(state: RelayState):
        return node_evaluator(state)

    graph.add_node("extractor", run_extractor)
    graph.add_node("reconstructor", run_reconstructor)
    graph.add_node("solver", run_solver)
    graph.add_node("evaluator", run_evaluator)

    graph.add_edge(START, "extractor")
    graph.add_edge("extractor", "reconstructor")
    graph.add_edge("reconstructor", "solver")
    graph.add_edge("solver", "evaluator")
    graph.add_edge("evaluator", END)

    return graph.compile()


create_relay_graph = create_relay_workflow
