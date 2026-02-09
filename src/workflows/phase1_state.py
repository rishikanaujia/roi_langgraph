"""
Phase 1 State Definition

Defines the state structure for Phase 1 workflow:
1. Research Loading
2. Expert Presentations
3. Peer Rankings
4. Aggregation

This state is passed between all Phase 1 agents.
"""

from typing import Dict, Any, List, TypedDict, Optional
from datetime import datetime


# ============================================================================
# Phase 1 State
# ============================================================================

class Phase1State(TypedDict, total=False):
    """
    Complete state for Phase 1 workflow.

    Data Flow:
    1. Input: countries, research_data
    2. Research Loading: country_research
    3. Expert Presentations: expert_presentations
    4. Peer Rankings: peer_rankings
    5. Aggregation: aggregated_ranking, final_scores

    All agents read from and write to this shared state.
    """

    # ==================== INPUT ====================
    countries: List[str]  # Country codes to analyze (e.g., ["USA", "IND", "CHN"])
    query: Optional[str]  # Optional natural language query

    # ==================== STAGE 1: RESEARCH LOADING ====================
    research_json_path: Optional[str]  # Path to research JSON file
    research_json_data: Optional[List[Dict[str, str]]]  # Direct research data
    country_research: Dict[str, str]  # Research text by country code
    research_metadata: Dict[str, Any]  # Research loading metadata

    # ==================== STAGE 2: EXPERT PRESENTATIONS ====================
    expert_presentations: Dict[str, Dict[str, Any]]  # Country code -> presentation
    # Structure of each presentation:
    # {
    #   "country_code": "USA",
    #   "expert_id": "expert_usa_1",
    #   "strengths": ["Strong policy support", "High solar resources"],
    #   "weaknesses": ["High labor costs", "Grid constraints"],
    #   "investment_case": "Detailed narrative...",
    #   "key_metrics": {"irr": 12.5, "lcoe": 45.2, "npv": 150000000},
    #   "recommendation": "STRONG BUY",
    #   "confidence": "high"
    # }

    presentation_metadata: Dict[str, Any]  # Presentation generation metadata

    # ==================== STAGE 3: PEER RANKINGS ====================
    peer_rankings: List[Dict[str, Any]]  # Rankings from each peer agent
    # Structure of each peer ranking:
    # {
    #   "peer_id": "peer_ranker_1",
    #   "rankings": [
    #     {"country_code": "USA", "rank": 1, "score": 9.5, "reasoning": "..."},
    #     {"country_code": "IND", "rank": 2, "score": 8.7, "reasoning": "..."},
    #     ...
    #   ],
    #   "methodology": "Weighted scoring across metrics",
    #   "timestamp": "2025-12-07T10:30:00"
    # }

    ranking_metadata: Dict[str, Any]  # Ranking generation metadata

    # ==================== STAGE 4: AGGREGATION ====================
    aggregated_ranking: Dict[str, Any]  # Final consensus ranking
    # Structure:
    # {
    #   "final_rankings": [
    #     {
    #       "rank": 1,
    #       "country_code": "USA",
    #       "consensus_score": 9.2,
    #       "peer_scores": [9.5, 9.0, 9.1],
    #       "score_stddev": 0.25,
    #       "peer_agreement": "high"
    #     },
    #     ...
    #   ],
    #   "methodology": "Borda count + score averaging",
    #   "timestamp": "2025-12-07T10:35:00"
    # }

    consensus_scores: Dict[str, float]  # Country code -> consensus score
    score_variance: Dict[str, float]  # Country code -> score variance
    aggregation_metadata: Dict[str, Any]  # Aggregation stats

    # ==================== EXECUTION METADATA ====================
    execution_metadata: Dict[str, Any]  # Timing, agent calls, etc.
    # Structure:
    # {
    #   "start_time": "2025-12-07T10:00:00",
    #   "end_time": "2025-12-07T10:35:00",
    #   "total_duration_seconds": 2100,
    #   "stage_timings": {
    #     "research": 5.2,
    #     "presentations": 120.5,
    #     "rankings": 180.3,
    #     "aggregation": 2.1
    #   },
    #   "agent_executions": [
    #     {"agent_id": "research_loader_v1", "duration": 5.2, "success": True},
    #     ...
    #   ],
    #   "parallel_efficiency": 0.85  # Speedup from parallelization
    # }

    errors: List[str]  # Any errors encountered
    warnings: List[str]  # Any warnings

    # ==================== DEBUG INFO ====================
    agent_outputs: Dict[str, Any]  # Raw agent outputs for debugging


