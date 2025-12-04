"""
Insights Team - ReAct Agents with Fixed Cost Tracking

Phase 2: ReAct agents with proper token/cost tracking

This version fixes the cost tracking issue by using a custom callback
handler that properly captures token usage from LLM calls within AgentExecutor.

Key Improvements:
- ✅ Accurate token counting
- ✅ Proper cost calculation
- ✅ Per-country cost breakdown
- ✅ Total spend tracking
- ✅ All ReAct functionality preserved
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# Tavily Search
from tavily import TavilyClient

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("ReActAgents")


# ============================================================================
# Custom Callback Handler for Cost Tracking
# ============================================================================

class CostTrackingCallback(BaseCallbackHandler):
    """
    Custom callback handler that properly tracks token usage and costs.
    
    This fixes the issue where AgentExecutor doesn't propagate token
    usage through the standard get_openai_callback().
    """
    
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost = 0.0
        self.llm_calls = 0
        
        # GPT-4o pricing (as of Dec 2024)
        self.prompt_token_cost = 0.0000025  # $0.0025 per 1K tokens
        self.completion_token_cost = 0.00001  # $0.01 per 1K tokens
    
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Called when LLM finishes."""
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            
            prompt_tokens = token_usage.get('prompt_tokens', 0)
            completion_tokens = token_usage.get('completion_tokens', 0)
            total_tokens = token_usage.get('total_tokens', 0)
            
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            self.total_tokens += total_tokens
            
            # Calculate cost
            prompt_cost = prompt_tokens * self.prompt_token_cost
            completion_cost = completion_tokens * self.completion_token_cost
            self.total_cost += prompt_cost + completion_cost
            
            self.llm_calls += 1
            
            logger.debug(
                f"LLM call {self.llm_calls}: "
                f"{prompt_tokens} prompt + {completion_tokens} completion = "
                f"{total_tokens} tokens (${prompt_cost + completion_cost:.4f})"
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary."""
        return {
            'total_tokens': self.total_tokens,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_cost_usd': round(self.total_cost, 4),
            'llm_calls': self.llm_calls
        }
    
    def reset(self):
        """Reset counters."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost = 0.0
        self.llm_calls = 0


# ============================================================================
# Configuration
# ============================================================================

# LLM for ReAct agents
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_retries=3,
    request_timeout=120
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
# Tool Definitions
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

Use this exact format:

Thought: [Your reasoning about what to do next]
Action: [Tool name OR "Final Answer"]
Action Input: [Input for the tool, OR your final analysis if Action is "Final Answer"]
Observation: [Result from tool - DO NOT write this, it will be provided]
... (repeat Thought/Action/Action Input/Observation as needed)

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


def create_country_analyzer_agent(callback_handler: CostTrackingCallback) -> AgentExecutor:
    """
    Create a ReAct agent for country analysis with cost tracking.
    
    Args:
        callback_handler: Custom callback for cost tracking
    
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
    
    # Wrap in executor with callback
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        max_execution_time=120,
        return_intermediate_steps=True,
        callbacks=[callback_handler]  # Add our custom callback
    )
    
    return agent_executor


@register_agent(
    agent_id="insights_team_country_analyzer_v4_react",
    name="GPT-4 Country Analyzer (ReAct)",
    description="ReAct agent with accurate cost tracking and intelligent reasoning",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",
    version="4.1.0",
    tags=["gpt-4", "react", "reasoning", "web-search", "cost-tracking"]
)
def react_country_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze countries using ReAct agents with accurate cost tracking.
    
    New in v4.1:
    - ✅ Fixed cost tracking (accurate tokens and costs)
    - ✅ Per-country cost breakdown
    - ✅ LLM call counting
    - ✅ All ReAct functionality preserved
    """
    country_reports = state.get("country_reports", {})
    country_insights = {}
    
    total_tokens = 0
    total_cost = 0.0
    total_searches = 0
    total_llm_calls = 0
    
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
            
            # Create callback for this country
            cost_callback = CostTrackingCallback()
            
            # Create agent with callback
            agent_executor = create_country_analyzer_agent(cost_callback)
            
            # Run agent
            result = agent_executor.invoke({
                "country_code": country_code,
                "avg_irr": metrics.get('average_irr', 0),
                "avg_lcoe": metrics.get('average_lcoe', 0),
                "avg_npv": metrics.get('average_npv', 0) / 1e6,
                "projects_detail": projects_detail
            })
            
            # Get cost summary from callback
            cost_summary = cost_callback.get_summary()
            
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
                    import re
                    urls = re.findall(r'Source: (https?://[^\s]+)', observation)
                    sources.extend(urls)
            
            # Update totals
            total_tokens += cost_summary['total_tokens']
            total_cost += cost_summary['total_cost_usd']
            total_llm_calls += cost_summary['llm_calls']
            
            logger.info(
                f"✓ ReAct Agent completed {country_code} - "
                f"Tokens: {cost_summary['total_tokens']} "
                f"({cost_summary['prompt_tokens']} prompt + "
                f"{cost_summary['completion_tokens']} completion), "
                f"Cost: ${cost_summary['total_cost_usd']:.4f}, "
                f"LLM calls: {cost_summary['llm_calls']}, "
                f"Searches: {searches_performed}"
            )
            
            # Store insights with accurate costs
            country_insights[country_code] = {
                "analysis": analysis_text,
                "confidence": "high" if searches_performed > 0 else "medium",
                "source": "GPT-4o ReAct Agent",
                "tokens_used": cost_summary['total_tokens'],
                "prompt_tokens": cost_summary['prompt_tokens'],
                "completion_tokens": cost_summary['completion_tokens'],
                "cost_usd": cost_summary['total_cost_usd'],
                "llm_calls": cost_summary['llm_calls'],
                "web_searches_performed": searches_performed,
                "sources": sources[:5],
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
        f"Total Tokens: {total_tokens}, "
        f"Total Cost: ${total_cost:.4f}, "
        f"LLM Calls: {total_llm_calls}, "
        f"Searches: {total_searches}"
    )
    
    return {
        "country_insights": country_insights,
        "insights_metadata": {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "total_llm_calls": total_llm_calls,
            "total_web_searches": total_searches,
            "model": "gpt-4o",
            "framework": "langchain-react",
            "search_tool": "tavily" if search_available else "none",
            "agent_type": "react",
            "cost_tracking": "accurate"
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

Use this exact format:

Thought: [Your reasoning]
Action: [Tool name OR "Final Answer"]
Action Input: [Input for tool, OR your final explanation if Action is "Final Answer"]
Observation: [Result - DO NOT write this]
... (repeat as needed)

**WHEN TO SEARCH:**
- Search if you need context about why a country is ranked high/low
- Search if there are recent policy changes affecting rankings
- DON'T search if the metrics clearly explain the ranking

**REQUIRED IN FINAL ANSWER (4-5 sentences):**
1. Why is #1 the top choice? (cite specific metrics)
2. What distinguishes top performers?
3. What are the key decision factors?
4. Any concerns or caveats?

Be clear, specific with numbers, and actionable.

{agent_scratchpad}""")


def create_ranking_explainer_agent(callback_handler: CostTrackingCallback) -> AgentExecutor:
    """Create ReAct agent for ranking explanation with cost tracking."""
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
        return_intermediate_steps=True,
        callbacks=[callback_handler]
    )
    
    return agent_executor


@register_agent(
    agent_id="insights_team_ranking_explainer_v3_react",
    name="GPT-4 Ranking Explainer (ReAct)",
    description="ReAct agent with accurate cost tracking for ranking explanations",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",
    version="3.1.0",
    tags=["gpt-4", "react", "reasoning", "cost-tracking"]
)
def react_ranking_explainer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Explain rankings using ReAct agent with accurate cost tracking."""
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
        
        # Create callback for ranking explainer
        cost_callback = CostTrackingCallback()
        
        agent_executor = create_ranking_explainer_agent(cost_callback)
        
        result = agent_executor.invoke({
            "ranking_summary": ranking_summary
        })
        
        # Get cost summary
        cost_summary = cost_callback.get_summary()
        
        explanation_text = result.get('output', 'Explanation unavailable')
        intermediate_steps = result.get('intermediate_steps', [])
        
        searches_performed = sum(
            1 for step in intermediate_steps 
            if step[0].tool == 'search_renewable_energy_news'
        )
        
        logger.info(
            f"✓ ReAct explanation complete - "
            f"Tokens: {cost_summary['total_tokens']}, "
            f"Cost: ${cost_summary['total_cost_usd']:.4f}, "
            f"LLM calls: {cost_summary['llm_calls']}, "
            f"Searches: {searches_performed}"
        )
        
        return {
            "ranking_explanation": {
                "explanation": explanation_text,
                "methodology": ranking.get("methodology", "Weighted scoring"),
                "confidence": "high",
                "source": "GPT-4o ReAct Agent",
                "tokens_used": cost_summary['total_tokens'],
                "prompt_tokens": cost_summary['prompt_tokens'],
                "completion_tokens": cost_summary['completion_tokens'],
                "cost_usd": cost_summary['total_cost_usd'],
                "llm_calls": cost_summary['llm_calls'],
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

print("✅ ReAct Agents with Fixed Cost Tracking registered!")
print("   - Country Analyzer (v4.1 - ReAct + accurate costs)")
print("   - Ranking Explainer (v3.1 - ReAct + accurate costs)")
print("   💰 Features: Accurate token/cost tracking, reasoning, web search")
print(f"   🔍 Web search: {'Available' if search_available else 'Disabled'}")
