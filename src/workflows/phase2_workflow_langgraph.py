"""
Phase 2 LangGraph Workflow with Hot Seat Debate

Extends Phase 1 workflow by adding a conditional hot seat debate stage.
When consensus on top-ranked country is low/medium, triggers a debate where
challengers argue for the runner-up country.

Workflow Flow:
1. Load Research → 2. Expert Presentations → 3. Peer Rankings →
4. Aggregate Rankings → 5. [CONDITIONAL] Hot Seat Debate → 6. Re-aggregate (if needed) →
7. Generate Report

Key Enhancements:
- Conditional debate triggering based on agreement level
- Re-aggregation after debate (if ranking overturned)
- Enhanced report with debate summary
- Configurable debate parameters

Author: Kanauija
Date: 2024-12-08
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, TypedDict, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END

# Import Phase 1 components - USE FUNCTIONS NOT CLASSES
from business_units.data_team.research_loader import load_research_from_json
from business_units.expert_team.expert_agents import execute_experts_parallel
from business_units.ranking_team.peer_ranking_agents import execute_peer_rankers_parallel
from business_units.ranking_team.aggregation_logic import aggregate_peer_rankings
from business_units.insights_team.report_generator import generate_executive_report

# Import Phase 2 hot seat debate
from business_units.ranking_team.hot_seat_debate import (
    execute_hot_seat_debate,
    should_trigger_debate
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Phase2WorkflowLangGraph")


# State Definition
class Phase2State(TypedDict):
    """
    State for Phase 2 LangGraph workflow.

    Extends Phase 1 state with debate-related fields.
    """
    # Input parameters
    countries: List[str]
    num_peer_rankers: int
    research_data: Optional[List[Dict[str, str]]]
    debate_enabled: bool
    debate_threshold: str  # "very_high", "high", "medium", "low"
    num_challengers: int

    # Phase 1 outputs
    country_research: Optional[Dict[str, str]]
    expert_presentations: Optional[Dict[str, Any]]
    peer_rankings: Optional[List[Dict[str, Any]]]
    aggregated_ranking: Optional[Dict[str, Any]]

    # Phase 2 debate outputs
    debate_triggered: bool
    debate_result: Optional[Dict[str, Any]]
    final_ranking: Optional[List[Dict[str, Any]]]

    # Report outputs
    report_markdown: Optional[str]
    report_metadata: Optional[Dict[str, Any]]

    # Execution metadata
    errors: List[str]
    stage_timings: Dict[str, float]
    total_duration: Optional[float]


# Node Functions
# ============================================================================

def load_research_node(state: Phase2State) -> Dict[str, Any]:
    """Load research data for all countries."""
    logger.info("=" * 70)
    logger.info("STAGE 1: RESEARCH LOADING")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        # Get research data (either provided or empty)
        research_json = state.get("research_data")

        if research_json:
            # Use provided research data
            country_research = load_research_from_json(research_json)
        else:
            # No research provided - will be empty
            country_research = {}

        duration = time.time() - start_time

        logger.info(f"✅ Stage 1 complete in {duration:.2f}s")
        logger.info(f"   Loaded research for {len(country_research)} countries")

        return {
            "country_research": country_research,
            "stage_timings": {**state.get("stage_timings", {}), "research": duration}
        }

    except Exception as e:
        logger.error(f"Research loading failed: {str(e)}")
        return {
            "errors": state.get("errors", []) + [f"Research loading: {str(e)}"]
        }


async def generate_presentations_node(state: Phase2State) -> Dict[str, Any]:
    """Generate expert presentations in parallel."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STAGE 2: EXPERT PRESENTATIONS (PARALLEL)")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        logger.info(f"🚀 Creating {len(state['countries'])} expert agents...")

        presentations = await execute_experts_parallel(
            state=state,
            countries=state["countries"]
        )

        duration = time.time() - start_time

        logger.info(f"✅ Stage 2 complete in {duration:.2f}s")
        logger.info(f"   Generated {len(presentations)} presentations")

        return {
            "expert_presentations": presentations,
            "stage_timings": {**state.get("stage_timings", {}), "presentations": duration}
        }

    except Exception as e:
        logger.error(f"Presentations failed: {str(e)}")
        return {
            "errors": state.get("errors", []) + [f"Presentations: {str(e)}"]
        }


