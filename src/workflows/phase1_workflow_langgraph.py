"""
Phase 1 Workflow - LangGraph Implementation

Uses LangGraph's StateGraph for proper workflow orchestration.
"""

import asyncio
import time
from datetime import datetime
from typing import TypedDict, List, Dict, Any, Optional, Annotated
import logging

from langgraph.graph import StateGraph, END

from business_units.expert_team.expert_agents import (
    create_expert_agent,
    execute_experts_parallel
)
from business_units.ranking_team.peer_ranking_agents import (
    create_peer_ranker_agent,
    execute_peer_rankers_parallel
)

logger = logging.getLogger("Phase1WorkflowLangGraph")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Enhanced State with Reducers
# ============================================================================

def add_to_list(existing: list, new: list) -> list:
    """Reducer: Append to list."""
    return existing + new


class Phase1GraphState(TypedDict):
    """State for LangGraph workflow with proper typing."""

    # Core data
    countries: List[str]
    country_research: Dict[str, str]
    expert_presentations: Dict[str, Dict]
    peer_rankings: Annotated[List[Dict], add_to_list]
    aggregated_ranking: Dict
    consensus_scores: Dict[str, float]

    # Report outputs
    executive_report: Dict
    report_markdown: str
    report_metadata: Dict

    # Execution tracking
    execution_metadata: Dict
    errors: Annotated[List[str], add_to_list]

    # Configuration
    num_peer_rankers: int
    research_json_path: Optional[str]
    research_json_data: Optional[List[Dict[str, str]]]
    query: Optional[str]


# ============================================================================
# Node Functions (LangGraph Nodes)
# ============================================================================

def load_research_node(state: Phase1GraphState) -> Phase1GraphState:
    """Node 1: Load research data."""
    stage_start = time.time()

    logger.info("\n" + "=" * 70)
    logger.info("STAGE 1: RESEARCH LOADING")
    logger.info("=" * 70)

    try:
        from business_units.data_team.research_loader import (
            load_research_from_json,
            load_research_from_file
        )

        # Load research based on what's provided
        if state.get("research_json_data"):
            country_research = load_research_from_json(state["research_json_data"])
        elif state.get("research_json_path"):
            country_research, errors = load_research_from_file(state["research_json_path"])
            if errors:
                for error in errors:
                    state["errors"].append(f"Research loading: {error}")
        else:
            raise ValueError("No research data provided")

        # Filter to requested countries
        filtered_research = {
            code: research
            for code, research in country_research.items()
            if code in state["countries"]
        }

        stage_duration = time.time() - stage_start

        # Update state
        state["country_research"] = filtered_research
        state["execution_metadata"]["stage_timings"]["research"] = round(stage_duration, 2)

        logger.info(f"✅ Stage 1 complete in {stage_duration:.2f}s")
        logger.info(f"   Loaded research for {len(filtered_research)} countries")

    except Exception as e:
        logger.error(f"Stage 1 failed: {str(e)}")
        state["errors"].append(f"Research loading failed: {str(e)}")

    return state


async def generate_presentations_node(state: Phase1GraphState) -> Phase1GraphState:
    """Node 2: Generate expert presentations (parallel)."""
    stage_start = time.time()

    logger.info("\n" + "=" * 70)
    logger.info("STAGE 2: EXPERT PRESENTATIONS (PARALLEL)")
    logger.info("=" * 70)

    try:
        logger.info(f"🚀 Creating {len(state['countries'])} expert agents...")

        # Use the execute_experts_parallel helper from expert_agents module
        result = await execute_experts_parallel(
            state=state,
            countries=state["countries"]
        )

        stage_duration = time.time() - stage_start

        # Update state with results
        state["expert_presentations"].update(result.get("expert_presentations", {}))
        state["execution_metadata"]["stage_timings"]["presentations"] = round(stage_duration, 2)

        # Track errors
        if result.get("errors"):
            state["errors"].extend(result["errors"])

        logger.info(f"✅ Stage 2 complete in {stage_duration:.2f}s")
        logger.info(f"   Generated {len(state['expert_presentations'])} presentations")

    except Exception as e:
        logger.error(f"Stage 2 failed: {str(e)}")
        state["errors"].append(f"Expert presentations failed: {str(e)}")

    return state


