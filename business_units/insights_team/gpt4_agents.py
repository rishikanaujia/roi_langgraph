"""
Insights Team - LangChain Powered Agents

Upgraded from Custom + OpenAI SDK to full LangChain.
"""

import os
import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.callbacks import get_openai_callback  # FIXED ✨

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("GPT4Agents")


# ============================================================================
# LangChain LLM Configuration
# ============================================================================

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_retries=3,
    request_timeout=60
)


# ============================================================================
# Country Analyzer - LangChain Version
# ============================================================================

country_analysis_template = ChatPromptTemplate.from_messages([
    ("system", """You are a renewable energy investment analyst with expertise in:
- Solar and wind resource assessment
- Project financial modeling (IRR, LCOE, NPV)
- Investment risk analysis
- Renewable energy policy

Provide concise, data-driven analysis suitable for executive decision-making."""),
    
    ("user", """Analyze this renewable energy investment opportunity:

**Country:** {country_code}

**Aggregate Financial Metrics:**
- Average IRR: {avg_irr:.2f}%
- Average LCOE: ${avg_lcoe:.2f}/MWh
- Average NPV: ${avg_npv:.1f}M

**Individual Projects:**
{projects_detail}

**Required Analysis (3-4 sentences):**
1. **Resource Quality Assessment:** Evaluate solar/wind resource strength
2. **Financial Viability:** Assess IRR, LCOE, NPV - be specific about what they mean
3. **Key Risks or Opportunities:** Identify critical factors
4. **Investment Recommendation:** Provide clear BUY/HOLD/AVOID recommendation with justification

Be specific, data-driven, and actionable.""")
])

country_analysis_chain = country_analysis_template | llm | StrOutputParser()


@register_agent(
    agent_id="insights_team_country_analyzer_v2_langchain",
    name="GPT-4 Country Analyzer (LangChain)",
    description="LangChain-powered country analysis with prompt templates and cost tracking",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",
    version="2.0.0"
)
def langchain_country_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze each country using LangChain."""
    country_reports = state.get("country_reports", {})
    country_insights = {}
    
    total_tokens = 0
    total_cost = 0.0
    
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
        
        try:
            logger.info(f"Generating LangChain insights for {country_code}...")
            
            with get_openai_callback() as cb:
                analysis_text = country_analysis_chain.invoke({
                    "country_code": country_code,
                    "avg_irr": metrics.get('average_irr', 0),
                    "avg_lcoe": metrics.get('average_lcoe', 0),
                    "avg_npv": metrics.get('average_npv', 0) / 1e6,
                    "projects_detail": projects_detail
                })
                
                total_tokens += cb.total_tokens
                total_cost += cb.total_cost
                
                logger.info(
                    f"✓ Generated insights for {country_code} "
                    f"(tokens: {cb.total_tokens}, cost: ${cb.total_cost:.4f})"
                )
                
                country_insights[country_code] = {
                    "analysis": analysis_text,
                    "confidence": "high",
                    "source": "GPT-4o via LangChain",
                    "tokens_used": cb.total_tokens,
                    "cost_usd": round(cb.total_cost, 4)
                }
        
        except Exception as e:
            logger.error(f"Failed to generate insights for {country_code}: {str(e)}")
            country_insights[country_code] = {
                "analysis": f"Analysis unavailable: {str(e)}",
                "confidence": "low",
                "error": str(e)
            }
    
    logger.info(f"Total GPT-4 usage - Tokens: {total_tokens}, Cost: ${total_cost:.4f}")
    
    return {
        "country_insights": country_insights,
        "insights_metadata": {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "model": "gpt-4o",
            "framework": "langchain"
        }
    }


# ============================================================================
# Ranking Explainer - LangChain Version
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
        logger.info("Generating LangChain ranking explanation...")
        
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

print("✅ LangChain GPT-4 Agents registered!")
print("   - Country Analyzer (v2.0 - LangChain)")
print("   - Ranking Explainer (v2.0 - LangChain)")
print("   📊 Features: Prompt templates, cost tracking, auto-retry")
