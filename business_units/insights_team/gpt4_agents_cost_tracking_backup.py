"""
Insights Team - ReAct Agents with Working Cost Tracking

Final version that ACTUALLY works:
- Removed invalid return_usage parameter
- Added missing contact parameter
- Simplified cost tracking that works reliably
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
# Working Cost Tracking Callback
# ============================================================================

class WorkingCostTracker(BaseCallbackHandler):
    """
    Simplified cost tracker that actually works.
    Focuses on capturing from llm_output which is reliably available.
    """
    
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost = 0.0
        self.llm_calls = 0
        
        # GPT-4o pricing (Dec 2024)
        self.prompt_token_cost = 0.0000025  # $2.50 per 1M tokens
        self.completion_token_cost = 0.00001  # $10.00 per 1M tokens
    
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Capture token usage from LLM response."""
        try:
            # Get token usage from llm_output
            if hasattr(response, 'llm_output') and response.llm_output:
                token_usage = response.llm_output.get('token_usage', {})
                
                if token_usage:
                    prompt_tokens = token_usage.get('prompt_tokens', 0)
                    completion_tokens = token_usage.get('completion_tokens', 0)
                    total_tokens = token_usage.get('total_tokens', 0)
                    
                    self.prompt_tokens += prompt_tokens
                    self.completion_tokens += completion_tokens
                    self.total_tokens += total_tokens
                    
                    # Calculate cost
                    prompt_cost = prompt_tokens * self.prompt_token_cost
                    completion_cost = completion_tokens * self.completion_token_cost
                    call_cost = prompt_cost + completion_cost
                    
                    self.total_cost += call_cost
                    self.llm_calls += 1
                    
                    logger.info(
                        f"💰 LLM call {self.llm_calls}: {total_tokens:,} tokens "
                        f"(${call_cost:.4f})"
                    )
                    return
            
            # If no token usage found, estimate from text length
            self.llm_calls += 1
            estimated_tokens = 500  # Conservative estimate
            
            if hasattr(response, 'generations') and response.generations:
                total_chars = sum(
                    len(gen.text) 
                    for gen_list in response.generations 
                    for gen in gen_list
                )
                estimated_tokens = max(500, total_chars // 4)
            
            self.total_tokens += estimated_tokens
            self.completion_tokens += estimated_tokens
            estimated_cost = estimated_tokens * self.completion_token_cost
            self.total_cost += estimated_cost
            
            logger.warning(
                f"⚠️  LLM call {self.llm_calls}: ~{estimated_tokens:,} tokens "
                f"(~${estimated_cost:.4f}) [ESTIMATED]"
            )
            
        except Exception as e:
            logger.error(f"Cost tracking error: {str(e)}")
            self.llm_calls += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            'total_tokens': self.total_tokens,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_cost_usd': round(self.total_cost, 4),
            'llm_calls': self.llm_calls,
            'estimated': self.prompt_tokens == 0
        }


# ============================================================================
# Configuration
# ============================================================================

# LLM - FIXED: removed invalid return_usage parameter
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_retries=3,
    request_timeout=120
)

# Tavily Search
tavily_client = None
search_available = False

try:
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        tavily_client = TavilyClient(api_key=tavily_api_key)
        search_available = True
        logger.info("✓ Tavily search available")
    else:
        logger.warning("⚠️  TAVILY_API_KEY not found")
except Exception as e:
    logger.warning(f"⚠️  Tavily init failed: {str(e)}")


# ============================================================================
# Search Tool
# ============================================================================

def search_renewable_energy_news(query: str) -> str:
    """Search for renewable energy news."""
    if not tavily_client:
        return "Search unavailable. Proceed with provided data."
    
    try:
        logger.info(f"🔍 Searching: '{query}'")
        
        response = tavily_client.search(
            query=query,
            max_results=3,
            search_depth="basic"
        )
        
        results = response.get('results', [])
        if not results:
            return "No results found. Proceed with provided data."
        
        formatted = "Search Results:\n\n"
        for i, item in enumerate(results, 1):
            formatted += f"{i}. {item.get('title', 'No title')}\n"
            formatted += f"   {item.get('content', '')[:250]}...\n"
            formatted += f"   Source: {item.get('url', '')}\n\n"
        
        logger.info(f"✓ Found {len(results)} results")
        return formatted
    
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return "Search failed. Proceed with provided data."


search_tool = Tool(
    name="search_renewable_energy_news",
    description="""Search for recent renewable energy news, policies, and market updates.

Use when you need CURRENT information about:
- Policy changes or announcements
- Market trends
- Regulatory updates
- Breaking news

Input: Search query string
Output: Recent articles with sources

Only search when current info would significantly improve analysis.""",
    func=search_renewable_energy_news
)