async def generate_rankings_node(state: Phase1GraphState) -> Phase1GraphState:
    """Node 3: Generate peer rankings (parallel)."""
    stage_start = time.time()

    logger.info("\n" + "=" * 70)
    logger.info("STAGE 3: PEER RANKINGS (PARALLEL)")
    logger.info("=" * 70)

    try:
        logger.info(f"🚀 Creating {state['num_peer_rankers']} peer ranker agents...")

        # Use the execute_peer_rankers_parallel helper from peer_ranking_agents module
        result = await execute_peer_rankers_parallel(
            state=state,
            num_peers=state["num_peer_rankers"]
        )

        stage_duration = time.time() - stage_start

        # Update state with results
        state["peer_rankings"].extend(result.get("peer_rankings", []))
        state["execution_metadata"]["stage_timings"]["rankings"] = round(stage_duration, 2)

        # Track errors
        if result.get("errors"):
            state["errors"].extend(result["errors"])

        logger.info(f"✅ Stage 3 complete in {stage_duration:.2f}s")
        logger.info(f"   Collected {len(state['peer_rankings'])} peer rankings")

    except Exception as e:
        logger.error(f"Stage 3 failed: {str(e)}")
        state["errors"].append(f"Peer rankings failed: {str(e)}")

    return state


def aggregate_rankings_node(state: Phase1GraphState) -> Phase1GraphState:
    """Node 4: Aggregate peer rankings."""
    stage_start = time.time()

    logger.info("\n" + "=" * 70)
    logger.info("STAGE 4: RANKING AGGREGATION")
    logger.info("=" * 70)

    try:
        from business_units.ranking_team.aggregation_logic import aggregate_peer_rankings

        # Aggregate rankings using the existing function
        aggregated = aggregate_peer_rankings(
            peer_rankings=state["peer_rankings"],
            method="hybrid"
        )

        stage_duration = time.time() - stage_start

        # Update state
        state["aggregated_ranking"] = aggregated

        # Extract consensus scores
        consensus_scores = {
            r["country_code"]: r["consensus_score"]
            for r in aggregated.get("final_rankings", [])
        }
        state["consensus_scores"] = consensus_scores

        state["execution_metadata"]["stage_timings"]["aggregation"] = round(stage_duration, 2)

        logger.info(f"✅ Stage 4 complete in {stage_duration:.2f}s")

    except Exception as e:
        logger.error(f"Stage 4 failed: {str(e)}")
        state["errors"].append(f"Aggregation failed: {str(e)}")

    return state


def generate_report_node(state: Phase1GraphState) -> Phase1GraphState:
    """Node 5: Generate executive report."""
    stage_start = time.time()

    logger.info("\n" + "=" * 70)
    logger.info("STAGE 5: REPORT GENERATION")
    logger.info("=" * 70)

    try:
        from business_units.insights_team.report_generator import generate_executive_report

        # Generate report (pass full state)
        result = generate_executive_report(state)

        stage_duration = time.time() - stage_start

        # Update state
        state["executive_report"] = result["executive_report"]
        state["report_markdown"] = result["report_markdown"]
        state["report_metadata"] = result["report_metadata"]
        state["execution_metadata"]["stage_timings"]["report_generation"] = round(stage_duration, 2)

        report_path = state["report_metadata"].get("filepath", "")
        logger.info(f"✅ Stage 5 complete in {stage_duration:.2f}s")
        if report_path:
            logger.info(f"   Report saved: {report_path}")

    except Exception as e:
        logger.error(f"Stage 5 failed: {str(e)}")
        state["errors"].append(f"Report generation failed: {str(e)}")

    return state


# ============================================================================
# Graph Builder
# ============================================================================

def create_phase1_graph(num_peer_rankers: int = 3) -> StateGraph:
    """
    Create Phase 1 workflow graph using LangGraph.

    Graph structure:
        load_research → generate_presentations → generate_rankings → aggregate_rankings → generate_report → END

    Args:
        num_peer_rankers: Number of peer ranker agents

    Returns:
        Compiled StateGraph ready for execution
    """

    # Create graph
    workflow = StateGraph(Phase1GraphState)

    # Add nodes (use different names from state keys)
    workflow.add_node("load_research", load_research_node)
    workflow.add_node("generate_presentations", generate_presentations_node)
    workflow.add_node("generate_rankings", generate_rankings_node)
    workflow.add_node("aggregate_rankings", aggregate_rankings_node)
    workflow.add_node("generate_report", generate_report_node)

    # Set entry point
    workflow.set_entry_point("load_research")

    # Add edges (linear flow for Phase 1)
    workflow.add_edge("load_research", "generate_presentations")
    workflow.add_edge("generate_presentations", "generate_rankings")
    workflow.add_edge("generate_rankings", "aggregate_rankings")
    workflow.add_edge("aggregate_rankings", "generate_report")
    workflow.add_edge("generate_report", END)

    # Compile graph
    compiled_graph = workflow.compile()

    logger.info("=" * 70)
    logger.info("PHASE 1 LANGGRAPH WORKFLOW COMPILED")
    logger.info("=" * 70)
    logger.info(f"Nodes: 5 (research, presentations, rankings, aggregation, report)")
    logger.info(f"Peer rankers: {num_peer_rankers}")
    logger.info(f"Execution mode: Async with parallel stages")
    logger.info("=" * 70)

    return compiled_graph


