"""
Phase 1 Workflow Orchestrator

Coordinates execution of all Phase 1 agents:
1. Research Loading (parallel)
2. Expert Presentations (parallel)
3. Peer Rankings (parallel)
4. Aggregation (sequential)

Provides:
- Parallel execution for speed
- State management
- Error handling
- Execution metrics
- Progress tracking
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from business_units.insights_team.report_generator import generate_executive_report
from src.workflows.phase1_state import (
    Phase1State,
    create_phase1_state,
    validate_phase1_state,
    get_stage_progress,
    merge_state_updates
)
from business_units.data_team.research_loader import research_loader
from business_units.expert_team.expert_agents import create_expert_agent
from business_units.ranking_team.peer_ranking_agents import create_peer_ranker_agent
from business_units.ranking_team.aggregation_logic import ranking_aggregator

logger = logging.getLogger("Phase1Workflow")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Phase 1 Workflow
# ============================================================================

class Phase1Workflow:
    """
    Phase 1 workflow orchestrator.

    Executes all Phase 1 stages with parallel execution where possible.
    """

    def __init__(self, num_peer_rankers: int = 3):
        """
        Initialize Phase 1 workflow.

        Args:
            num_peer_rankers: Number of independent peer rankers to use
        """
        self.num_peer_rankers = num_peer_rankers
        self.execution_log = []

        logger.info("=" * 70)
        logger.info("PHASE 1 WORKFLOW INITIALIZED")
        logger.info("=" * 70)
        logger.info(f"Configuration:")
        logger.info(f"  Peer rankers: {num_peer_rankers}")
        logger.info(f"  Parallel execution: Enabled")

    def run(
            self,
            countries: List[str],
            research_json_path: Optional[str] = None,
            research_json_data: Optional[List[Dict[str, str]]] = None,
            query: Optional[str] = None
    ) -> Phase1State:
        """
        Execute Phase 1 workflow synchronously.

        Args:
            countries: List of country codes (e.g., ["USA", "IND", "CHN"])
            research_json_path: Optional path to research JSON file
            research_json_data: Optional direct research data
            query: Optional natural language query

        Returns:
            Final Phase1State with complete rankings
        """
        # Run async workflow in sync context
        return asyncio.run(self.run_async(
            countries=countries,
            research_json_path=research_json_path,
            research_json_data=research_json_data,
            query=query
        ))

    async def run_async(
            self,
            countries: List[str],
            research_json_path: Optional[str] = None,
            research_json_data: Optional[List[Dict[str, str]]] = None,
            query: Optional[str] = None
    ) -> Phase1State:
        """Execute Phase 1 workflow asynchronously."""
        workflow_start = time.time()

        logger.info("\n" + "=" * 70)
        logger.info("PHASE 1 WORKFLOW - STARTING")
        logger.info("=" * 70)
        logger.info(f"Countries: {countries}")
        logger.info(f"Peer rankers: {self.num_peer_rankers}")

        # Create initial state
        state = create_phase1_state(
            countries=countries,
            research_json_path=research_json_path,
            research_json_data=research_json_data,
            query=query
        )

        # Validate state
        is_valid, errors = validate_phase1_state(state)
        if not is_valid:
            logger.error(f"Invalid state: {errors}")
            state["errors"].extend(errors)
            return state

        try:
            # Stage 1: Research Loading
            state = await self._stage1_research(state)

            # Stage 2: Expert Presentations (parallel)
            state = await self._stage2_presentations(state)

            # Stage 3: Peer Rankings (parallel)
            state = await self._stage3_rankings(state)

            # Stage 4: Aggregation (sequential)
            state = await self._stage4_aggregation(state)

            # Stage 5: Report Generation (sequential)  # <-- ADD THIS
            state = await self._stage5_report_generation(state)  # <-- ADD THIS

            # Finalize
            workflow_end = time.time()
            workflow_duration = workflow_end - workflow_start

            state["execution_metadata"]["end_time"] = datetime.now().isoformat()
            state["execution_metadata"]["total_duration_seconds"] = round(workflow_duration, 2)

            # Calculate parallel efficiency
            total_agent_time = sum(
                exec["duration"]
                for exec in state["execution_metadata"]["agent_executions"]
                if "duration" in exec
            )

            if workflow_duration > 0:
                state["execution_metadata"]["parallel_efficiency"] = round(
                    total_agent_time / workflow_duration, 2
                )

            logger.info("\n" + "=" * 70)
            logger.info("PHASE 1 WORKFLOW - COMPLETE")
            logger.info("=" * 70)
            logger.info(f"Total duration: {workflow_duration:.2f}s")
            logger.info(f"Parallel efficiency: {state['execution_metadata']['parallel_efficiency']:.2f}x")
            logger.info(f"Countries ranked: {len(state.get('aggregated_ranking', {}).get('final_rankings', []))}")

            # Show final ranking
            final_rankings = state.get('aggregated_ranking', {}).get('final_rankings', [])
            if final_rankings:
                logger.info(f"\nFinal Rankings:")
                for r in final_rankings:
                    logger.info(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")

            # Show report info
            report_path = state.get("report_metadata", {}).get("filepath")  # <-- ADD THIS
            if report_path:  # <-- ADD THIS
                logger.info(f"\n📄 Report saved: {report_path}")  # <-- ADD THIS

            return state

        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            state["errors"].append(f"Workflow error: {str(e)}")
            return state

    async def _stage1_research(self, state: Phase1State) -> Phase1State:
        """
        Stage 1: Load research data.

        This is typically fast and doesn't need parallelization.
        """
        stage_start = time.time()

        logger.info("\n" + "=" * 70)
        logger.info("STAGE 1: RESEARCH LOADING")
        logger.info("=" * 70)

        try:
            # Run research loader
            result = await asyncio.to_thread(research_loader, state)

            # Merge results
            state = merge_state_updates(state, result)

            stage_duration = time.time() - stage_start
            state["execution_metadata"]["stage_timings"]["research"] = round(stage_duration, 2)

            logger.info(f"✅ Stage 1 complete in {stage_duration:.2f}s")
            logger.info(f"   Loaded research for {len(state['country_research'])} countries")

            return state

        except Exception as e:
            logger.error(f"Stage 1 failed: {str(e)}")
            state["errors"].append(f"Research loading failed: {str(e)}")
            return state

    async def _stage2_presentations(self, state: Phase1State) -> Phase1State:
        """
        Stage 2: Generate expert presentations (parallel).

        Each country gets its own expert agent running in parallel.
        """
        stage_start = time.time()

        logger.info("\n" + "=" * 70)
        logger.info("STAGE 2: EXPERT PRESENTATIONS (PARALLEL)")
        logger.info("=" * 70)

        countries = state.get("countries", [])

        if not countries:
            logger.warning("No countries to process")
            return state

        logger.info(f"🚀 Creating {len(countries)} expert agents...")

        # Create expert agents for each country
        expert_agents = {
            country: create_expert_agent(country, expert_id=1)
            for country in countries
        }

        # Execute all experts in parallel
        async def run_expert(country: str, agent: callable):
            """Run single expert agent."""
            try:
                logger.info(f"   Starting expert for {country}...")
                result = await asyncio.to_thread(agent, state)
                logger.info(f"   ✅ Expert for {country} complete")
                return result
            except Exception as e:
                logger.error(f"   ❌ Expert for {country} failed: {str(e)}")
                return {
                    "expert_presentations": {},
                    "presentation_metadata": {
                        country: {
                            "success": False,
                            "error": str(e)
                        }
                    }
                }

        tasks = [
            run_expert(country, agent)
            for country, agent in expert_agents.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge all results
        all_presentations = {}
        all_metadata = {}

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Expert task failed: {str(result)}")
                continue

            if "expert_presentations" in result:
                all_presentations.update(result["expert_presentations"])

            if "presentation_metadata" in result:
                all_metadata.update(result["presentation_metadata"])

        # Update state
        state["expert_presentations"] = all_presentations
        state["presentation_metadata"] = all_metadata

        stage_duration = time.time() - stage_start
        state["execution_metadata"]["stage_timings"]["presentations"] = round(stage_duration, 2)

        logger.info(f"✅ Stage 2 complete in {stage_duration:.2f}s")
        logger.info(f"   Generated {len(all_presentations)} presentations")
        logger.info(f"   Speedup from parallelization: ~{len(countries)}x")

        return state

    async def _stage3_rankings(self, state: Phase1State) -> Phase1State:
        """
        Stage 3: Peer rankings (parallel).

        Multiple peer agents rank all presentations independently.
        """
        stage_start = time.time()

        logger.info("\n" + "=" * 70)
        logger.info("STAGE 3: PEER RANKINGS (PARALLEL)")
        logger.info("=" * 70)

        presentations = state.get("expert_presentations", {})

        if not presentations:
            logger.warning("No presentations to rank")
            return state

        logger.info(f"🚀 Creating {self.num_peer_rankers} peer ranker agents...")

        # Create peer ranker agents
        peer_agents = {
            peer_id: create_peer_ranker_agent(peer_id)
            for peer_id in range(1, self.num_peer_rankers + 1)
        }

        # Execute all peers in parallel
        async def run_peer(peer_id: int, agent: callable):
            """Run single peer ranker agent."""
            try:
                logger.info(f"   Starting peer ranker #{peer_id}...")
                result = await asyncio.to_thread(agent, state)
                logger.info(f"   ✅ Peer ranker #{peer_id} complete")
                return result
            except Exception as e:
                logger.error(f"   ❌ Peer ranker #{peer_id} failed: {str(e)}")
                return {
                    "peer_rankings": [],
                    "ranking_metadata": {
                        f"peer_{peer_id}": {
                            "success": False,
                            "error": str(e)
                        }
                    }
                }

        tasks = [
            run_peer(peer_id, agent)
            for peer_id, agent in peer_agents.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge all results
        all_rankings = []
        all_metadata = {}

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Peer ranker task failed: {str(result)}")
                continue

            if "peer_rankings" in result and result["peer_rankings"]:
                all_rankings.extend(result["peer_rankings"])

            if "ranking_metadata" in result:
                all_metadata.update(result["ranking_metadata"])

        # Update state
        state["peer_rankings"] = all_rankings
        state["ranking_metadata"] = all_metadata

        stage_duration = time.time() - stage_start
        state["execution_metadata"]["stage_timings"]["rankings"] = round(stage_duration, 2)

        logger.info(f"✅ Stage 3 complete in {stage_duration:.2f}s")
        logger.info(f"   Collected {len(all_rankings)} peer rankings")
        logger.info(f"   Speedup from parallelization: ~{self.num_peer_rankers}x")

        return state

    async def _stage4_aggregation(self, state: Phase1State) -> Phase1State:
        """
        Stage 4: Aggregate peer rankings (sequential).

        Combines all peer rankings into final consensus ranking.
        """
        stage_start = time.time()

        logger.info("\n" + "=" * 70)
        logger.info("STAGE 4: RANKING AGGREGATION")
        logger.info("=" * 70)

        peer_rankings = state.get("peer_rankings", [])

        if not peer_rankings:
            logger.warning("No peer rankings to aggregate")
            return state

        try:
            # Run aggregator
            result = await asyncio.to_thread(ranking_aggregator, state)

            # Merge results
            state = merge_state_updates(state, result)

            stage_duration = time.time() - stage_start
            state["execution_metadata"]["stage_timings"]["aggregation"] = round(stage_duration, 2)

            logger.info(f"✅ Stage 4 complete in {stage_duration:.2f}s")

            return state

        except Exception as e:
            logger.error(f"Stage 4 failed: {str(e)}")
            state["errors"].append(f"Aggregation failed: {str(e)}")
            return state


    async def _stage5_report_generation(self, state: Phase1State) -> Phase1State:
        """
        Stage 5: Generate executive report (sequential).

        Creates comprehensive markdown report with all results.
        """
        stage_start = time.time()

        logger.info("\n" + "=" * 70)
        logger.info("STAGE 5: REPORT GENERATION")
        logger.info("=" * 70)

        try:
            # Run report generator
            result = await asyncio.to_thread(generate_executive_report, state)

            # Merge results
            state = merge_state_updates(state, result)

            stage_duration = time.time() - stage_start
            state["execution_metadata"]["stage_timings"]["report_generation"] = round(stage_duration, 2)

            report_size = len(state.get("report_markdown", ""))
            report_path = state.get("report_metadata", {}).get("filepath", "")

            logger.info(f"✅ Stage 5 complete in {stage_duration:.2f}s")
            logger.info(f"   Report size: {report_size:,} characters")
            if report_path:
                logger.info(f"   Report saved: {report_path}")

            return state

        except Exception as e:
            logger.error(f"Stage 5 failed: {str(e)}")
            state["errors"].append(f"Report generation failed: {str(e)}")
            return state

    def get_progress(self, state: Phase1State) -> Dict[str, str]:
        """Get current workflow progress."""
        return get_stage_progress(state)

    def get_summary(self, state: Phase1State) -> Dict[str, Any]:
        """Get workflow execution summary."""
        final_rankings = state.get('aggregated_ranking', {}).get('final_rankings', [])

        return {
            "countries_analyzed": len(state.get("countries", [])),
            "research_loaded": len(state.get("country_research", {})),
            "presentations_generated": len(state.get("expert_presentations", {})),
            "peer_rankings_collected": len(state.get("peer_rankings", [])),
            "final_rankings_count": len(final_rankings),
            "top_choice": final_rankings[0]["country_code"] if final_rankings else None,
            "execution_time_seconds": state.get("execution_metadata", {}).get("total_duration_seconds", 0),
            "parallel_efficiency": state.get("execution_metadata", {}).get("parallel_efficiency", 0),
            "errors": state.get("errors", []),
            "progress": self.get_progress(state)
        }


# ============================================================================
# Convenience Functions
# ============================================================================

def run_phase1_workflow(
        countries: List[str],
        research_json_path: Optional[str] = None,
        research_json_data: Optional[List[Dict[str, str]]] = None,
        num_peer_rankers: int = 3,
        query: Optional[str] = None
) -> Phase1State:
    """
    Convenience function to run Phase 1 workflow.

    Args:
        countries: List of country codes
        research_json_path: Optional path to research JSON
        research_json_data: Optional direct research data
        num_peer_rankers: Number of peer rankers (default: 3)
        query: Optional query

    Returns:
        Final Phase1State with rankings

    Example:
        >>> result = run_phase1_workflow(
        ...     countries=["USA", "IND", "CHN"],
        ...     research_json_path="data/research.json",
        ...     num_peer_rankers=5
        ... )
        >>> print(result['aggregated_ranking']['final_rankings'])
    """
    workflow = Phase1Workflow(num_peer_rankers=num_peer_rankers)

    return workflow.run(
        countries=countries,
        research_json_path=research_json_path,
        research_json_data=research_json_data,
        query=query
    )
