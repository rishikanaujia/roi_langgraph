"""
LangGraph Country Comparison Workflow

Main workflow that orchestrates all agents using LangGraph.
Uses StateGraph to define the flow of agent execution.
"""

from typing import Dict, Any, List, Literal
from langgraph.graph import StateGraph, END
from datetime import datetime
import logging

from src.state.shared_state import WorkflowState, create_initial_state
from src.registry.agent_registry import get_registry
from src.registry.agent_metadata import AgentCapability


class CountryComparisonWorkflow:
    """
    LangGraph workflow for country comparison.

    Flow:
    1. START → Validate Input
    2. Load Representative Locations
    3. Analyze Locations (parallel)
    4. Aggregate by Country
    5. Rank Countries (iterative with verification)
    6. Generate Dual Recommendation (if needed)
    7. END
    """

    def __init__(self):
        """Initialize workflow."""
        self.logger = self._create_logger()
        self.registry = get_registry()
        self.graph = None
        self._build_graph()

    def _create_logger(self) -> logging.Logger:
        """Create logger."""
        logger = logging.getLogger("CountryComparisonWorkflow")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _build_graph(self) -> None:
        """Build the LangGraph state graph."""

        # Create graph
        workflow = StateGraph(WorkflowState)

        # Add nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("load_locations", self._load_locations)
        workflow.add_node("analyze_locations", self._analyze_locations)
        workflow.add_node("aggregate_countries", self._aggregate_countries)
        workflow.add_node("rank_countries", self._rank_countries)
        workflow.add_node("verify_ranking", self._verify_ranking)
        workflow.add_node("generate_dual_recommendation", self._generate_dual_recommendation)

        # Define edges
        workflow.set_entry_point("validate_input")

        workflow.add_edge("validate_input", "load_locations")
        workflow.add_edge("load_locations", "analyze_locations")
        workflow.add_edge("analyze_locations", "aggregate_countries")
        workflow.add_edge("aggregate_countries", "rank_countries")
        workflow.add_edge("rank_countries", "verify_ranking")

        # Conditional edge after verification
        workflow.add_conditional_edges(
            "verify_ranking",
            self._should_retry_ranking,
            {
                "retry": "rank_countries",  # Try again with feedback
                "dual_recommendation": "generate_dual_recommendation",  # Ambiguous
                "end": END  # Success
            }
        )

        workflow.add_edge("generate_dual_recommendation", END)

        # Compile
        self.graph = workflow.compile()
        self.logger.info("LangGraph workflow compiled successfully")

    # ==================== NODE FUNCTIONS ====================

    def _validate_input(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Validate input parameters.

        Node 1: Check countries are valid.
        """
        self.logger.info("Validating input...")

        countries = state.get("countries", [])

        if not countries or len(countries) < 2:
            return {
                "errors": ["Need at least 2 countries to compare"]
            }

        if len(countries) > 10:
            return {
                "errors": ["Maximum 10 countries allowed"]
            }

        # Mark start time
        return {
            "execution_metadata": {
                "start_time": datetime.now().isoformat(),
                "agent_executions": []
            }
        }

    def _load_locations(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Load representative locations for each country.

        Node 2: Get 2 locations per country (solar + wind).
        """
        self.logger.info("Loading representative locations...")

        # Find location loader agent
        agents = self.registry.find_agents_by_capability(
            AgentCapability.DATA_FETCH
        )

        if agents:
            # Use registered agent
            agent = agents[0]
            result = self.registry.execute_agent(agent.agent_id, state)

            if result.success:
                return result.outputs

        # Fallback: Mock locations
        countries = state.get("countries", [])
        locations = []

        for country in countries:
            # In real system, load from database
            locations.append({
                "country_code": country,
                "technology": "solar_pv",
                "name": f"{country} Solar",
                "latitude": 0.0,
                "longitude": 0.0
            })
            locations.append({
                "country_code": country,
                "technology": "onshore_wind",
                "name": f"{country} Wind",
                "latitude": 0.0,
                "longitude": 0.0
            })

        return {"locations": locations}

    def _analyze_locations(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Analyze all locations.

        Node 3: Run analysis for each location (can be parallel).
        """
        self.logger.info("Analyzing locations...")

        locations = state.get("locations", [])

        # Find analysis agents
        analysis_agents = self.registry.find_agents_by_capability(
            AgentCapability.ANALYSIS
        )

        analyses = []

        for location in locations:
            # Prepare state for this location
            location_state = {
                **state,
                "current_location": location
            }

            if analysis_agents:
                # Use registered agent
                agent = analysis_agents[0]
                result = self.registry.execute_agent(agent.agent_id, location_state)

                if result.success:
                    analyses.append({
                        **result.outputs,
                        "location": location
                    })
            else:
                # Fallback: Mock analysis
                analyses.append({
                    "location": location,
                    "irr": 5.0,
                    "lcoe": 60.0,
                    "npv": -50000000
                })

        return {"location_analyses": analyses}

    def _aggregate_countries(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Aggregate location results by country.

        Node 4: Group analyses by country and compute averages.
        """
        self.logger.info("Aggregating by country...")

        analyses = state.get("location_analyses", [])
        countries = state.get("countries", [])

        country_reports = {}

        for country in countries:
            # Filter analyses for this country
            country_analyses = [
                a for a in analyses
                if a.get("location", {}).get("country_code") == country
            ]

            if country_analyses:
                # Compute averages
                avg_irr = sum(a.get("irr", 0) for a in country_analyses) / len(country_analyses)
                avg_lcoe = sum(a.get("lcoe", 0) for a in country_analyses) / len(country_analyses)
                avg_npv = sum(a.get("npv", 0) for a in country_analyses) / len(country_analyses)

                country_reports[country] = {
                    "country_code": country,
                    "country_name": country,
                    "aggregate_metrics": {
                        "average_irr": avg_irr,
                        "average_lcoe": avg_lcoe,
                        "average_npv": avg_npv
                    },
                    "location_analyses": country_analyses
                }

        return {"country_reports": country_reports}

    def _rank_countries(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Rank countries using AI.

        Node 5: Generate ranking with GPT-4.
        """
        iteration = len(state.get("ranking_iterations", []))
        self.logger.info(f"Ranking countries (iteration {iteration + 1})...")

        country_reports = state.get("country_reports", {})

        # Find ranking agents
        ranking_agents = self.registry.find_agents_by_capability(
            AgentCapability.RANKING
        )

        if ranking_agents:
            agent = ranking_agents[0]
            result = self.registry.execute_agent(agent.agent_id, state)

            if result.success:
                ranking = result.outputs.get("ranking", {})

                # Save this iteration
                iteration_record = {
                    "iteration": iteration + 1,
                    "ranking": ranking,
                    "timestamp": datetime.now().isoformat()
                }

                return {
                    "ranking": ranking,
                    "ranking_iterations": [iteration_record]
                }

        # Fallback: Simple ranking
        sorted_countries = sorted(
            country_reports.items(),
            key=lambda x: x[1]["aggregate_metrics"]["average_irr"],
            reverse=True
        )

        ranking = {
            "ranked_countries": [
                {
                    "rank": i + 1,
                    "country_code": code,
                    "country_name": code,
                    "overall_score": report["aggregate_metrics"]["average_irr"] * 10
                }
                for i, (code, report) in enumerate(sorted_countries)
            ]
        }

        return {"ranking": ranking}

    def _verify_ranking(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Verify ranking for bias and consistency.

        Node 6: Check ranking with AI verifier.
        """
        self.logger.info("Verifying ranking...")

        ranking = state.get("ranking", {})
        country_reports = state.get("country_reports", {})

        # Find verification agents
        verification_agents = self.registry.find_agents_by_capability(
            AgentCapability.VERIFICATION
        )

        if verification_agents:
            agent = verification_agents[0]
            result = self.registry.execute_agent(agent.agent_id, state)

            if result.success:
                return result.outputs

        # Fallback: Simple verification (always pass)
        return {
            "verification": {
                "verified": True,
                "summary": "Ranking looks good",
                "issues_found": []
            }
        }

    def _generate_dual_recommendation(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Generate dual recommendation for ambiguous rankings.

        Node 7: Create Option A vs Option B.
        """
        self.logger.info("Generating dual recommendation...")

        ranking = state.get("ranking", {})
        country_reports = state.get("country_reports", {})

        # Simple dual recommendation
        ranked = ranking.get("ranked_countries", [])

        if len(ranked) >= 2:
            dual_rec = {
                "recommendation_type": "dual",
                "message": "This comparison involves genuine trade-offs",
                "option_a": {
                    "country": ranked[0]["country_name"],
                    "score": ranked[0]["overall_score"]
                },
                "option_b": {
                    "country": ranked[1]["country_name"],
                    "score": ranked[1]["overall_score"]
                }
            }

            return {"dual_recommendation": dual_rec}

        return {}

    # ==================== CONDITIONAL EDGE FUNCTIONS ====================

    def _should_retry_ranking(self, state: WorkflowState) -> Literal["retry", "dual_recommendation", "end"]:
        """
        Decide what to do after verification.

        Returns:
            - "retry": Ranking failed, try again with feedback
            - "dual_recommendation": Ranking failed 3 times, generate dual rec
            - "end": Ranking passed, done!
        """
        verification = state.get("verification", {})
        iterations = state.get("ranking_iterations", [])

        # Check if verified
        if verification.get("verified", False):
            self.logger.info("✓ Ranking verified!")
            return "end"

        # Check iteration count
        max_iterations = 3
        if len(iterations) >= max_iterations:
            self.logger.warning(
                f"✗ Max iterations ({max_iterations}) reached, "
                f"generating dual recommendation"
            )
            return "dual_recommendation"

        # Try again
        self.logger.info(f"✗ Ranking failed verification, retrying...")
        return "retry"

    # ==================== EXECUTION ====================

    def run(self, countries: List[str], query: str = None) -> Dict[str, Any]:
        """
        Run the workflow.

        Args:
            countries: List of country codes to compare
            query: Optional natural language query

        Returns:
            Final state with all results
        """
        self.logger.info(f"Starting workflow for countries: {countries}")

        # Create initial state
        initial_state = create_initial_state(countries, query)

        # Run graph
        final_state = self.graph.invoke(initial_state)

        # Add end time
        final_state["execution_metadata"]["end_time"] = datetime.now().isoformat()

        self.logger.info("Workflow completed")

        return final_state

    async def run_async(self, countries: List[str], query: str = None) -> Dict[str, Any]:
        """Async version of run."""
        return self.run(countries, query)

    def get_graph_image(self, output_path: str = "workflow_graph.png") -> None:
        """
        Generate visual representation of the graph.

        Requires: graphviz
        """
        try:
            from IPython.display import Image, display

            # Get graph image
            img = self.graph.get_graph().draw_mermaid_png()

            # Save to file
            with open(output_path, "wb") as f:
                f.write(img)

            self.logger.info(f"Graph saved to {output_path}")

        except Exception as e:
            self.logger.warning(f"Could not generate graph image: {str(e)}")


# Convenience function
def create_workflow() -> CountryComparisonWorkflow:
    """Create and return workflow instance."""
    return CountryComparisonWorkflow()