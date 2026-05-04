"""Main Agent - NovaHR LangGraph Pipeline"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.main_agent.router import build_graph, State

# Compile graph once at import time
graph = build_graph()


def run_main_agent(state: dict) -> dict:
    """
    Run the NovaHR main agent pipeline.
    
    Takes a state dict and returns updated state dict.
    """
    result = graph.invoke(state)
    return result


__all__ = ["graph", "run_main_agent", "State"]
