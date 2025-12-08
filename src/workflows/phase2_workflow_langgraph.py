"""
Phase 2 LangGraph Workflow

Complete workflow implementation including:
- Phase 1 stages (research, presentations, rankings, aggregation)
- Conditional debate triggering based on consensus level
- Hot seat debate execution when consensus is low/medium
- Final ranking with debate verdict applied
- Executive report generation with debate summary

Author: Kanauija
Date: 2024-12-08
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, TypedDict
from pathlib import Path

from langgraph.graph import StateGraph, END

# Business unit imports
from business_units.data_team.research_loader import load_research_from_json
from business_units.expert_team.expert_agents import execute_experts_parallel
from business_units.ranking_team.peer_ranking_agents import execute_peer_rankers_parallel
from business_units.ranking_team.aggregation_logic import aggregate_peer_rankings
from business_units.ranking_team.hot_seat_debate import HotSeatDebate, should_trigger_debate
from business_units.insights_team.report_generator import generate_executive_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Phase2WorkflowLangGraph")


# State Definition
# ============================================================================

class Phase2State(TypedDict, total=False):
    """
    State for Phase 2 LangGraph workflow.

    Input Parameters:
    -----------------
    countries: List of country codes to analyze
    num_peer_rankers: Number of peer rankers to create
    research_json_data: Pre-generated research data (optional)
    debate_enabled: Whether to enable hot seat debate
    debate_threshold: Threshold for triggering debate (very_high, high, medium, low)
    num_challengers: Number of challengers in debate

    Phase 1 Outputs:
    ----------------
    country_research: Research data for each country
    expert_presentations: Expert analysis presentations
    peer_rankings: Individual peer ranker rankings
    aggregated_ranking: Consensus ranking from aggregation

    Phase 2 Outputs:
    ----------------
    debate_triggered: Whether debate was actually triggered
    debate_result: Results from hot seat debate (if triggered)
    final_ranking: Final ranking after debate (if applicable)

    Report:
    -------
    report_markdown: Generated markdown report
    report_metadata: Report metadata (filepath, etc.)

    Metadata:
    ---------
    errors: List of errors encountered
    stage_timings: Dict of timing for each stage
    total_duration: Total execution time
    """
    # Input parameters
    countries: List[str]
    num_peer_rankers: int
    research_json_data: Optional[Dict[str, Any]]
    debate_enabled: bool
    debate_threshold: str
    num_challengers: int

    # Phase 1 outputs
    country_research: Dict[str, Any]
    expert_presentations: Dict[str, Any]
    peer_rankings: List[Dict[str, Any]]
    aggregated_ranking: Dict[str, Any]

    # Phase 2 outputs
    debate_triggered: bool
    debate_result: Optional[Dict[str, Any]]
    final_ranking: List[Dict[str, Any]]

    # Report
    report_markdown: str
    report_metadata: Dict[str, Any]

    # Metadata
    errors: List[str]
    stage_timings: Dict[str, float]
    total_duration: float


# Node Functions
# ============================================================================

async def load_research_node(state: Phase2State) -> Dict[str, Any]:
    """Load research data from JSON (or use provided data)."""
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("STAGE 1: RESEARCH LOADING")
    logger.info("=" * 70)

    research_json_data = state.get("research_json_data")

    # Load research data
    country_research = load_research_from_json(json_data=research_json_data)

    duration = time.time() - start_time

    logger.info(f"✅ Stage 1 complete in {duration:.2f}s")
    logger.info(f"   Loaded research for {len(country_research)} countries")
    logger.info("")

    return {
        "country_research": country_research,
        "stage_timings": {"research": duration}
    }


async def generate_presentations_node(state: Phase2State) -> Dict[str, Any]:
    """Generate expert presentations for each country (parallel execution)."""
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("STAGE 2: EXPERT PRESENTATIONS (PARALLEL)")
    logger.info("=" * 70)

    logger.info(f"🚀 Creating {len(state['countries'])} expert agents...")

    # Pass state directly (like Phase 1 does)
    result = await execute_experts_parallel(
        state=state,
        countries=state["countries"]
    )

    # Get presentations from result
    presentations_data = result.get("expert_presentations", {})

    # Check if it's a list or dict and convert if needed
    if isinstance(presentations_data, list):
        # Convert list to dict for peer rankers
        expert_presentations = {
            pres["country_code"]: pres
            for pres in presentations_data
        }
    else:
        # Already a dict
        expert_presentations = presentations_data

    duration = time.time() - start_time

    logger.info(f"✅ Stage 2 complete in {duration:.2f}s")
    logger.info(f"   Generated {len(expert_presentations)} presentations")
    logger.info("")

    # Handle errors
    errors = result.get("errors", [])
    if errors:
        return {
            "expert_presentations": expert_presentations,
            "errors": errors,
            "stage_timings": {"presentations": duration}
        }

    return {
        "expert_presentations": expert_presentations,
        "stage_timings": {"presentations": duration}
    }


async def generate_rankings_node(state: Phase2State) -> Dict[str, Any]:
    """Generate peer rankings from expert presentations (parallel execution)."""
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("STAGE 3: PEER RANKINGS (PARALLEL)")
    logger.info("=" * 70)

    num_peer_rankers = state["num_peer_rankers"]

    logger.info(f"🚀 Creating {num_peer_rankers} peer ranker agents...")

    # Pass state directly (like Phase 1 does)
    result = await execute_peer_rankers_parallel(
        state=state,
        num_peers=num_peer_rankers
    )

    # Get rankings from result
    rankings_list = result.get("peer_rankings", [])

    duration = time.time() - start_time

    logger.info(f"✅ Stage 3 complete in {duration:.2f}s")
    logger.info(f"   Collected {len(rankings_list)} peer rankings")
    logger.info("")

    # Handle errors
    errors = result.get("errors", [])
    if errors:
        return {
            "peer_rankings": rankings_list,
            "errors": errors,
            "stage_timings": {"rankings": duration}
        }

    return {
        "peer_rankings": rankings_list,
        "stage_timings": {"rankings": duration}
    }


async def aggregate_rankings_node(state: Phase2State) -> Dict[str, Any]:
    """Aggregate peer rankings into consensus ranking."""
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("STAGE 4: RANKING AGGREGATION")
    logger.info("=" * 70)

    peer_rankings = state["peer_rankings"]

    try:
        # Aggregate rankings - use 'method' not 'aggregation_method'
        aggregated_ranking = aggregate_peer_rankings(
            peer_rankings=peer_rankings,
            method="hybrid"
        )

        duration = time.time() - start_time

        logger.info(f"✅ Stage 4 complete in {duration:.2f}s")
        logger.info(f"   Aggregated {len(peer_rankings)} rankings")
        logger.info(f"   Consensus level: {aggregated_ranking.get('consensus_level', 'unknown')}")
        logger.info("")

        return {
            "aggregated_ranking": aggregated_ranking,
            "stage_timings": {"aggregation": duration}
        }

    except Exception as e:
        logger.error(f"Aggregation failed: {str(e)}")
        duration = time.time() - start_time

        return {
            "aggregated_ranking": None,
            "errors": [f"Aggregation error: {str(e)}"],
            "stage_timings": {"aggregation": duration}
        }


async def hot_seat_debate_node(state: Phase2State) -> Dict[str, Any]:
    """
    Execute hot seat debate (if triggered).

    The debate is only executed if:
    1. Debate is enabled
    2. At least 2 countries exist
    3. Consensus is below threshold

    Otherwise, this node just sets final_ranking = aggregated_ranking
    """
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("STAGE 5: HOT SEAT DEBATE (CONDITIONAL)")
    logger.info("=" * 70)

    # Check if we should actually run debate
    debate_enabled = state.get("debate_enabled", True)
    aggregated_ranking = state.get("aggregated_ranking")

    # Safety check
    if aggregated_ranking is None:
        logger.error("⚠️  Aggregation failed - skipping debate")
        duration = time.time() - start_time

        return {
            "debate_triggered": False,
            "debate_result": None,
            "final_ranking": [],
            "stage_timings": {"debate": duration}
        }

    final_rankings = aggregated_ranking.get("final_rankings", [])
    debate_threshold = state.get("debate_threshold", "high")

    # Check if debate should be triggered
    should_debate = (
            debate_enabled and
            len(final_rankings) >= 2 and
            should_trigger_debate(aggregated_ranking, threshold=debate_threshold)
    )

    if not should_debate:
        logger.info("⏭️  Debate not triggered - using aggregated ranking")
        duration = time.time() - start_time

        return {
            "debate_triggered": False,
            "debate_result": None,
            "final_ranking": final_rankings,
            "stage_timings": {"debate": duration}
        }

    # Execute debate
    logger.info("🔥 Executing hot seat debate...")

    try:
        # Get top 2 countries
        top_ranked = final_rankings[0]
        runner_up = final_rankings[1]

        # Execute debate
        debate = HotSeatDebate()
        num_challengers = state.get("num_challengers", 2)

        # Convert expert_presentations dict to list for debate
        expert_presentations_list = [
            pres for pres in state["expert_presentations"].values()
        ]

        debate_result = await debate.execute_debate(
            top_ranked_country=top_ranked,
            runner_up_country=runner_up,
            expert_presentations=expert_presentations_list,
            peer_rankings=state["peer_rankings"],
            num_challengers=num_challengers
        )

        # Apply verdict to final ranking
        verdict = debate_result["verdict"]

        if verdict == "OVERTURNED":
            logger.info("🔄 Verdict: OVERTURNED - Swapping top 2 positions")

            # Swap top 2 positions
            final_ranking = final_rankings.copy()
            final_ranking[0], final_ranking[1] = final_ranking[1], final_ranking[0]

            # Update ranks
            final_ranking[0]["rank"] = 1
            final_ranking[1]["rank"] = 2

            # Add debate markers
            final_ranking[0]["debate_winner"] = True
            final_ranking[1]["debate_loser"] = True

        else:
            logger.info("✅ Verdict: UPHELD - Maintaining original ranking")
            final_ranking = final_rankings

            # Add debate markers
            final_ranking[0]["debate_winner"] = True
            final_ranking[1]["debate_challenger"] = True

        duration = time.time() - start_time

        logger.info(f"✅ Stage 5 complete in {duration:.2f}s")
        logger.info(f"   Debate verdict: {verdict}")
        logger.info(f"   Final top country: {final_ranking[0]['country_code']}")
        logger.info("")

        return {
            "debate_triggered": True,
            "debate_result": debate_result,
            "final_ranking": final_ranking,
            "stage_timings": {"debate": duration}
        }

    except Exception as e:
        logger.error(f"Debate execution failed: {str(e)}")
        duration = time.time() - start_time

        # Fallback to original ranking
        return {
            "debate_triggered": True,
            "debate_result": {"error": str(e)},
            "final_ranking": final_rankings,
            "errors": [f"Debate error: {str(e)}"],
            "stage_timings": {"debate": duration}
        }


async def generate_report_node(state: Phase2State) -> Dict[str, Any]:
    """Generate executive report with all results."""
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("STAGE 6: REPORT GENERATION")
    logger.info("=" * 70)

    # Prepare report state
    report_state = {
        "countries": state["countries"],
        "expert_presentations": state["expert_presentations"],
        "peer_rankings": state["peer_rankings"],
        "aggregated_ranking": state.get("aggregated_ranking"),
        "final_ranking": state.get("final_ranking", []),
        "debate_triggered": state.get("debate_triggered", False),
        "debate_result": state.get("debate_result"),
        "stage_timings": state.get("stage_timings", {})
    }

    # Generate report
    report_result = generate_executive_report(report_state)

    duration = time.time() - start_time

    logger.info(f"✅ Stage 6 complete in {duration:.2f}s")
    logger.info(f"   Report saved to: {report_result['report_metadata']['filepath']}")
    logger.info("")

    return {
        "report_markdown": report_result["report_markdown"],
        "report_metadata": report_result["report_metadata"],
        "stage_timings": {"report": duration}
    }


# Conditional Edge Function
# ============================================================================

def should_debate(state: Phase2State) -> str:
    """
    Conditional edge: Decide whether to trigger debate or go straight to report.

    Debate is triggered when:
    1. Debate is enabled
    2. At least 2 countries exist (need a runner-up)
    3. Consensus level is below the threshold
    """
    # Check if debate is enabled
    if not state.get("debate_enabled", True):
        logger.info("⏭️  Debate disabled - proceeding to report")
        return "report"

    # Safety check for None
    aggregated_ranking = state.get("aggregated_ranking")
    if aggregated_ranking is None:
        logger.error("⚠️  Aggregation failed - skipping debate")
        return "report"

    # Get final rankings
    final_rankings = aggregated_ranking.get("final_rankings", [])

    # Need at least 2 countries for debate
    if len(final_rankings) < 2:
        logger.info("⏭️  Less than 2 countries - skipping debate")
        return "report"

    # Check if debate should be triggered based on consensus
    debate_threshold = state.get("debate_threshold", "high")

    if should_trigger_debate(aggregated_ranking, threshold=debate_threshold):
        logger.info(f"🔥 Debate triggered! (threshold: {debate_threshold})")
        return "debate"
    else:
        logger.info(f"⏭️  Consensus sufficient - skipping debate (threshold: {debate_threshold})")
        return "report"


# Workflow Builder
# ============================================================================

def build_phase2_workflow() -> StateGraph:
    """
    Build Phase 2 LangGraph workflow with conditional debate.

    Workflow structure:
    -------------------
    START → research → presentations → rankings → aggregation
                                                      ↓
                                                [CONDITIONAL]
                                                /           \
                                           debate         report
                                              ↓              ↓
                                           report          END
    """
    # Create workflow
    workflow = StateGraph(Phase2State)

    # Add nodes
    workflow.add_node("research", load_research_node)
    workflow.add_node("presentations", generate_presentations_node)
    workflow.add_node("rankings", generate_rankings_node)
    workflow.add_node("aggregation", aggregate_rankings_node)
    workflow.add_node("debate", hot_seat_debate_node)
    workflow.add_node("report", generate_report_node)

    # Add edges
    workflow.set_entry_point("research")
    workflow.add_edge("research", "presentations")
    workflow.add_edge("presentations", "rankings")
    workflow.add_edge("rankings", "aggregation")

    # Add conditional edge
    workflow.add_conditional_edges(
        "aggregation",
        should_debate,
        {
            "debate": "debate",
            "report": "report"
        }
    )

    # Connect debate to report
    workflow.add_edge("debate", "report")

    # Set finish point
    workflow.add_edge("report", END)

    return workflow


# Main Execution Function
# ============================================================================

async def run_phase2_langgraph(
        countries: List[str],
        research_json_data: Optional[Dict[str, Any]] = None,
        num_peer_rankers: int = 3,
        debate_enabled: bool = True,
        debate_threshold: str = "high",
        num_challengers: int = 2
) -> Dict[str, Any]:
    """
    Execute complete Phase 2 workflow using LangGraph.

    Parameters:
    -----------
    countries : List[str]
        List of country codes to analyze
    research_json_data : Optional[Dict[str, Any]]
        Pre-generated research data (if None, will be loaded from storage)
    num_peer_rankers : int
        Number of peer rankers to create (default: 3)
    debate_enabled : bool
        Whether to enable hot seat debate (default: True)
    debate_threshold : str
        Threshold for triggering debate (default: "high")
        Options: "very_high", "high", "medium", "low"
    num_challengers : int
        Number of challengers in debate (default: 2)

    Returns:
    --------
    Dict[str, Any]
        Complete workflow results including:
        - expert_presentations: Expert analysis for each country
        - peer_rankings: Individual peer ranker rankings
        - aggregated_ranking: Consensus ranking
        - debate_triggered: Whether debate was executed
        - debate_result: Debate results (if triggered)
        - final_ranking: Final ranking after debate
        - report_markdown: Generated markdown report
        - report_metadata: Report metadata
        - execution_metadata: Timing and execution details
        - errors: Any errors encountered
    """
    start_time = time.time()

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 2 LANGGRAPH WORKFLOW - STARTING")
    logger.info("=" * 70)
    logger.info(f"Countries: {countries}")
    logger.info(f"Peer rankers: {num_peer_rankers}")
    logger.info(f"Debate enabled: {debate_enabled}")
    logger.info(f"Debate threshold: {debate_threshold}")
    logger.info(f"Number of challengers: {num_challengers}")

    # Build workflow
    workflow = build_phase2_workflow()
    compiled_workflow = workflow.compile()

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 2 LANGGRAPH WORKFLOW COMPILED")
    logger.info("=" * 70)
    logger.info("Nodes: 6 (research, presentations, rankings, aggregation, debate, report)")
    logger.info(f"Conditional logic: Debate triggered if agreement < {debate_threshold}")
    logger.info("Execution mode: Async with parallel stages")
    logger.info("=" * 70)

    # Create initial state
    initial_state: Phase2State = {
        "countries": countries,
        "num_peer_rankers": num_peer_rankers,
        "research_json_data": research_json_data,
        "debate_enabled": debate_enabled,
        "debate_threshold": debate_threshold,
        "num_challengers": num_challengers,
        "errors": [],
        "stage_timings": {}
    }

    # Execute workflow
    final_state = await compiled_workflow.ainvoke(initial_state)

    # Calculate total duration
    total_duration = time.time() - start_time

    # Merge all stage timings
    all_timings = {}
    for timing_dict in final_state.get("stage_timings", []):
        if isinstance(timing_dict, dict):
            all_timings.update(timing_dict)

    # Build execution metadata
    execution_metadata = {
        "total_duration_seconds": total_duration,
        "stage_timings": all_timings,
        "num_countries": len(countries),
        "num_peer_rankers": num_peer_rankers,
        "debate_enabled": debate_enabled,
        "debate_threshold": debate_threshold,
        "debate_triggered": final_state.get("debate_triggered", False),
        "num_challengers": num_challengers if final_state.get("debate_triggered") else 0
    }

    logger.info("=" * 70)
    logger.info("PHASE 2 LANGGRAPH WORKFLOW - COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total duration: {total_duration:.2f}s")
    logger.info(f"Debate triggered: {execution_metadata['debate_triggered']}")
    logger.info(f"Final ranking: {len(final_state.get('final_ranking', []))} countries")
    logger.info("=" * 70)
    logger.info("")

    # Return complete results
    return {
        # Phase 1 outputs
        "expert_presentations": final_state.get("expert_presentations", {}),
        "peer_rankings": final_state.get("peer_rankings", []),
        "aggregated_ranking": final_state.get("aggregated_ranking", {}),

        # Phase 2 outputs
        "debate_triggered": final_state.get("debate_triggered", False),
        "debate_result": final_state.get("debate_result"),
        "final_ranking": final_state.get("final_ranking", []),

        # Report
        "report_markdown": final_state.get("report_markdown", ""),
        "report_metadata": final_state.get("report_metadata", {}),

        # Metadata
        "execution_metadata": execution_metadata,
        "errors": final_state.get("errors", [])
    }


# Test/Demo Function
# ============================================================================

async def demo_phase2_workflow():
    """Demo function to test Phase 2 workflow."""
    from api.services.research_service import generate_research_data

    print("\n" + "=" * 70)
    print("PHASE 2 LANGGRAPH WORKFLOW - DEMO")
    print("=" * 70)

    # Generate research data
    print("\n📊 Generating research data...")
    research_data = generate_research_data(["USA", "CHN", "IND"])

    # Run workflow
    print("\n🚀 Running Phase 2 workflow...")
    result = await run_phase2_langgraph(
        countries=["USA", "CHN", "IND"],
        research_json_data=research_data,
        num_peer_rankers=3,
        debate_enabled=True,
        debate_threshold="high",
        num_challengers=2
    )

    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\nExpert Presentations: {len(result['expert_presentations'])}")
    print(f"Peer Rankings: {len(result['peer_rankings'])}")
    print(f"Debate Triggered: {result['debate_triggered']}")

    if result['debate_triggered']:
        print(f"Debate Verdict: {result['debate_result']['verdict']}")

    print(f"\nFinal Ranking:")
    for r in result['final_ranking']:
        print(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")

    print(f"\nReport: {result['report_metadata']['filepath']}")
    print(f"Total Duration: {result['execution_metadata']['total_duration_seconds']:.2f}s")

    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_phase2_workflow())