# ============================================================================
# Helper Functions
# ============================================================================

def create_phase1_state(
        countries: List[str],
        research_json_path: Optional[str] = None,
        research_json_data: Optional[List[Dict[str, str]]] = None,
        query: Optional[str] = None
) -> Phase1State:
    """
    Create initial Phase 1 state.

    Args:
        countries: List of country codes (e.g., ["USA", "IND", "CHN"])
        research_json_path: Optional path to research JSON file
        research_json_data: Optional direct research data
        query: Optional natural language query

    Returns:
        Initialized Phase 1 state

    Example:
        >>> state = create_phase1_state(
        ...     countries=["USA", "IND", "CHN"],
        ...     research_json_path="data/research.json"
        ... )
    """
    state: Phase1State = {
        # Input
        "countries": countries,
        "query": query,

        # Stage 1: Research
        "country_research": {},
        "research_metadata": {},

        # Stage 2: Presentations
        "expert_presentations": {},
        "presentation_metadata": {},

        # Stage 3: Rankings
        "peer_rankings": [],
        "ranking_metadata": {},

        # Stage 4: Aggregation
        "aggregated_ranking": {},
        "consensus_scores": {},
        "score_variance": {},
        "aggregation_metadata": {},

        # Execution
        "execution_metadata": {
            "start_time": datetime.now().isoformat(),
            "stage_timings": {},
            "agent_executions": [],
            "parallel_efficiency": 0.0
        },
        "errors": [],
        "warnings": [],
        "agent_outputs": {}
    }

    # Add research sources if provided
    if research_json_path:
        state["research_json_path"] = research_json_path
    if research_json_data:
        state["research_json_data"] = research_json_data

    return state


def validate_phase1_state(state: Phase1State) -> tuple[bool, List[str]]:
    """
    Validate Phase 1 state structure.

    Args:
        state: Phase 1 state to validate

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        >>> is_valid, errors = validate_phase1_state(state)
        >>> if not is_valid:
        ...     print(f"State validation failed: {errors}")
    """
    errors = []

    # Check required keys
    if "countries" not in state or not state["countries"]:
        errors.append("Missing or empty 'countries' list")

    if "country_research" not in state:
        errors.append("Missing 'country_research' dict")

    if "expert_presentations" not in state:
        errors.append("Missing 'expert_presentations' dict")

    if "peer_rankings" not in state:
        errors.append("Missing 'peer_rankings' list")

    if "aggregated_ranking" not in state:
        errors.append("Missing 'aggregated_ranking' dict")

    # Validate countries are uppercase 3-letter codes
    if "countries" in state:
        for country in state["countries"]:
            if not isinstance(country, str):
                errors.append(f"Country code must be string, got {type(country)}")
            elif len(country) != 3:
                errors.append(f"Country code must be 3 letters, got '{country}'")
            elif not country.isupper():
                errors.append(f"Country code must be uppercase, got '{country}'")

    return len(errors) == 0, errors


def get_stage_progress(state: Phase1State) -> Dict[str, str]:
    """
    Get progress status of each Phase 1 stage.

    Args:
        state: Phase 1 state

    Returns:
        Dict mapping stage name to status (pending/in_progress/complete)

    Example:
        >>> progress = get_stage_progress(state)
        >>> print(progress)
        {
            "research": "complete",
            "presentations": "in_progress",
            "rankings": "pending",
            "aggregation": "pending"
        }
    """
    progress = {
        "research": "pending",
        "presentations": "pending",
        "rankings": "pending",
        "aggregation": "pending"
    }

    # Check research stage
    if state.get("country_research"):
        num_countries = len(state.get("countries", []))
        num_research = len(state["country_research"])

        if num_research == 0:
            progress["research"] = "pending"
        elif num_research < num_countries:
            progress["research"] = "in_progress"
        else:
            progress["research"] = "complete"

    # Check presentations stage
    if state.get("expert_presentations"):
        num_countries = len(state.get("countries", []))
        num_presentations = len(state["expert_presentations"])

        if num_presentations == 0:
            progress["presentations"] = "pending"
        elif num_presentations < num_countries:
            progress["presentations"] = "in_progress"
        else:
            progress["presentations"] = "complete"

    # Check rankings stage
    if state.get("peer_rankings"):
        progress["rankings"] = "complete" if state["peer_rankings"] else "pending"

    # Check aggregation stage
    if state.get("aggregated_ranking"):
        progress["aggregation"] = "complete" if state["aggregated_ranking"] else "pending"

    return progress


