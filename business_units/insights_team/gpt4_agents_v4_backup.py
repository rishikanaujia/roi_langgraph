"""
Insights Team - ReAct Agents with Reasoning

Phase 2: Upgraded to ReAct (Reasoning + Acting) agents

ReAct agents:
- ✅ Think through problems step-by-step
- ✅ Decide WHEN to use tools (not always)
- ✅ Show reasoning traces for transparency
- ✅ Multi-step problem solving
- ✅ More cost-effective (search only when needed)

Key Improvements over v3.0:
- Agents decide whether to search (intelligence)
- Visible reasoning process (transparency)
- Better cost efficiency (search on-demand)
- Multi-turn interactions with tools
- Handles complex queries better
"""

import os
import logging
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_community.callbacks import get_openai_callback

# Tavily Search
from tavily import TavilyClient

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("ReActAgents")


# ============================================================================
# Configuration
# ============================================================================

# LLM for ReAct agents (using GPT-4o for reasoning capability)
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_retries=3,
    request_timeout=120  # Longer timeout for agent loops
)

# Tavily Search Client
tavily_client = None
search_available = False

try:
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        tavily_client = TavilyClient(api_key=tavily_api_key)
        search_available = True
        logger.info("✓ Tavily search available for ReAct agents")
    else:
        logger.warning("⚠️  TAVILY_API_KEY not found - ReAct agents will work without search")
except Exception as e:
    logger.warning(f"⚠️  Tavily initialization failed: {str(e)}")


# ============================================================================
# Tool Definitions for ReAct Agents
# ============================================================================

def search_renewable_energy_news(query: str) -> str:
    """
    Search the web for recent renewable energy news, policy updates, and market information.
    
    Use this tool when you need:
    - Recent policy changes or announcements
    - Market conditions or investment trends
    - Breaking news affecting renewable energy
    - Regulatory updates
    
    Args:
        query: Search query (e.g., "India renewable energy policy 2025")
    
    Returns:
        Formatted search results with sources
    """
    if not tavily_client:
        return "Search tool not available. Proceed with analysis using provided data."
    
    try:
        logger.info(f"🔍 ReAct Agent searching: '{query}'")
        
        response = tavily_client.search(
            query=query,
            max_results=3,
            search_depth="basic",
            include_answer=False
        )
        
        results = response.get('results', [])
        
        if not results:
            return "No relevant information found. Proceed with analysis using provided data."
        
        # Format results
        formatted = "Search Results:\n\n"
        for i, item in enumerate(results, 1):
            formatted += f"{i}. {item.get('title', 'No title')}\n"
            formatted += f"   {item.get('content', 'No content')[:250]}...\n"
            formatted += f"   Source: {item.get('url', 'No URL')}\n\n"
        
        logger.info(f"✓ ReAct Agent found {len(results)} results")
        return formatted
    
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return f"Search failed: {str(e)}. Proceed with analysis using provided data."


# Create LangChain Tool
search_tool = Tool(
    name="search_renewable_energy_news",
    description="""Search the web for recent renewable energy news, policies, and market information.
    
Use this tool when you need CURRENT information about:
- Policy changes or government announcements
- Market trends or investment news
- Regulatory updates
- Breaking news affecting the renewable energy sector

Input: A search query string (e.g., "Brazil renewable energy incentives 2025")
Output: Recent news articles and information with sources

IMPORTANT: Only use this tool when current information would significantly improve your analysis.
For stable facts (resource quality, basic financial metrics), use the provided data.""",
    func=search_renewable_energy_news
)


# ============================================================================
# ReAct Agent: Country Analyzer
# ============================================================================