# ============================================================================
# ReAct Prompts
# ============================================================================

COUNTRY_ANALYZER_PROMPT = PromptTemplate.from_template("""You are a renewable energy investment analyst using ReAct reasoning.

TOOLS: {tools}
TOOL NAMES: {tool_names}

INVESTMENT:
Country: {country_code}
IRR: {avg_irr:.2f}%, LCOE: ${avg_lcoe:.2f}/MWh, NPV: ${avg_npv:.1f}M

Projects:
{projects_detail}

Think step-by-step:
Thought: [reasoning]
Action: [tool name OR provide answer]
Action Input: [if using tool]
Observation: [filled automatically]

WHEN TO SEARCH: Need recent policy/market info
DON'T SEARCH: For stable data already provided

PROVIDE (4-5 sentences):
1. Resource Quality
2. Financial Viability (IRR, LCOE, NPV)
3. Policy Context (if searched)
4. Risks/Opportunities
5. Recommendation: BUY/HOLD/AVOID

{agent_scratchpad}""")


RANKING_EXPLAINER_PROMPT = PromptTemplate.from_template("""Explain investment rankings to executives.

TOOLS: {tools}
TOOL NAMES: {tool_names}

RANKING:
{ranking_summary}

Think step-by-step:
Thought: [reasoning]
Action: [tool OR provide answer]
Action Input: [if using tool]

PROVIDE (4-5 sentences):
1. Why #1 is top? (cite metrics)
2. What distinguishes top performers?
3. Key decision factors?
4. Concerns/caveats?

{agent_scratchpad}""")


# ============================================================================
# Create Agents
# ============================================================================

def create_country_analyzer(callback: WorkingCostTracker) -> AgentExecutor:
    """Create country analyzer agent."""
    tools = [search_tool] if search_available else []
    
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=COUNTRY_ANALYZER_PROMPT
    )
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        max_execution_time=120,
        return_intermediate_steps=True,
        callbacks=[callback]
    )


def create_ranking_explainer(callback: WorkingCostTracker) -> AgentExecutor:
    """Create ranking explainer agent."""
    tools = [search_tool] if search_available else []
    
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=RANKING_EXPLAINER_PROMPT
    )
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=4,
        max_execution_time=60,
        return_intermediate_steps=True,
        callbacks=[callback]
    )


# ============================================================================
# Registered Agents
# ============================================================================