async def generate_rankings_node(state: Phase2State) -> Dict[str, Any]:
    """Generate peer rankings in parallel."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STAGE 3: PEER RANKINGS (PARALLEL)")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        logger.info(f"🚀 Creating {state['num_peer_rankers']} peer ranker agents...")

        rankings = await execute_peer_rankers_parallel(
            state=state,
            num_peers=state["num_peer_rankers"]
        )

        duration = time.time() - start_time

        logger.info(f"✅ Stage 3 complete in {duration:.2f}s")
        logger.info(f"   Collected {len(rankings)} peer rankings")

        return {
            "peer_rankings": rankings,
            "stage_timings": {**state.get("stage_timings", {}), "rankings": duration}
        }

    except Exception as e:
        logger.error(f"Rankings failed: {str(e)}")
        return {
            "errors": state.get("errors", []) + [f"Rankings: {str(e)}"]
        }


def aggregate_rankings_node(state: Phase2State) -> Dict[str, Any]:
    """Aggregate peer rankings into consensus ranking."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STAGE 4: RANKING AGGREGATION")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        aggregated = aggregate_peer_rankings(
            peer_rankings=state["peer_rankings"],
            method="hybrid"
        )

        duration = time.time() - start_time

        logger.info(f"✅ Stage 4 complete in {duration:.2f}s")

        return {
            "aggregated_ranking": aggregated,
            "stage_timings": {**state.get("stage_timings", {}), "aggregation": duration}
        }

    except Exception as e:
        logger.error(f"Aggregation failed: {str(e)}")
        return {
            "errors": state.get("errors", []) + [f"Aggregation: {str(e)}"]
        }


async def hot_seat_debate_node(state: Phase2State) -> Dict[str, Any]:
    """Execute hot seat debate if triggered."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STAGE 5: HOT SEAT DEBATE")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        # Get final rankings from aggregation
        final_rankings = state["aggregated_ranking"].get("final_rankings", [])

        # Check if debate should be triggered
        trigger = should_trigger_debate(
            final_rankings,
            threshold=state.get("debate_threshold", "high")
        )

        if not trigger:
            logger.info("⏭️  Debate skipped - consensus is sufficient")
            duration = time.time() - start_time
            return {
                "debate_triggered": False,
                "debate_result": None,
                "final_ranking": final_rankings,
                "stage_timings": {**state.get("stage_timings", {}), "debate": duration}
            }

        logger.info("🔥 Debate triggered - challenging top ranking")

        # Get top 2 countries
        top_ranked = final_rankings[0]
        runner_up = final_rankings[1]

        # Execute debate
        debate_result = await execute_hot_seat_debate(
            top_ranked_country=top_ranked,
            runner_up_country=runner_up,
            expert_presentations=state["expert_presentations"],
            peer_rankings=state["peer_rankings"],
            num_challengers=state.get("num_challengers", 2),
            model="gpt-4o"
        )

        # Determine final ranking based on verdict
        if debate_result["verdict"] == "OVERTURNED":
            logger.info("🔄 Verdict: OVERTURNED - Re-ranking required")
            # Swap positions
            final_ranking = final_rankings.copy()
            final_ranking[0] = runner_up.copy()
            final_ranking[0]["rank"] = 1
            final_ranking[0]["debate_winner"] = True
            final_ranking[1] = top_ranked.copy()
            final_ranking[1]["rank"] = 2
            final_ranking[1]["debate_loser"] = True
        else:
            logger.info("✅ Verdict: UPHELD - Original ranking maintained")
            final_ranking = final_rankings

        duration = time.time() - start_time

        logger.info(f"✅ Stage 5 complete in {duration:.2f}s")

        return {
            "debate_triggered": True,
            "debate_result": debate_result,
            "final_ranking": final_ranking,
            "stage_timings": {**state.get("stage_timings", {}), "debate": duration}
        }

    except Exception as e:
        logger.error(f"Debate failed: {str(e)}")
        final_rankings = state["aggregated_ranking"].get("final_rankings", [])
        return {
            "debate_triggered": False,
            "debate_result": None,
            "final_ranking": final_rankings,
            "errors": state.get("errors", []) + [f"Debate: {str(e)}"]
        }


def generate_report_node(state: Phase2State) -> Dict[str, Any]:
    """Generate final report with optional debate summary."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STAGE 6: REPORT GENERATION")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        # Prepare state for report generator
        report_state = {
            "countries": state["countries"],
            "expert_presentations": state["expert_presentations"],
            "peer_rankings": state["peer_rankings"],
            "aggregated_ranking": {
                **state["aggregated_ranking"],
                "final_rankings": state["final_ranking"]  # Use final ranking (post-debate)
            },
            "execution_metadata": {
                "stage_timings": state.get("stage_timings", {}),
                "total_duration_seconds": sum(state.get("stage_timings", {}).values())
            }
        }

        # Generate report using the function
        report_result = generate_executive_report(report_state)

        duration = time.time() - start_time

        logger.info(f"✅ Stage 6 complete in {duration:.2f}s")
        logger.info(f"   Report saved: {report_result['report_metadata']['filepath']}")

        return {
            "report_markdown": report_result["report_markdown"],
            "report_metadata": report_result["report_metadata"],
            "stage_timings": {**state.get("stage_timings", {}), "report_generation": duration}
        }

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return {
            "errors": state.get("errors", []) + [f"Report: {str(e)}"]
        }