# ReAct prompt template - this is the "brain" of the agent
REACT_COUNTRY_ANALYZER_PROMPT = PromptTemplate.from_template("""You are a renewable energy investment analyst using a ReAct (Reasoning + Acting) approach.

You have access to tools to gather additional information when needed.

AVAILABLE TOOLS:
{tools}

TOOL NAMES: {tool_names}

ANALYSIS TASK:
Analyze this renewable energy investment opportunity:

**Country:** {country_code}

**Financial Metrics:**
- Average IRR: {avg_irr:.2f}%
- Average LCOE: ${avg_lcoe:.2f}/MWh
- Average NPV: ${avg_npv:.1f}M

**Project Details:**
{projects_detail}

**REASONING PROCESS:**

Use this format for your reasoning:

Thought: [Your reasoning about what to do next]
Action: [The action to take - either use a tool or provide Final Answer]
Action Input: [The input for the action]
Observation: [The result of the action]
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have enough information to provide a comprehensive answer
Final Answer: [Your complete analysis]

**WHEN TO SEARCH:**
- Search if you need RECENT policy changes or announcements
- Search if market conditions have likely changed recently
- Search if there are regulatory uncertainties
- DON'T search for stable facts already provided (resource quality, financial metrics)
- DON'T search if the financial data is clear and recent

**REQUIRED IN FINAL ANSWER (4-5 sentences):**
1. **Resource Quality Assessment:** Evaluate solar/wind resources
2. **Financial Viability:** Assess IRR, LCOE, NPV with specific interpretation
3. **Policy & Market Context:** Consider recent developments (if you searched)
4. **Key Risks or Opportunities:** Identify critical factors
5. **Investment Recommendation:** Clear BUY/HOLD/AVOID with justification

Be data-driven, cite sources if you searched, and provide actionable recommendations.

{agent_scratchpad}""")


def create_country_analyzer_agent() -> AgentExecutor:
    """
    Create a ReAct agent for country analysis.
    
    Returns:
        AgentExecutor ready to analyze countries
    """
    tools = [search_tool] if search_available else []
    
    # Create ReAct agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=REACT_COUNTRY_ANALYZER_PROMPT
    )
    
    # Wrap in executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # Show reasoning traces
        handle_parsing_errors=True,
        max_iterations=5,  # Limit reasoning loops
        max_execution_time=120,  # 2 minute timeout
        return_intermediate_steps=True  # Keep reasoning history
    )
    
    return agent_executor


@register_agent(
    agent_id="insights_team_country_analyzer_v4_react",
    name="GPT-4 Country Analyzer (ReAct)",
    description="ReAct agent that reasons about when to search for current information",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",
    version="4.0.0",
    tags=["gpt-4", "react", "reasoning", "web-search", "intelligent"]
)
def react_country_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze countries using ReAct agents with reasoning.
    
    New in v4.0 (ReAct):
    - Agent decides when to search (not always)
    - Visible reasoning process
    - More cost-effective
    - Multi-step problem solving
    """
    country_reports = state.get("country_reports", {})
    country_insights = {}
    
    # Create agent once (reuse across countries)
    agent_executor = create_country_analyzer_agent()
    
    total_tokens = 0
    total_cost = 0.0
    total_searches = 0
    
    for country_code, report in country_reports.items():
        metrics = report.get("aggregate_metrics", {})
        analyses = report.get("location_analyses", [])
        
        # Build project details
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
        
        try:
            logger.info(f"🤖 ReAct Agent analyzing {country_code}...")
            
            # Run ReAct agent with cost tracking
            with get_openai_callback() as cb:
                result = agent_executor.invoke({
                    "country_code": country_code,
                    "avg_irr": metrics.get('average_irr', 0),
                    "avg_lcoe": metrics.get('average_lcoe', 0),
                    "avg_npv": metrics.get('average_npv', 0) / 1e6,
                    "projects_detail": projects_detail
                })
                
                # Extract results
                analysis_text = result.get('output', 'Analysis unavailable')
                intermediate_steps = result.get('intermediate_steps', [])
                
                # Count searches performed
                searches_performed = sum(
                    1 for step in intermediate_steps 
                    if step[0].tool == 'search_renewable_energy_news'
                )
                total_searches += searches_performed
                
                # Extract sources from search results
                sources = []
                for step in intermediate_steps:
                    if step[0].tool == 'search_renewable_energy_news':
                        observation = step[1]
                        # Extract URLs from observation
                        import re
                        urls = re.findall(r'Source: (https?://[^\s]+)', observation)
                        sources.extend(urls)
                
                total_tokens += cb.total_tokens
                total_cost += cb.total_cost
                
                logger.info(
                    f"✓ ReAct Agent completed {country_code} "
                    f"(tokens: {cb.total_tokens}, searches: {searches_performed}, "
                    f"cost: ${cb.total_cost:.4f})"
                )
                
                # Store insights
                country_insights[country_code] = {
                    "analysis": analysis_text,
                    "confidence": "high" if searches_performed > 0 else "medium",
                    "source": "GPT-4o ReAct Agent",
                    "tokens_used": cb.total_tokens,
                    "cost_usd": round(cb.total_cost, 4),
                    "web_searches_performed": searches_performed,
                    "sources": sources[:5],  # Limit to 5 sources
                    "reasoning_steps": len(intermediate_steps),
                    "agent_decided_to_search": searches_performed > 0
                }
        
        except Exception as e:
            logger.error(f"ReAct Agent failed for {country_code}: {str(e)}")
            country_insights[country_code] = {
                "analysis": f"Analysis unavailable: {str(e)}",
                "confidence": "low",
                "error": str(e)
            }
    
    logger.info(
        f"ReAct Analysis Complete - "
        f"Tokens: {total_tokens}, "
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
            "framework": "langchain-react",
            "search_tool": "tavily" if search_available else "none",
            "agent_type": "react"
        }
    }


# ============================================================================
# ReAct Agent: Ranking Explainer
# ============================================================================

REACT_RANKING_EXPLAINER_PROMPT = PromptTemplate.from_template("""You are explaining investment rankings to executives using a ReAct approach.

