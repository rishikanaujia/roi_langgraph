"""
Insights Team - LangChain Agents with Web Search

Phase 2 Enhancement: Added web search capability for real-time information.

New Features:
- ✅ Web search tool (Tavily) for recent news and policy updates
- ✅ Intelligent search query generation
- ✅ Source citation and transparency
- ✅ Fallback to analysis without search if needed
- ✅ Cost tracking for both LLM and search API calls
"""

import os
import logging
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.callbacks import get_openai_callback

# Tavily Search Tool
from tavily import TavilyClient

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("GPT4Agents")


# ============================================================================
# Configuration
# ============================================================================

# LangChain LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_retries=3,
    request_timeout=60
)

# Tavily Search Client
tavily_client = None
try:
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        tavily_client = TavilyClient(api_key=tavily_api_key)
        logger.info("✓ Tavily search client initialized")
    else:
        logger.warning("⚠️  TAVILY_API_KEY not found - web search disabled")
except Exception as e:
    logger.warning(f"⚠️  Tavily initialization failed: {str(e)} - web search disabled")


# ============================================================================
# Web Search Helper Functions
# ============================================================================

def generate_search_query(country_code: str, context: str) -> str:
    """
    Generate an intelligent search query for the country.
    
    Args:
        country_code: Country code (e.g., "USA", "IND")
        context: Brief context about what we're analyzing
    
    Returns:
        Search query string
    """
    # Map country codes to full names
    country_names = {
        "USA": "United States",
        "DEU": "Germany",
        "IND": "India",
        "CHN": "China",
        "BRA": "Brazil",
        "AUS": "Australia",
        "GBR": "United Kingdom",
        "CAN": "Canada",
        "FRA": "France",
        "JPN": "Japan"
    }
    
    country_name = country_names.get(country_code, country_code)
    
    # Generate focused search query
    query = f"{country_name} renewable energy policy investment news 2025"
    
    return query