def merge_state_updates(
        current_state: Phase1State,
        updates: Dict[str, Any]
) -> Phase1State:
    """
    Merge agent outputs into current state.

    Args:
        current_state: Current state
        updates: Updates from agent execution

    Returns:
        Updated state

    Example:
        >>> new_state = merge_state_updates(
        ...     current_state,
        ...     {"country_research": {"USA": "..."}}
        ... )
    """
    # Create copy to avoid mutation
    new_state = current_state.copy()

    # Merge updates
    for key, value in updates.items():
        if key in new_state:
            # Handle merging of dicts
            if isinstance(new_state[key], dict) and isinstance(value, dict):
                new_state[key] = {**new_state[key], **value}
            # Handle appending to lists
            elif isinstance(new_state[key], list) and isinstance(value, list):
                new_state[key] = new_state[key] + value
            else:
                new_state[key] = value
        else:
            new_state[key] = value

    return new_state


def extract_final_ranking(state: Phase1State) -> List[Dict[str, Any]]:
    """
    Extract final ranking from state in clean format.

    Args:
        state: Phase 1 state with aggregated ranking

    Returns:
        List of ranked countries with scores

    Example:
        >>> ranking = extract_final_ranking(state)
        >>> print(ranking[0])
        {
            "rank": 1,
            "country_code": "USA",
            "score": 9.2,
            "peer_agreement": "high"
        }
    """
    aggregated = state.get("aggregated_ranking", {})

    if not aggregated:
        return []

    final_rankings = aggregated.get("final_rankings", [])

    # Sort by rank
    sorted_rankings = sorted(final_rankings, key=lambda x: x.get("rank", 999))

    return sorted_rankings


def get_country_presentation(
        state: Phase1State,
        country_code: str
) -> Optional[Dict[str, Any]]:
    """
    Get expert presentation for specific country.

    Args:
        state: Phase 1 state
        country_code: Country code (e.g., "USA")

    Returns:
        Presentation dict or None if not found
    """
    presentations = state.get("expert_presentations", {})
    return presentations.get(country_code)


def get_peer_ranking_for_country(
        state: Phase1State,
        country_code: str
) -> List[Dict[str, Any]]:
    """
    Get all peer rankings for specific country.

    Args:
        state: Phase 1 state
        country_code: Country code (e.g., "USA")

    Returns:
        List of rankings from each peer for this country

    Example:
        >>> rankings = get_peer_ranking_for_country(state, "USA")
        >>> for r in rankings:
        ...     print(f"Peer {r['peer_id']}: Rank {r['rank']}, Score {r['score']}")
    """
    peer_rankings = state.get("peer_rankings", [])
    country_rankings = []

    for peer_ranking in peer_rankings:
        peer_id = peer_ranking.get("peer_id")
        rankings = peer_ranking.get("rankings", [])

        for ranking in rankings:
            if ranking.get("country_code") == country_code:
                country_rankings.append({
                    "peer_id": peer_id,
                    "rank": ranking.get("rank"),
                    "score": ranking.get("score"),
                    "reasoning": ranking.get("reasoning", "")
                })

    return country_rankings


# ============================================================================
# State Serialization
# ============================================================================

def state_to_json_safe(state: Phase1State) -> Dict[str, Any]:
    """
    Convert state to JSON-safe format (for API responses).

    Removes internal debug info and simplifies structure.
    """
    return {
        "countries": state.get("countries", []),
        "research_loaded": len(state.get("country_research", {})),
        "presentations_complete": len(state.get("expert_presentations", {})),
        "peer_rankings_count": len(state.get("peer_rankings", [])),
        "final_ranking": extract_final_ranking(state),
        "execution_metadata": state.get("execution_metadata", {}),
        "progress": get_stage_progress(state)
    }