# Conditional Edge Function
# ============================================================================

def should_debate(state: Phase2State) -> str:
    """
    Determine if debate should be executed.

    Returns:
        "debate" if debate should be triggered
        "report" if debate should be skipped
    """
    # Skip if debate disabled
    if not state.get("debate_enabled", True):
        logger.info("⏭️  Debate disabled by configuration")
        # Set final ranking to aggregated ranking
        final_rankings = state["aggregated_ranking"].get("final_rankings", [])
        state["final_ranking"] = final_rankings
        return "report"

    # Get final rankings
    final_rankings = state["aggregated_ranking"].get("final_rankings", [])

    # Skip if less than 2 countries
    if len(final_rankings) < 2:
        logger.info("⏭️  Debate skipped - need at least 2 countries")
        state["final_ranking"] = final_rankings
        return "report"

    # Check agreement level
    trigger = should_trigger_debate(
        final_rankings,
        threshold=state.get("debate_threshold", "high")
    )

    if trigger:
        logger.info("🔥 Routing to HOT SEAT DEBATE")
        return "debate"
    else:
        logger.info("⏭️  Routing to REPORT (skipping debate)")
        # Set final ranking to aggregated ranking
        state["final_ranking"] = final_rankings
        return "report"


# Workflow Construction
# ============================================================================

