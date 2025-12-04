"""
Shared State Definition

TypedDict defining the complete state passed through the workflow.
"""

from typing import Dict, Any, List, TypedDict, Optional


class WorkflowState(TypedDict, total=False):
    """
    Complete state for the country comparison workflow.
    
    This state is passed between all workflow nodes.
    Each node can read from and write to this state.
    """
    
    # ==================== INPUT ====================
    countries: List[str]  # List of country codes to compare
    query: Optional[str]  # Optional natural language query
    
    # ==================== RESEARCH DATA (NEW) ====================
    research_json_path: Optional[str]  # Path to research JSON file
    research_json_data: Optional[List[Dict[str, str]]]  # Direct research data
    country_research: Dict[str, str]  # Research text by country code
    research_metadata: Dict[str, Any]  # Research loading metadata
    
    # ==================== DATA LOADING ====================
    locations: List[Dict[str, Any]]  # Representative locations
    
    # ==================== ANALYSIS ====================
    location_analyses: List[Dict[str, Any]]  # Analysis for each location
    country_reports: Dict[str, Dict[str, Any]]  # Aggregated by country
    
    # ==================== RANKING ====================
    ranking: Dict[str, Any]  # Current ranking
    verification: Dict[str, Any]  # Verification results
    ranking_iterations: List[Dict[str, Any]]  # History of ranking attempts
    
    # ==================== INSIGHTS (NEW) ====================
    country_insights: Dict[str, Dict[str, Any]]  # Insights per country
    ranking_explanation: Dict[str, Any]  # Ranking explanation
    insights_metadata: Dict[str, Any]  # Insights generation metadata
    
    # ==================== DUAL RECOMMENDATION ====================
    dual_recommendation: Optional[Dict[str, Any]]  # For ambiguous cases
    
    # ==================== METADATA ====================
    execution_metadata: Dict[str, Any]  # Execution timing, agent calls, etc.
    errors: List[str]  # Any errors encountered
    agent_outputs: Dict[str, Any]  # Raw agent outputs for debugging


def create_initial_state(
    countries: List[str],
    query: str = None,
    research_json_path: str = None,
    research_json_data: List[Dict[str, str]] = None
) -> WorkflowState:
    """
    Create initial workflow state.
    
    Args:
        countries: List of country codes to compare
        query: Optional natural language query
        research_json_path: Optional path to research JSON
        research_json_data: Optional direct research data
        
    Returns:
        Initial state dictionary
    """
    state: WorkflowState = {
        "countries": countries,
        "query": query,
        "locations": [],
        "country_research": {},
        "research_metadata": {},
        "location_analyses": [],
        "country_reports": {},
        "ranking": {},
        "verification": {},
        "ranking_iterations": [],
        "country_insights": {},
        "ranking_explanation": {},
        "insights_metadata": {},
        "dual_recommendation": None,
        "execution_metadata": {
            "agent_executions": []
        },
        "errors": [],
        "agent_outputs": {}
    }
    
    # Add research data if provided
    if research_json_path:
        state["research_json_path"] = research_json_path
    if research_json_data:
        state["research_json_data"] = research_json_data
    
    return state
