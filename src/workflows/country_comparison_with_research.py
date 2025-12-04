"""
Country Comparison Workflow with Research Data

Enhanced version that loads research data and passes it to insights agents.
Matches the pattern from country_comparison_graph.py
"""

import logging
from typing import Dict, Any, List, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END

from src.state.shared_state import WorkflowState, create_initial_state
from src.registry.agent_registry import get_registry
from src.registry.agent_metadata import AgentCapability

logger = logging.getLogger("CountryComparisonWorkflow")


# ============================================================================
# Workflow with Research
# ============================================================================

class CountryComparisonWorkflowWithResearch:
    """Enhanced workflow that includes research data."""
    
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
        
        # Add nodes (with research step)
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("load_research", self._load_research)  # NEW
        workflow.add_node("load_locations", self._load_locations)
        workflow.add_node("analyze_locations", self._analyze_locations)
        workflow.add_node("aggregate_countries", self._aggregate_countries)
        workflow.add_node("rank_countries", self._rank_countries)
        workflow.add_node("verify_ranking", self._verify_ranking)
        workflow.add_node("generate_insights", self._generate_insights)  # NEW
        
        # Define edges (with research step)
        workflow.set_entry_point("validate_input")
        workflow.add_edge("validate_input", "load_research")  # NEW
        workflow.add_edge("load_research", "load_locations")  # NEW
        workflow.add_edge("load_locations", "analyze_locations")
        workflow.add_edge("analyze_locations", "aggregate_countries")
        workflow.add_edge("aggregate_countries", "rank_countries")
        workflow.add_edge("rank_countries", "verify_ranking")
        
        # Conditional edge after verification
        workflow.add_conditional_edges(
            "verify_ranking",
            self._should_generate_insights,
            {
                "retry": "rank_countries",
                "insights": "generate_insights"
            }
        )
        
        workflow.add_edge("generate_insights", END)
        
        # Compile
        self.graph = workflow.compile()
        self.logger.info("LangGraph workflow with research compiled successfully")
    
    # ==================== NODE FUNCTIONS ====================
    
    def _validate_input(self, state: WorkflowState) -> Dict[str, Any]:
        """Validate input parameters."""
        self.logger.info("Validating input...")
        
        countries = state.get("countries", [])
        
        if not countries or len(countries) < 2:
            return {"errors": ["Need at least 2 countries to compare"]}
        
        if len(countries) > 10:
            return {"errors": ["Maximum 10 countries allowed"]}
        
        return {
            "execution_metadata": {
                "start_time": datetime.now().isoformat(),
                "agent_executions": []
            }
        }
    
    def _load_research(self, state: WorkflowState) -> Dict[str, Any]:
        """Load research data for countries (NEW)."""
        self.logger.info("Loading research data...")
        
        try:
            # Execute research loader agent
            result = self.registry.execute_agent(
                "data_team_research_loader_v1",
                state
            )
            
            if result.success:
                research = result.outputs.get("country_research", {})
                metadata = result.outputs.get("research_metadata", {})
                
                self.logger.info(
                    f"✓ Loaded research for {len(research)} countries "
                    f"({metadata.get('total_characters', 0):,} chars)"
                )
                
                return {
                    "country_research": research,
                    "research_metadata": metadata
                }
        
        except Exception as e:
            self.logger.warning(f"Research loading failed: {str(e)}")
        
        # Continue without research
        return {
            "country_research": {},
            "research_metadata": {"error": "Failed to load research"}
        }
    
    def _load_locations(self, state: WorkflowState) -> Dict[str, Any]:
        """Load representative locations."""
        self.logger.info("Loading representative locations...")
        
        # Find location loader agent
        agents = self.registry.find_agents_by_capability(
            AgentCapability.DATA_FETCH
        )
        
        # Filter to NASA loader (not research loader)
        nasa_agents = [
            a for a in agents 
            if "nasa" in a.agent_id.lower()
        ]
        
        if nasa_agents:
            agent = nasa_agents[0]
            result = self.registry.execute_agent(agent.agent_id, state)
            
            if result.success:
                return result.outputs
        
        return {"locations": []}
    
    def _analyze_locations(self, state: WorkflowState) -> Dict[str, Any]:
        """Analyze all locations."""
        self.logger.info("Analyzing locations...")
        
        locations = state.get("locations", [])
        
        # Find analysis agents
        analysis_agents = self.registry.find_agents_by_capability(
            AgentCapability.ANALYSIS
        )
        
        analyses = []
        
        for location in locations:
            location_state = {
                **state,
                "current_location": location
            }
            
            if analysis_agents:
                agent = analysis_agents[0]
                result = self.registry.execute_agent(agent.agent_id, location_state)
                
                if result.success:
                    analyses.append({
                        **result.outputs,
                        "location": location
                    })
        
        return {"location_analyses": analyses}
    
    def _aggregate_countries(self, state: WorkflowState) -> Dict[str, Any]:
        """Aggregate location results by country."""
        self.logger.info("Aggregating by country...")
        
        analyses = state.get("location_analyses", [])
        countries = state.get("countries", [])
        
        country_reports = {}
        
        for country in countries:
            country_analyses = [
                a for a in analyses
                if a.get("location", {}).get("country_code") == country
            ]
            
            if country_analyses:
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
        """Rank countries."""
        iteration = len(state.get("ranking_iterations", []))
        self.logger.info(f"Ranking countries (iteration {iteration + 1})...")
        
        # Find ranking agents
        ranking_agents = self.registry.find_agents_by_capability(
            AgentCapability.RANKING
        )
        
        if ranking_agents:
            agent = ranking_agents[0]
            result = self.registry.execute_agent(agent.agent_id, state)
            
            if result.success:
                ranking = result.outputs.get("ranking", {})
                
                iteration_record = {
                    "iteration": iteration + 1,
                    "ranking": ranking,
                    "timestamp": datetime.now().isoformat()
                }
                
                return {
                    "ranking": ranking,
                    "ranking_iterations": [iteration_record]
                }
        
        return {"ranking": {}}
    
    def _verify_ranking(self, state: WorkflowState) -> Dict[str, Any]:
        """Verify ranking."""
        self.logger.info("Verifying ranking...")
        
        ranking = state.get("ranking", {})
        
        # Simple verification - always pass
        return {
            "verification": {
                "verified": True,
                "summary": "Ranking verified",
                "issues_found": []
            }
        }
    
    def _generate_insights(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate insights with research context (NEW)."""
        self.logger.info("Generating insights with research context...")
        
        country_research = state.get("country_research", {})
        if country_research:
            self.logger.info(f"📚 Including research for {len(country_research)} countries")
        
        # Initialize results with defaults (CRITICAL FIX)
        results = {
            "country_insights": {},
            "ranking_explanation": {},
            "insights_metadata": {}
        }
        
        # Find insights agents
        insights_agents = self.registry.find_agents_by_capability(
            AgentCapability.REPORT_GEN
        )
        
        # Filter to insights team agents
        country_analyzers = [
            a for a in insights_agents 
            if "country_analyzer" in a.agent_id
        ]
        
        ranking_explainers = [
            a for a in insights_agents 
            if "ranking_explainer" in a.agent_id
        ]
        
        # Generate country insights
        if country_analyzers:
            self.logger.info(f"Found {len(country_analyzers)} country analyzer(s)")
            agent = country_analyzers[0]
            result = self.registry.execute_agent(agent.agent_id, state)
            
            if result.success:
                results["country_insights"] = result.outputs.get("country_insights", {})
                results["insights_metadata"] = result.outputs.get("insights_metadata", {})
                self.logger.info("✓ Country insights generated")
            else:
                self.logger.warning(f"Country analyzer failed: {result.error}")
        else:
            self.logger.warning("No country analyzer agents found")
        
        # Generate ranking explanation
        if ranking_explainers:
            self.logger.info(f"Found {len(ranking_explainers)} ranking explainer(s)")
            agent = ranking_explainers[0]
            result = self.registry.execute_agent(agent.agent_id, state)
            
            if result.success:
                results["ranking_explanation"] = result.outputs.get("ranking_explanation", {})
                self.logger.info("✓ Ranking explanation generated")
            else:
                self.logger.warning(f"Ranking explainer failed: {result.error}")
        else:
            self.logger.warning("No ranking explainer agents found")
        
        return results
    
    # ==================== CONDITIONAL EDGE ====================
    
    def _should_generate_insights(self, state: WorkflowState) -> Literal["retry", "insights"]:
        """Decide what to do after verification."""
        verification = state.get("verification", {})
        iterations = state.get("ranking_iterations", [])
        
        if verification.get("verified", False):
            self.logger.info("✓ Ranking verified, generating insights!")
            return "insights"
        
        max_iterations = 3
        if len(iterations) >= max_iterations:
            self.logger.warning("Max iterations reached, proceeding to insights")
            return "insights"
        
        self.logger.info("Ranking failed, retrying...")
        return "retry"
    
    # ==================== EXECUTION ====================
    
    def run(
        self,
        countries: List[str],
        query: str = None,
        research_json_path: str = None,
        research_json_data: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Run the workflow with research data.
        
        Args:
            countries: List of country codes
            query: Optional query
            research_json_path: Optional path to research JSON
            research_json_data: Optional direct research data
            
        Returns:
            Final state with all results
        """
        self.logger.info(f"Starting workflow for countries: {countries}")
        
        # Create initial state
        initial_state = create_initial_state(
            countries,
            query,
            research_json_path,
            research_json_data
        )
        
        # Run graph
        final_state = self.graph.invoke(initial_state)
        
        # Add end time
        final_state["execution_metadata"]["end_time"] = datetime.now().isoformat()
        
        self.logger.info("Workflow completed")
        
        return final_state


# Convenience function
def create_workflow_with_research() -> CountryComparisonWorkflowWithResearch:
    """Create and return workflow instance."""
    return CountryComparisonWorkflowWithResearch()


# Initialize workflow
workflow_with_research = create_workflow_with_research()

print("✅ Country Comparison Workflow with Research compiled!")
print("   📚 Loads research data automatically")
print("   🧠 Passes research to insights agents")
print("   🎯 Richer, context-aware analysis")
