"""
FastAPI Routes for Multi-Agent System - WITH AI INSIGHTS
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging

from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

app = FastAPI(
    title="AI-Powered Renewable Energy Analysis",
    description="Multi-agent system with NASA data + Financial models + GPT-4 insights",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("API")

# Global workflow instance
workflow = None


@app.on_event("startup")
async def startup_event():
    """Initialize workflow on startup."""
    global workflow
    
    logger.info("Starting Multi-Agent API v2.0...")
    
    # Register all business unit agents
    logger.info("Registering agents...")
    import business_units.data_team.nasa_agent
    import business_units.finance_team.financial_agents
    import business_units.insights_team.gpt4_agents
    import business_units.ranking_team.agents
    # Add more as needed:
    
    # Create workflow
    logger.info("Creating LangGraph workflow...")
    workflow = CountryComparisonWorkflow()
    
    # Show registered agents
    registry = get_registry()
    stats = registry.get_statistics()
    logger.info(f"✓ Registered {stats['total_agents']} agents from {len(stats['by_business_unit'])} teams")
    
    logger.info("API ready! 🚀")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI-Powered Renewable Energy Analysis API",
        "version": "2.0.0",
        "features": [
            "Real NASA POWER data",
            "Financial modeling (IRR, LCOE, NPV)",
            "GPT-4 insights",
            "Multi-agent orchestration"
        ],
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
        "business_units": len(stats['by_business_unit']),
        "capabilities": list(stats['by_capability'].keys())
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
    
    return {"total": len(agents_list), "agents": agents_list}


@app.post("/api/v1/analyze-investments")
async def analyze_investments(
    countries: List[str] = Query(..., min_items=2, max_items=10),
    query: Optional[str] = Query(None),
    include_ai_insights: bool = Query(True, description="Include GPT-4 insights")
):
    """
    Comprehensive investment analysis with AI insights.
    
    Features:
    - Real NASA POWER data
    - Financial calculations (IRR, LCOE, NPV)
    - Country rankings
    - Optional GPT-4 insights
    """
    global workflow
    
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    try:
        logger.info(f"Starting analysis for: {countries}")
        
        # Run main workflow
        result = workflow.run(countries=countries, query=query)
        
        # Add AI insights if requested
        if include_ai_insights:
            logger.info("Generating AI insights...")
            
            from business_units.insights_team.gpt4_agents import (
                gpt4_country_analyzer,
                gpt4_ranking_explainer
            )
            
            insights = gpt4_country_analyzer(result)
            result.update(insights)
            
            explanation = gpt4_ranking_explainer(result)
            result.update(explanation)
            
            logger.info("✓ AI insights generated")
        
        logger.info("Analysis completed successfully")
        
        return {
            "success": True,
            "data": {
                "summary": {
                    "countries_analyzed": len(result.get('country_reports', {})),
                    "top_recommendation": result.get('ranking', {}).get('ranked_countries', [{}])[0].get('country_code'),
                    "timestamp": result.get('execution_metadata', {}).get('end_time'),
                    "ai_insights_included": include_ai_insights
                },
                "country_reports": result.get('country_reports', {}),
                "ranking": result.get('ranking', {}),
                "ranking_explanation": result.get('ranking_explanation') if include_ai_insights else None,
                "country_insights": result.get('country_insights') if include_ai_insights else None,
                "verification": result.get('verification', {}),
                "execution_metadata": result.get('execution_metadata', {})
            }
        }
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/countries/supported")
async def supported_countries():
    """Get list of supported countries."""
    from business_units.data_team.nasa_agent import COUNTRY_LOCATIONS
    
    return {
        "total": len(COUNTRY_LOCATIONS),
        "countries": [
            {
                "code": code,
                "locations": {
                    "solar": locs["solar"]["name"],
                    "wind": locs["wind"]["name"]
                }
            }
            for code, locs in COUNTRY_LOCATIONS.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