def create_phase2_workflow() -> StateGraph:
    """
    Create Phase 2 LangGraph workflow with conditional debate.

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = StateGraph(Phase2State)

    # Add nodes
    workflow.add_node("research", load_research_node)
    workflow.add_node("presentations", generate_presentations_node)
    workflow.add_node("rankings", generate_rankings_node)
    workflow.add_node("aggregation", aggregate_rankings_node)
    workflow.add_node("debate", hot_seat_debate_node)
    workflow.add_node("report", generate_report_node)

    # Define edges
    workflow.set_entry_point("research")
    workflow.add_edge("research", "presentations")
    workflow.add_edge("presentations", "rankings")
    workflow.add_edge("rankings", "aggregation")

    # CONDITIONAL EDGE: Debate or skip to report
    workflow.add_conditional_edges(
        "aggregation",
        should_debate,
        {
            "debate": "debate",
            "report": "report"
        }
    )

    # If debate happened, go to report
    workflow.add_edge("debate", "report")

    # Report is the end
    workflow.add_edge("report", END)

    return workflow.compile()


# Main Execution Function
# ============================================================================

async def run_phase2_langgraph(
        countries: List[str],
        research_json_data: Optional[List[Dict[str, str]]] = None,
        num_peer_rankers: int = 3,
        debate_enabled: bool = True,
        debate_threshold: str = "high",
        num_challengers: int = 2
) -> Dict[str, Any]:
    """
    Execute Phase 2 LangGraph workflow.

    Args:
        countries: List of country codes to rank
        research_json_data: Optional pre-loaded research data
        num_peer_rankers: Number of peer ranking agents
        debate_enabled: Enable/disable hot seat debate
        debate_threshold: Consensus threshold to trigger debate
                         ("very_high", "high", "medium", "low")
        num_challengers: Number of challengers in debate

    Returns:
        Dict with complete workflow results including debate
    """
    workflow_start = time.time()

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 2 LANGGRAPH WORKFLOW - STARTING")
    logger.info("=" * 70)
    logger.info(f"Countries: {countries}")
    logger.info(f"Peer rankers: {num_peer_rankers}")
    logger.info(f"Debate enabled: {debate_enabled}")
    logger.info(f"Debate threshold: {debate_threshold}")
    logger.info(f"Number of challengers: {num_challengers}")

    # Initialize state
    initial_state: Phase2State = {
        "countries": countries,
        "num_peer_rankers": num_peer_rankers,
        "research_data": research_json_data,
        "debate_enabled": debate_enabled,
        "debate_threshold": debate_threshold,
        "num_challengers": num_challengers,
        "country_research": None,
        "expert_presentations": None,
        "peer_rankings": None,
        "aggregated_ranking": None,
        "debate_triggered": False,
        "debate_result": None,
        "final_ranking": None,
        "report_markdown": None,
        "report_metadata": None,
        "errors": [],
        "stage_timings": {},
        "total_duration": None
    }

    # Create and compile workflow
    workflow = create_phase2_workflow()

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 2 LANGGRAPH WORKFLOW COMPILED")
    logger.info("=" * 70)
    logger.info("Nodes: 6 (research, presentations, rankings, aggregation, debate, report)")
    logger.info(f"Conditional logic: Debate triggered if agreement < {debate_threshold}")
    logger.info("Execution mode: Async with parallel stages")
    logger.info("=" * 70)

    # Execute workflow
    final_state = await workflow.ainvoke(initial_state)

    # Calculate total duration
    total_duration = time.time() - workflow_start
    final_state["total_duration"] = total_duration

    # Log completion
    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 2 LANGGRAPH WORKFLOW - COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total duration: {total_duration:.2f}s")
    logger.info(f"Countries ranked: {len(countries)}")
    logger.info(f"Debate triggered: {final_state.get('debate_triggered', False)}")

    if final_state.get("debate_triggered"):
        verdict = final_state["debate_result"]["verdict"]
        logger.info(f"Debate verdict: {verdict}")

    # Log final rankings
    if final_state.get("final_ranking"):
        logger.info("")
        logger.info("Final Rankings:")
        for r in final_state["final_ranking"]:
            logger.info(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")

    # Log report path
    if final_state.get("report_metadata"):
        logger.info(f"\n📄 Report saved: {final_state['report_metadata']['filepath']}")

    # Execution metadata
    execution_metadata = {
        "total_duration_seconds": total_duration,
        "stage_timings": final_state.get("stage_timings", {}),
        "num_countries": len(countries),
        "num_peer_rankers": num_peer_rankers,
        "debate_enabled": debate_enabled,
        "debate_triggered": final_state.get("debate_triggered", False),
        "errors": final_state.get("errors", []),
        "timestamp": datetime.now().isoformat()
    }

    # Return comprehensive result
    return {
        "expert_presentations": final_state.get("expert_presentations", {}),
        "peer_rankings": final_state.get("peer_rankings", []),
        "aggregated_ranking": final_state.get("aggregated_ranking", {}),
        "debate_triggered": final_state.get("debate_triggered", False),
        "debate_result": final_state.get("debate_result"),
        "final_ranking": final_state.get("final_ranking", []),
        "report_markdown": final_state.get("report_markdown", ""),
        "report_metadata": final_state.get("report_metadata", {}),
        "execution_metadata": execution_metadata,
        "errors": final_state.get("errors", [])
    }


# Entry point for testing
if __name__ == "__main__":
    async def test_phase2():
        """Test Phase 2 workflow."""
        result = await run_phase2_langgraph(
            countries=["USA", "CHN", "IND"],
            num_peer_rankers=3,
            debate_enabled=True,
            debate_threshold="high",  # Will trigger if agreement is medium or low
            num_challengers=2
        )

        print("\n" + "=" * 70)
        print("PHASE 2 WORKFLOW TEST COMPLETE")
        print("=" * 70)
        print(f"Debate triggered: {result['debate_triggered']}")
        if result['debate_triggered']:
            print(f"Verdict: {result['debate_result']['verdict']}")
        print(f"Final rankings: {len(result['final_ranking'])} countries")
        print(f"Errors: {len(result['errors'])}")


    asyncio.run(test_phase2())