AVAILABLE TOOLS:
{tools}

TOOL NAMES: {tool_names}

RANKING TO EXPLAIN:
{ranking_summary}

**YOUR TASK:**
Explain this ranking clearly to C-level executives.

**REASONING PROCESS:**

Thought: [Your reasoning about what information you need]
Action: [Use a tool or provide Final Answer]
Action Input: [Input for the action]
Observation: [Result]
... (repeat as needed)
Thought: I have enough information to explain
Final Answer: [Your explanation]

**WHEN TO SEARCH:**
- Search if you need context about why a country is ranked high/low
- Search if there are recent policy changes affecting rankings
- DON'T search if the metrics clearly explain the ranking
- DON'T search for general renewable energy information

**REQUIRED IN FINAL ANSWER (4-5 sentences):**
1. Why is #1 the top choice? (cite specific metrics)
2. What distinguishes top performers?
3. What are the key decision factors?
4. Any concerns or caveats executives should know?

Be clear, specific with numbers, and actionable.

{agent_scratchpad}""")


def create_ranking_explainer_agent() -> AgentExecutor:
    """Create ReAct agent for ranking explanation."""
    tools = [search_tool] if search_available else []
    
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=REACT_RANKING_EXPLAINER_PROMPT
    )
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=4,
        max_execution_time=60,
        return_intermediate_steps=True
    )
    
    return agent_executor


@register_agent(
    agent_id="insights_team_ranking_explainer_v3_react",
    name="GPT-4 Ranking Explainer (ReAct)",
    description="ReAct agent that reasons about ranking explanations",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",
    version="3.0.0",
    tags=["gpt-4", "react", "reasoning"]
)
def react_ranking_explainer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Explain rankings using ReAct agent."""
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
    
    # Build ranking summary
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
        logger.info("🤖 ReAct Agent explaining rankings...")
        
        agent_executor = create_ranking_explainer_agent()
        
        with get_openai_callback() as cb:
            result = agent_executor.invoke({
                "ranking_summary": ranking_summary
            })
            
            explanation_text = result.get('output', 'Explanation unavailable')
            intermediate_steps = result.get('intermediate_steps', [])
            
            searches_performed = sum(
                1 for step in intermediate_steps 
                if step[0].tool == 'search_renewable_energy_news'
            )
            
            logger.info(
                f"✓ ReAct explanation complete "
                f"(tokens: {cb.total_tokens}, searches: {searches_performed})"
            )
            
            return {
                "ranking_explanation": {
                    "explanation": explanation_text,
                    "methodology": ranking.get("methodology", "Weighted scoring"),
                    "confidence": "high",
                    "source": "GPT-4o ReAct Agent",
                    "tokens_used": cb.total_tokens,
                    "cost_usd": round(cb.total_cost, 4),
                    "reasoning_steps": len(intermediate_steps)
                }
            }
    
    except Exception as e:
        logger.error(f"ReAct explanation failed: {str(e)}")
        return {
            "ranking_explanation": {
                "explanation": "Explanation unavailable",
                "error": str(e),
                "confidence": "low"
            }
        }


# ============================================================================
# Module Initialization
# ============================================================================

os.makedirs("business_units/insights_team", exist_ok=True)
with open("business_units/insights_team/__init__.py", "w") as f:
    f.write("")

print("✅ ReAct Agents registered!")
print("   - Country Analyzer (v4.0 - ReAct with reasoning)")
print("   - Ranking Explainer (v3.0 - ReAct)")
print("   🧠 Features: Intelligent reasoning, tool decisions, transparency")
print(f"   🔍 Web search: {'Available' if search_available else 'Disabled'}")