# ============================================================================
# Workflow Runner
# ============================================================================

async def run_phase1_langgraph(
        countries: List[str],
        research_json_path: Optional[str] = None,
        research_json_data: Optional[List[Dict[str, str]]] = None,
        query: Optional[str] = None,
        num_peer_rankers: int = 3
) -> Phase1GraphState:
    """
    Run Phase 1 workflow using LangGraph.

    Args:
        countries: List of country codes (e.g., ["USA", "IND", "CHN"])
        research_json_path: Path to research JSON file (optional)
        research_json_data: Research data as list of dicts (optional)
        query: Optional query string
        num_peer_rankers: Number of peer rankers (default: 3)

    Returns:
        Final state with rankings and report
    """
    workflow_start = time.time()

    logger.info("\n" + "=" * 70)
    logger.info("PHASE 1 LANGGRAPH WORKFLOW - STARTING")
    logger.info("=" * 70)
    logger.info(f"Countries: {countries}")
    logger.info(f"Peer rankers: {num_peer_rankers}")

    # Create initial state
    initial_state: Phase1GraphState = {
        "countries": countries,
        "country_research": {},
        "expert_presentations": {},
        "peer_rankings": [],
        "aggregated_ranking": {},
        "consensus_scores": {},
        "executive_report": {},
        "report_markdown": "",
        "report_metadata": {},
        "execution_metadata": {
            "start_time": datetime.now().isoformat(),
            "end_time": "",
            "total_duration_seconds": 0,
            "parallel_efficiency": 0,
            "stage_timings": {},
            "agent_executions": []
        },
        "errors": [],
        "num_peer_rankers": num_peer_rankers,
        "research_json_path": research_json_path,
        "research_json_data": research_json_data,
        "query": query
    }

    # Create and compile graph
    graph = create_phase1_graph(num_peer_rankers=num_peer_rankers)

    # Execute graph
    final_state = await graph.ainvoke(initial_state)

    # Finalize execution metadata
    workflow_end = time.time()
    workflow_duration = workflow_end - workflow_start

    final_state["execution_metadata"]["end_time"] = datetime.now().isoformat()
    final_state["execution_metadata"]["total_duration_seconds"] = round(workflow_duration, 2)

    logger.info("\n" + "=" * 70)
    logger.info("PHASE 1 LANGGRAPH WORKFLOW - COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total duration: {workflow_duration:.2f}s")
    logger.info(f"Countries ranked: {len(final_state.get('aggregated_ranking', {}).get('final_rankings', []))}")

    # Show final ranking
    final_rankings = final_state.get('aggregated_ranking', {}).get('final_rankings', [])
    if final_rankings:
        logger.info(f"\nFinal Rankings:")
        for r in final_rankings:
            logger.info(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")

    # Show report info
    report_path = final_state.get("report_metadata", {}).get("filepath")
    if report_path:
        logger.info(f"\n📄 Report saved: {report_path}")

    # Show errors if any
    if final_state["errors"]:
        logger.warning(f"\n⚠️  {len(final_state['errors'])} error(s) occurred:")
        for error in final_state["errors"]:
            logger.warning(f"  - {error}")

    return final_state


# ============================================================================
# Synchronous Wrapper
# ============================================================================

def run_phase1_langgraph_sync(
        countries: List[str],
        research_json_path: Optional[str] = None,
        research_json_data: Optional[List[Dict[str, str]]] = None,
        query: Optional[str] = None,
        num_peer_rankers: int = 3
) -> Phase1GraphState:
    """Synchronous wrapper for run_phase1_langgraph."""
    return asyncio.run(run_phase1_langgraph(
        countries=countries,
        research_json_path=research_json_path,
        research_json_data=research_json_data,
        query=query,
        num_peer_rankers=num_peer_rankers
    ))


# ============================================================================
# Visualization Support
# ============================================================================

def visualize_phase1_graph(output_path: str = "phase1_graph.png"):
    """
    Generate visual representation of Phase 1 graph.

    Args:
        output_path: Path to save the graph visualization
    """
    graph = create_phase1_graph()

    try:
        # Generate mermaid diagram
        mermaid = graph.get_graph().draw_mermaid()

        print("Phase 1 Workflow Graph (Mermaid):")
        print("=" * 70)
        print(mermaid)
        print("=" * 70)
        print(f"\nCopy this to https://mermaid.live to visualize")

        return mermaid

    except Exception as e:
        logger.error(f"Could not generate graph visualization: {e}")
        return None