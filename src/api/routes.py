"""
FastAPI Routes for Multi-Agent System

Exposes the LangGraph workflow as REST API endpoints.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging

from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.state.shared_state import CountryAnalysisRequest, CountryAnalysisResponse
from src.registry.agent_registry import get_registry


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Renewable Energy Analysis",
    description="LangGraph-based multi-agent system for renewable energy investment analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger
logger = logging.getLogger("API")

# Global workflow instance
workflow = None


@app.on_event("startup")
async def startup_event():
    """Initialize workflow on startup."""
    global workflow
    
    logger.info("Starting Multi-Agent API...")
    
    # Register business unit agents
    logger.info("Registering business unit agents...")
    import business_units.ranking_team.agents
    # Add more as needed:
    # import business_units.research_team.agents
    # import business_units.analysis_team.agents
    
    # Create workflow
    logger.info("Creating LangGraph workflow...")
    workflow = CountryComparisonWorkflow()
    
    # Show registered agents
    registry = get_registry()
    stats = registry.get_statistics()
    logger.info(f"Registered {stats['total_agents']} agents from "
                f"{len(stats['by_business_unit'])} business units")
    
    logger.info("API ready!")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Multi-Agent Renewable Energy Analysis API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    registry = get_registry()
    stats = registry.get_statistics()
    
    return {
        "status": "healthy",
        "agents_registered": stats['total_agents'],
        "business_units": len(stats['by_business_unit'])
    }


@app.get("/agents")
async def list_agents(
    business_unit: Optional[str] = Query(None, description="Filter by business unit"),
    capability: Optional[str] = Query(None, description="Filter by capability")
):
    """List all registered agents."""
    registry = get_registry()
    
    # Get agents
    if business_unit:
        agents = registry.find_agents_by_business_unit(business_unit)
    else:
        agents = registry.list_agents()
    
    # Convert to dict
    agents_list = [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "description": a.description,
            "framework": a.framework.value,
            "capabilities": [c.value for c in a.capabilities],
            "business_unit": a.business_unit,
            "version": a.version
        }
        for a in agents
    ]
    
    return {
        "total": len(agents_list),
        "agents": agents_list
    }


@app.post("/api/v1/compare-countries")
async def compare_countries(
    countries: List[str] = Query(..., min_items=2, max_items=10, description="Country codes to compare"),
    query: Optional[str] = Query(None, description="Optional natural language query")
):
    """
    Compare renewable energy investments across countries.
    
    Uses LangGraph workflow to orchestrate multiple agents.
    """
    global workflow
    
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    try:
        logger.info(f"Starting comparison for countries: {countries}")
        
        # Run workflow
        result = workflow.run(countries=countries, query=query)
        
        logger.info(f"Comparison completed successfully")
        
        return {
            "success": True,
            "data": {
                "comparison_summary": {
                    "countries_analyzed": len(result.get('country_reports', {})),
                    "timestamp": result.get('execution_metadata', {}).get('end_time')
                },
                "country_reports": result.get('country_reports', {}),
                "ranking": result.get('ranking', {}),
                "verification": result.get('verification', {}),
                "dual_recommendation": result.get('dual_recommendation'),
                "ranking_iterations": result.get('ranking_iterations', []),
                "execution_metadata": result.get('execution_metadata', {})
            }
        }
    
    except Exception as e:
        logger.error(f"Comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflow/graph")
async def get_workflow_graph():
    """Get visual representation of the workflow graph."""
    # This would return a mermaid diagram or image
    return {
        "message": "Graph visualization not implemented yet",
        "nodes": [
            "validate_input",
            "load_locations",
            "analyze_locations",
            "aggregate_countries",
            "rank_countries",
            "verify_ranking",
            "generate_dual_recommendation"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
