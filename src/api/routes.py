"""
FastAPI Routes - Multi-Framework Showcase

Now demonstrates:
- Custom framework (NASA, Financial, Ranking)
- LangChain framework (GPT-4 insights) ✨ NEW
- LangGraph framework (Workflow orchestration)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging

from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

app = FastAPI(
    title="Multi-Framework AI Investment Platform",
    description="Demonstrates Custom + LangChain + LangGraph integration",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("API")

workflow = None


@app.on_event("startup")
async def startup_event():
    """Initialize workflow with multi-framework agents."""
    global workflow
    
    logger.info("Starting Multi-Framework API v2.1...")
    
    # Register agents from different frameworks
    logger.info("Registering agents...")
    import business_units.data_team.nasa_agent              # Custom
    import business_units.finance_team.financial_agents     # Custom
    import business_units.insights_team.gpt4_agents         # LangChain ✨
    import business_units.ranking_team.agents               # Custom
    
    workflow = CountryComparisonWorkflow()  # LangGraph
    
    registry = get_registry()
    stats = registry.get_statistics()
    
    # Show framework breakdown
    logger.info(f"✓ Registered {stats['total_agents']} agents:")
    for framework, count in stats['by_framework'].items():
        logger.info(f"  - {framework}: {count} agents")
    
    logger.info("API ready! 🚀")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Multi-Framework AI Investment Platform",
        "version": "2.1.0",
        "frameworks": {
            "custom": "NASA, Financial, Ranking agents",
            "langchain": "GPT-4 insight agents ✨ NEW",
            "langgraph": "Main workflow orchestration"
        },
        "features": [
            "Real NASA POWER data",
            "Financial modeling (IRR, LCOE, NPV)",
            "LangChain GPT-4 insights with cost tracking ✨",
            "Multi-agent orchestration"
        ],
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check with framework breakdown."""
    registry = get_registry()
    stats = registry.get_statistics()
    
    return {
        "status": "healthy",
        "agents_registered": stats['total_agents'],
        "business_units": len(stats['by_business_unit']),
        "frameworks": stats['by_framework'],  # Shows Custom + LangChain
        "capabilities": list(stats['by_capability'].keys())
    }


@app.get("/agents")
async def list_agents(
    business_unit: Optional[str] = Query(None),
    framework: Optional[str] = Query(None)
):
    """List all registered agents with framework info."""
    registry = get_registry()
    
    if business_unit:
        agents = registry.find_agents_by_business_unit(business_unit)
    else:
        agents = registry.list_agents()
    
    # Filter by framework if requested
    if framework:
        agents = [a for a in agents if a.framework.value == framework]
    
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
        "agents": agents_list,
        "frameworks_used": list(set(a['framework'] for a in agents_list))
    }


@app.post("/api/v1/analyze-investments")
async def analyze_investments(
    countries: List[str] = Query(..., min_items=2, max_items=10),
    query: Optional[str] = Query(None),
    include_ai_insights: bool = Query(True, description="Include LangChain GPT-4 insights")
):
    """
    Complete investment analysis with multi-framework agents.
    
    Frameworks used:
    - Custom: Data fetching, financial calculations, ranking
    - LangChain: GPT-4 powered insights with cost tracking ✨
    - LangGraph: Workflow orchestration
    """
    global workflow
    
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    try:
        logger.info(f"Starting analysis for: {countries}")
        
        # Run main workflow (LangGraph + Custom agents)
        result = workflow.run(countries=countries, query=query)
        
        # Add LangChain insights if requested
        insights_metadata = None
        if include_ai_insights:
            logger.info("Generating LangChain AI insights...")
            
            from business_units.insights_team.gpt4_agents import (
                langchain_country_analyzer,
                langchain_ranking_explainer
            )
            
            insights = langchain_country_analyzer(result)
            result.update(insights)
            
            explanation = langchain_ranking_explainer(result)
            result.update(explanation)
            
            # Extract cost metadata
            insights_metadata = result.get('insights_metadata', {})
            
            logger.info(
                f"✓ AI insights generated "
                f"(tokens: {insights_metadata.get('total_tokens', 0)}, "
                f"cost: ${insights_metadata.get('total_cost_usd', 0):.4f})"
            )
        
        logger.info("Analysis completed successfully")
        
        return {
            "success": True,
            "data": {
                "summary": {
                    "countries_analyzed": len(result.get('country_reports', {})),
                    "top_recommendation": result.get('ranking', {}).get('ranked_countries', [{}])[0].get('country_code'),
                    "timestamp": result.get('execution_metadata', {}).get('end_time'),
                    "ai_insights_included": include_ai_insights,
                    "frameworks_used": ["custom", "langgraph"] + (["langchain"] if include_ai_insights else [])
                },
                "country_reports": result.get('country_reports', {}),
                "ranking": result.get('ranking', {}),
                "ranking_explanation": result.get('ranking_explanation') if include_ai_insights else None,
                "country_insights": result.get('country_insights') if include_ai_insights else None,
                "insights_metadata": insights_metadata,  # LangChain cost tracking ✨
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


@app.get("/api/v1/frameworks")
async def list_frameworks():
    """List all frameworks used in the system."""
    registry = get_registry()
    stats = registry.get_statistics()
    
    return {
        "frameworks": {
            "custom": {
                "description": "Custom Python agents",
                "count": stats['by_framework'].get('custom', 0),
                "used_for": ["Data fetching", "Financial calculations", "Simple ranking"]
            },
            "langchain": {
                "description": "LangChain AI agents",
                "count": stats['by_framework'].get('langchain', 0),
                "used_for": ["GPT-4 insights", "Cost tracking", "Prompt management"],
                "features": ["Automatic retry", "Token tracking", "Output parsing"]
            },
            "langgraph": {
                "description": "LangGraph workflow orchestration",
                "count": 1,  # Main workflow
                "used_for": ["State machine", "Conditional routing", "Workflow management"]
            }
        },
        "total_agents": stats['total_agents']
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
