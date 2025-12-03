"""
Analysis Team Agents

Example: How the Analysis Team can integrate their LangGraph agents.
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability
from src.adapters.langgraph_adapter import wrap_langgraph_agent


# ============ EXAMPLE 1: LangGraph Multi-Step Analysis ============

class AnalysisState(TypedDict):
    """State for analysis workflow."""
    location: Dict[str, Any]
    irr: float
    lcoe: float
    npv: float
    status: str


def calculate_irr(state: AnalysisState) -> Dict[str, Any]:
    """Calculate IRR."""
    # In real system, complex financial calculations
    return {"irr": 5.5, "status": "irr_calculated"}


def calculate_lcoe(state: AnalysisState) -> Dict[str, Any]:
    """Calculate LCOE."""
    return {"lcoe": 65.0, "status": "lcoe_calculated"}


def calculate_npv(state: AnalysisState) -> Dict[str, Any]:
    """Calculate NPV."""
    return {"npv": -50000000, "status": "npv_calculated"}


def create_financial_analysis_graph():
    """
    Analysis team's LangGraph for financial calculations.

    This graph:
    1. Calculates IRR
    2. Calculates LCOE
    3. Calculates NPV
    """

    workflow = StateGraph(AnalysisState)

    # Add nodes
    workflow.add_node("calculate_irr", calculate_irr)
    workflow.add_node("calculate_lcoe", calculate_lcoe)
    workflow.add_node("calculate_npv", calculate_npv)

    # Define flow
    workflow.set_entry_point("calculate_irr")
    workflow.add_edge("calculate_irr", "calculate_lcoe")
    workflow.add_edge("calculate_lcoe", "calculate_npv")
    workflow.add_edge("calculate_npv", END)

    return workflow.compile()


# Register LangGraph agent
analysis_graph = create_financial_analysis_graph()
wrapped_analysis = wrap_langgraph_agent(
    analysis_graph,
    state_mapping={"current_location": "location"},
    output_mapping={"irr": "irr", "lcoe": "lcoe", "npv": "npv"}
)

register_agent(
    agent_id="analysis_team_financial_langgraph_v1",
    name="Financial Analysis (LangGraph)",
    description="Calculates IRR, LCOE, NPV using LangGraph workflow",
    framework=AgentFramework.LANGGRAPH,
    capabilities=[AgentCapability.ANALYSIS],
    business_unit="analysis_team",
    contact="analysis@company.com",
    required_inputs=["current_location"],
    output_keys=["irr", "lcoe", "npv"]
)(wrapped_analysis)

print("✅ Analysis Team agents registered!")