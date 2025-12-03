"""
Shared State Definition

Defines the LangGraph state structure used across all agents.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add
from pydantic import BaseModel, Field


class WorkflowState(TypedDict):
    """
    Main workflow state used by LangGraph.
    
    This state is shared across all agents in the workflow.
    """
    
    # Input parameters
    countries: List[str]
    query: Optional[str]
    
    # Location data
    locations: List[Dict[str, Any]]  # ← ADD THIS LINE
    
    # Analysis results (accumulated)
    location_analyses: Annotated[List[Dict[str, Any]], add]
    country_reports: Dict[str, Dict[str, Any]]
    
    # Ranking and verification
    ranking: Optional[Dict[str, Any]]
    verification: Optional[Dict[str, Any]]
    ranking_iterations: Annotated[List[Dict[str, Any]], add]
    
    # Dual recommendation
    dual_recommendation: Optional[Dict[str, Any]]
    
    # Execution metadata
    execution_metadata: Dict[str, Any]
    errors: Annotated[List[str], add]
    
    # Agent outputs
    agent_outputs: Dict[str, Any]


class CountryAnalysisRequest(BaseModel):
    """Request model for country comparison."""
    
    countries: List[str] = Field(
        description="List of country codes",
        min_items=2,
        max_items=10
    )
    
    query: Optional[str] = Field(
        default=None,
        description="Optional query"
    )
    
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional config"
    )


class CountryAnalysisResponse(BaseModel):
    """Response model."""
    
    summary: Dict[str, Any]
    country_reports: Dict[str, Dict[str, Any]]
    ranking: Dict[str, Any]
    verification: Dict[str, Any]
    dual_recommendation: Optional[Dict[str, Any]]
    ranking_iterations: List[Dict[str, Any]]
    execution_metadata: Dict[str, Any]


def create_initial_state(
    countries: List[str],
    query: Optional[str] = None
) -> WorkflowState:
    """Create initial workflow state."""
    return {
        "countries": countries,
        "query": query,
        "locations": [],  # ← ADD THIS LINE
        "location_analyses": [],
        "country_reports": {},
        "ranking": None,
        "verification": None,
        "ranking_iterations": [],
        "dual_recommendation": None,
        "execution_metadata": {
            "start_time": None,
            "end_time": None,
            "agent_executions": []
        },
        "errors": [],
        "agent_outputs": {}
    }


def merge_state_updates(
    current_state: WorkflowState,
    updates: Dict[str, Any]
) -> WorkflowState:
    """Merge updates into current state."""
    new_state = current_state.copy()
    
    for key, value in updates.items():
        if key in new_state:
            existing = new_state[key]
            
            # Lists with 'add' annotation - append
            if isinstance(existing, list) and isinstance(value, list):
                new_state[key] = existing + value
            
            # Dicts - merge
            elif isinstance(existing, dict) and isinstance(value, dict):
                new_state[key] = {**existing, **value}
            
            # Everything else - replace
            else:
                new_state[key] = value
        else:
            # New key
            new_state[key] = value
    
    return new_state


# State accessor helpers
def get_country_report(state: WorkflowState, country_code: str) -> Optional[Dict[str, Any]]:
    """Get report for specific country."""
    return state.get("country_reports", {}).get(country_code)


def add_location_analysis(state: WorkflowState, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Add a location analysis to state."""
    return {"location_analyses": [analysis]}


def add_error(state: WorkflowState, error: str) -> Dict[str, Any]:
    """Add an error to state."""
    return {"errors": [error]}


def log_agent_execution(
    state: WorkflowState,
    agent_id: str,
    execution_time: float,
    success: bool
) -> Dict[str, Any]:
    """Log agent execution in metadata."""
    execution_log = {
        "agent_id": agent_id,
        "execution_time": execution_time,
        "success": success
    }
    
    current_metadata = state.get("execution_metadata", {})
    agent_executions = current_metadata.get("agent_executions", [])
    agent_executions.append(execution_log)
    
    return {
        "execution_metadata": {
            **current_metadata,
            "agent_executions": agent_executions
        }
    }