@register_agent(
    agent_id="insights_team_country_analyzer_v4_react",
    name="GPT-4 Country Analyzer (ReAct)",
    description="ReAct agent with working cost tracking and web search",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",  # FIXED: Added missing parameter
    version="4.3.0",
    tags=["gpt-4", "react", "web-search", "cost-tracking"]
)
def react_country_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze countries with ReAct reasoning and cost tracking."""
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
            
            projects_detail += f"\n**{loc.get('name')}** ({loc.get('technology')}):"\
                              f"\n- IRR: {analysis.get('irr', 0):.2f}%"\
                              f"\n- LCOE: ${analysis.get('lcoe', 0):.2f}/MWh"\
                              f"\n- NPV: ${analysis.get('npv', 0)/1e6:.1f}M"\
                              f"\n- CF: {analysis.get('capacity_factor', 0):.1%}\n"
            
            if loc.get('technology') == 'solar_pv':
                projects_detail += f"- Solar: {resource.get('ghi_kwh_m2_day', 0):.2f} kWh/m²/day\n"
            else:
                projects_detail += f"- Wind: {resource.get('wind_speed_100m_ms', 0):.2f} m/s\n"
        
        try:
            logger.info(f"🤖 Analyzing {country_code}...")
            
            # Create tracker
            cost_tracker = WorkingCostTracker()
            
            # Create and run agent
            agent = create_country_analyzer(cost_tracker)
            
            result = agent.invoke({
                "country_code": country_code,
                "avg_irr": metrics.get('average_irr', 0),
                "avg_lcoe": metrics.get('average_lcoe', 0),
                "avg_npv": metrics.get('average_npv', 0) / 1e6,
                "projects_detail": projects_detail
            })
            
            # Get costs
            cost_summary = cost_tracker.get_summary()
            
            # Extract results
            analysis_text = result.get('output', 'Analysis unavailable')
            intermediate_steps = result.get('intermediate_steps', [])
            
            # Count searches
            searches = sum(
                1 for step in intermediate_steps 
                if len(step) > 0 and hasattr(step[0], 'tool') 
                and step[0].tool == 'search_renewable_energy_news'
            )
            
            # Extract sources
            sources = []
            for step in intermediate_steps:
                if len(step) > 0 and hasattr(step[0], 'tool') and step[0].tool == 'search_renewable_energy_news':
                    import re
                    urls = re.findall(r'Source: (https?://[^\s]+)', str(step[1]))
                    sources.extend(urls)
            
            # Update totals
            total_tokens += cost_summary['total_tokens']
            total_cost += cost_summary['total_cost_usd']
            total_llm_calls += cost_summary['llm_calls']
            total_searches += searches
            
            logger.info(
                f"✓ {country_code} - Tokens: {cost_summary['total_tokens']:,}, "
                f"Cost: ${cost_summary['total_cost_usd']:.4f}, "
                f"LLM calls: {cost_summary['llm_calls']}, Searches: {searches}"
            )
            
            # Store insights
            country_insights[country_code] = {
                "analysis": analysis_text,
                "confidence": "high" if searches > 0 else "medium",
                "source": "GPT-4o ReAct Agent",
                "tokens_used": cost_summary['total_tokens'],
                "prompt_tokens": cost_summary['prompt_tokens'],
                "completion_tokens": cost_summary['completion_tokens'],
                "cost_usd": cost_summary['total_cost_usd'],
                "llm_calls": cost_summary['llm_calls'],
                "web_searches_performed": searches,
                "sources": sources[:5],
                "reasoning_steps": len(intermediate_steps),
                "cost_estimated": cost_summary.get('estimated', False)
            }
        
        except Exception as e:
            logger.error(f"Failed for {country_code}: {str(e)}")
            country_insights[country_code] = {
                "analysis": f"Analysis unavailable: {str(e)}",
                "confidence": "low",
                "error": str(e)
            }
    
    logger.info(
        f"Complete - Total Tokens: {total_tokens:,}, "
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
            "agent_type": "react",
            "cost_tracking": "working"
        }
    }


@register_agent(
    agent_id="insights_team_ranking_explainer_v3_react",
    name="GPT-4 Ranking Explainer (ReAct)",
    description="ReAct ranking explainer with cost tracking",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",  # FIXED: Added missing parameter
    version="3.3.0",
    tags=["gpt-4", "react", "cost-tracking"]
)
def react_ranking_explainer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Explain rankings with ReAct reasoning."""
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
    
    # Build summary
    ranking_summary = "Investment Ranking:\n\n"
    for country in ranked_countries[:5]:
        code = country['country_code']
        report = country_reports.get(code, {})
        metrics = report.get('aggregate_metrics', {})
        
        ranking_summary += f"{country['rank']}. {code} (Score: {country['overall_score']:.1f})\n"
        ranking_summary += f"   IRR: {metrics.get('average_irr', 0):.2f}%\n"
        ranking_summary += f"   LCOE: ${metrics.get('average_lcoe', 0):.2f}/MWh\n"
        ranking_summary += f"   NPV: ${metrics.get('average_npv', 0)/1e6:.1f}M\n\n"
    
    try:
        logger.info("🤖 Explaining rankings...")
        
        cost_tracker = WorkingCostTracker()
        agent = create_ranking_explainer(cost_tracker)
        
        result = agent.invoke({"ranking_summary": ranking_summary})
        
        cost_summary = cost_tracker.get_summary()
        
        logger.info(
            f"✓ Explanation - Tokens: {cost_summary['total_tokens']:,}, "
            f"Cost: ${cost_summary['total_cost_usd']:.4f}"
        )
        
        return {
            "ranking_explanation": {
                "explanation": result.get('output', 'Explanation unavailable'),
                "methodology": ranking.get("methodology", "Weighted scoring"),
                "confidence": "high",
                "source": "GPT-4o ReAct Agent",
                "tokens_used": cost_summary['total_tokens'],
                "prompt_tokens": cost_summary['prompt_tokens'],
                "completion_tokens": cost_summary['completion_tokens'],
                "cost_usd": cost_summary['total_cost_usd'],
                "llm_calls": cost_summary['llm_calls'],
                "cost_estimated": cost_summary.get('estimated', False)
            }
        }
    
    except Exception as e:
        logger.error(f"Explanation failed: {str(e)}")
        return {
            "ranking_explanation": {
                "explanation": "Explanation unavailable",
                "error": str(e),
                "confidence": "low"
            }
        }


# Initialize
os.makedirs("business_units/insights_team", exist_ok=True)
with open("business_units/insights_team/__init__.py", "w") as f:
    f.write("")

print("✅ ReAct Agents with Working Cost Tracking!")
print("   ✅ Fixed: removed invalid return_usage parameter")
print("   ✅ Fixed: added missing contact parameter")
print("   💰 Simplified cost tracking that works")
print(f"   🔍 Search: {'Available' if search_available else 'Disabled'}")