def search_web(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search the web using Tavily.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
    
    Returns:
        List of search results with title, content, and URL
    """
    if not tavily_client:
        logger.warning("Tavily client not available, skipping search")
        return []
    
    try:
        logger.info(f"Searching web: '{query}'")
        
        # Tavily search with focus on recent, relevant content
        response = tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",  # "basic" or "advanced"
            include_answer=False,
            include_raw_content=False
        )
        
        results = []
        for item in response.get('results', []):
            results.append({
                'title': item.get('title', ''),
                'content': item.get('content', ''),
                'url': item.get('url', ''),
                'score': item.get('score', 0)
            })
        
        logger.info(f"✓ Found {len(results)} search results")
        return results
    
    except Exception as e:
        logger.error(f"Web search failed: {str(e)}")
        return []


def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    Format search results for inclusion in prompt.
    
    Args:
        results: List of search results
    
    Returns:
        Formatted string
    """
    if not results:
        return "No recent web information available."
    
    formatted = "**Recent Web Information:**\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"{i}. **{result['title']}**\n"
        formatted += f"   {result['content'][:200]}...\n"
        formatted += f"   Source: {result['url']}\n\n"
    
    return formatted


# ============================================================================
# Country Analyzer with Web Search
# ============================================================================

country_analysis_template = ChatPromptTemplate.from_messages([
    ("system", """You are a renewable energy investment analyst with expertise in:
- Solar and wind resource assessment
- Project financial modeling (IRR, LCOE, NPV)
- Investment risk analysis
- Renewable energy policy
- Market analysis and current events

When analyzing investments:
1. Consider both historical data AND recent developments
2. Cite specific sources when referencing recent information
3. Balance quantitative analysis with qualitative insights
4. Provide actionable recommendations

Be data-driven, current, and specific."""),
    
    ("user", """Analyze this renewable energy investment opportunity:

**Country:** {country_code}

**Aggregate Financial Metrics:**
- Average IRR: {avg_irr:.2f}%
- Average LCOE: ${avg_lcoe:.2f}/MWh
- Average NPV: ${avg_npv:.1f}M

**Individual Projects:**
{projects_detail}

{web_search_results}

**Required Analysis (4-5 sentences):**
1. **Resource Quality Assessment:** Evaluate solar/wind resource strength
2. **Financial Viability:** Assess IRR, LCOE, NPV - explain what they mean for investors
3. **Policy & Market Context:** Consider recent developments and policy changes (if available)
4. **Key Risks or Opportunities:** Identify critical factors including recent changes
5. **Investment Recommendation:** Provide clear BUY/HOLD/AVOID with justification

If recent web information is available, incorporate it and cite sources.
Be specific, data-driven, and actionable.""")
])

country_analysis_chain = country_analysis_template | llm | StrOutputParser()


@register_agent(
    agent_id="insights_team_country_analyzer_v3_with_search",
    name="GPT-4 Country Analyzer with Web Search",
    description="LangChain agent with web search for real-time policy and market information",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",
    version="3.0.0",
    tags=["gpt-4", "web-search", "tavily", "real-time"]
)
def langchain_country_analyzer_with_search(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze each country using LangChain with web search capability.
    
    New in v3.0:
    - Web search for recent policy updates and news
    - Source citation and transparency
    - Intelligent search query generation
    - Graceful fallback if search fails
    """
    country_reports = state.get("country_reports", {})
    country_insights = {}
    
    total_tokens = 0
    total_cost = 0.0
    total_searches = 0
    
    for country_code, report in country_reports.items():
        metrics = report.get("aggregate_metrics", {})
        analyses = report.get("location_analyses", [])
        
        # Build detailed projects summary
        projects_detail = ""
        for analysis in analyses:
            loc = analysis.get('location', {})
            resource = loc.get('resource_data', {})
            
            projects_detail += f"""
**{loc.get('name')}** ({loc.get('technology')}):
- IRR: {analysis.get('irr', 0):.2f}%
- LCOE: ${analysis.get('lcoe', 0):.2f}/MWh
- NPV: ${analysis.get('npv', 0)/1e6:.1f}M
- Capacity Factor: {analysis.get('capacity_factor', 0):.1%}
"""
            
            if loc.get('technology') == 'solar_pv':
                ghi = resource.get('ghi_kwh_m2_day', 0)
                projects_detail += f"- Solar Resource: {ghi:.2f} kWh/m²/day\n"
            else:
                ws = resource.get('wind_speed_100m_ms', 0)
                projects_detail += f"- Wind Speed (100m): {ws:.2f} m/s\n"
        
        # Perform web search for recent information
        search_results = []
        web_search_results_text = ""
        
        if tavily_client:
            try:
                search_query = generate_search_query(country_code, "investment")
                search_results = search_web(search_query, max_results=3)
                total_searches += 1
                
                if search_results:
                    web_search_results_text = format_search_results(search_results)
                    logger.info(f"✓ Web search completed for {country_code}")
                else:
                    web_search_results_text = "No recent web information found."
            except Exception as e:
                logger.warning(f"Search failed for {country_code}: {str(e)}")
                web_search_results_text = "Web search unavailable - analysis based on provided data only."
        else:
            web_search_results_text = "Web search not configured - analysis based on provided data only."
        
        # Generate analysis with LangChain
        try:
            logger.info(f"Generating enhanced analysis for {country_code}...")
            
            with get_openai_callback() as cb:
                analysis_text = country_analysis_chain.invoke({
                    "country_code": country_code,
                    "avg_irr": metrics.get('average_irr', 0),
                    "avg_lcoe": metrics.get('average_lcoe', 0),
                    "avg_npv": metrics.get('average_npv', 0) / 1e6,
                    "projects_detail": projects_detail,
                    "web_search_results": web_search_results_text
                })
                
                total_tokens += cb.total_tokens
                total_cost += cb.total_cost
                
                logger.info(
                    f"✓ Generated enhanced insights for {country_code} "
                    f"(tokens: {cb.total_tokens}, cost: ${cb.total_cost:.4f})"
                )
                
                # Store insights with metadata
                country_insights[country_code] = {
                    "analysis": analysis_text,
                    "confidence": "high" if search_results else "medium",
                    "source": "GPT-4o via LangChain + Web Search",
                    "tokens_used": cb.total_tokens,
                    "cost_usd": round(cb.total_cost, 4),
                    "web_search_performed": bool(search_results),
                    "sources": [r['url'] for r in search_results] if search_results else []
                }
        
        except Exception as e:
            logger.error(f"Failed to generate insights for {country_code}: {str(e)}")
            country_insights[country_code] = {
                "analysis": f"Analysis unavailable: {str(e)}",
                "confidence": "low",
                "error": str(e)
            }
    
    logger.info(
        f"Total usage - Tokens: {total_tokens}, "
        f"Cost: ${total_cost:.4f}, "
        f"Searches: {total_searches}"
    )
    
    return {
        "country_insights": country_insights,
        "insights_metadata": {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "total_web_searches": total_searches,
            "model": "gpt-4o",
            "framework": "langchain",
            "search_tool": "tavily" if tavily_client else "none"
        }
    }


# ============================================================================
# Ranking Explainer (unchanged from v2.0)
# ============================================================================

ranking_explanation_template = ChatPromptTemplate.from_messages([
    ("system", """You are explaining investment rankings to C-level executives.

Your audience:
- Busy executives who need clear, actionable recommendations
- Not technical experts - avoid jargon
- Need to understand WHY, not just WHAT

Your style:
- Clear and concise (4-5 sentences)
- Cite specific metrics to support claims
- Highlight key decision factors
- Note any concerns or caveats"""),
    
    ("user", """Explain this renewable energy investment ranking:

{ranking_summary}

**Provide a clear explanation covering:**

1. **Top Choice Justification:** Why is #1 ranked first? Cite specific metrics (IRR, LCOE, NPV)

2. **Key Differentiators:** What distinguishes the top performers from the rest?

3. **Decision Factors:** What are the 2-3 most important factors driving this ranking?

4. **Concerns/Caveats:** Are there any risks or concerns executives should know about?

**Format:** 4-5 clear sentences. Be specific with numbers. Make it actionable.""")
])

ranking_explanation_chain = ranking_explanation_template | llm | StrOutputParser()


@register_agent(
    agent_id="insights_team_ranking_explainer_v2_langchain",
    name="GPT-4 Ranking Explainer (LangChain)",
    description="LangChain-powered ranking explanation for executives",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",
    version="2.0.0"
)
def langchain_ranking_explainer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Explain ranking using LangChain."""
    ranking = state.get("ranking", {})
    country_reports = state.get("country_reports", {})
    
    ranked_countries = ranking.get("ranked_countries", [])
    
    if not ranked_countries:
        return {
            "ranking_explanation": {
                "explanation": "No ranking available",
                "confidence": "low"
            }
        }
    
    ranking_summary = "**Investment Ranking:**\n\n"
    
    for country in ranked_countries[:5]:
        code = country['country_code']
        report = country_reports.get(code, {})
        metrics = report.get('aggregate_metrics', {})
        
        ranking_summary += f"""**{country['rank']}. {code}** (Score: {country['overall_score']:.1f})
- IRR: {metrics.get('average_irr', 0):.2f}%
- LCOE: ${metrics.get('average_lcoe', 0):.2f}/MWh
- NPV: ${metrics.get('average_npv', 0)/1e6:.1f}M

"""
    
    try:
        logger.info("Generating ranking explanation...")
        
        with get_openai_callback() as cb:
            explanation_text = ranking_explanation_chain.invoke({
                "ranking_summary": ranking_summary
            })
            
            logger.info(
                f"✓ Generated ranking explanation "
                f"(tokens: {cb.total_tokens}, cost: ${cb.total_cost:.4f})"
            )
            
            return {
                "ranking_explanation": {
                    "explanation": explanation_text,
                    "methodology": ranking.get("methodology", "Weighted scoring"),
                    "confidence": "high",
                    "source": "GPT-4o via LangChain",
                    "tokens_used": cb.total_tokens,
                    "cost_usd": round(cb.total_cost, 4)
                }
            }
    
    except Exception as e:
        logger.error(f"Failed to generate ranking explanation: {str(e)}")
        return {
            "ranking_explanation": {
                "explanation": "Explanation unavailable",
                "error": str(e),
                "confidence": "low"
            }
        }


# Module initialization
import os
os.makedirs("business_units/insights_team", exist_ok=True)
with open("business_units/insights_team/__init__.py", "w") as f:
    f.write("")

print("✅ LangChain GPT-4 Agents with Web Search registered!")
print("   - Country Analyzer (v3.0 - with Tavily search)")
print("   - Ranking Explainer (v2.0 - LangChain)")
print("   📊 Features: Web search, source citation, cost tracking")
