"""
Insights Team - GPT-4 Powered Agents - FIXED

Provides AI-generated insights, explanations, and recommendations.
"""

import os
import logging
from typing import Dict, Any
from openai import OpenAI
from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("GPT4Agents")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@register_agent(
    agent_id="insights_team_country_analyzer_v1",
    name="GPT-4 Country Analyzer",
    description="Provides AI-powered insights on country investment potential",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.REPORT_GEN],  # Changed from ANALYSIS
    business_unit="insights_team",
    contact="insights@company.com",
    required_inputs=["country_reports"],
    output_keys=["country_insights"]
)
def gpt4_country_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI-powered insights for each country."""
    country_reports = state.get("country_reports", {})
    
    country_insights = {}
    
    for country_code, report in country_reports.items():
        metrics = report.get("aggregate_metrics", {})
        analyses = report.get("location_analyses", [])
        
        # Build context for GPT-4
        context = f"""
Analyze this renewable energy investment opportunity:

Country: {country_code}

Overall Metrics:
- Average IRR: {metrics.get('average_irr', 0):.2f}%
- Average LCOE: ${metrics.get('average_lcoe', 0):.2f}/MWh
- Average NPV: ${metrics.get('average_npv', 0)/1e6:.1f}M

Projects:
"""
        
        for analysis in analyses:
            loc = analysis.get('location', {})
            resource = loc.get('resource_data', {})
            
            context += f"""
- {loc.get('name')} ({loc.get('technology')}):
  * IRR: {analysis.get('irr', 0):.2f}%
  * LCOE: ${analysis.get('lcoe', 0):.2f}/MWh
  * NPV: ${analysis.get('npv', 0)/1e6:.1f}M
  * Capacity Factor: {analysis.get('capacity_factor', 0):.1%}
"""
            
            if loc.get('technology') == 'solar_pv':
                context += f"  * Solar Resource: {resource.get('ghi_kwh_m2_day', 0):.2f} kWh/m²/day\n"
            else:
                context += f"  * Wind Speed: {resource.get('wind_speed_100m_ms', 0):.2f} m/s\n"
        
        # Call GPT-4
        try:
            logger.info(f"Generating insights for {country_code}...")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a renewable energy investment analyst. Provide concise, actionable insights."
                    },
                    {
                        "role": "user",
                        "content": f"""{context}

Provide a brief analysis (3-4 sentences) covering:
1. Resource quality assessment
2. Financial viability (be specific about IRR/LCOE/NPV)
3. Key risks or opportunities
4. Investment recommendation (BUY/HOLD/AVOID)

Be specific and data-driven."""
                    }
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            insight = response.choices[0].message.content
            
            logger.info(f"✓ Generated insights for {country_code}")
            
            country_insights[country_code] = {
                "analysis": insight,
                "confidence": "high",
                "source": "GPT-4o"
            }
        
        except Exception as e:
            logger.error(f"Failed to generate insights for {country_code}: {str(e)}")
            country_insights[country_code] = {
                "analysis": "Analysis unavailable",
                "confidence": "low",
                "error": str(e)
            }
    
    return {"country_insights": country_insights}


@register_agent(
    agent_id="insights_team_ranking_explainer_v1",
    name="GPT-4 Ranking Explainer",
    description="Explains why countries are ranked in a specific order",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.REPORT_GEN],  # Changed from ANALYSIS
    business_unit="insights_team",
    contact="insights@company.com",
    required_inputs=["country_reports", "ranking"],
    output_keys=["ranking_explanation"]
)
def gpt4_ranking_explainer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Explain the ranking using GPT-4."""
    ranking = state.get("ranking", {})
    country_reports = state.get("country_reports", {})
    
    ranked_countries = ranking.get("ranked_countries", [])
    
    if not ranked_countries:
        return {"ranking_explanation": "No ranking available"}
    
    # Build context
    context = "Investment Ranking:\n\n"
    
    for country in ranked_countries[:5]:
        code = country['country_code']
        report = country_reports.get(code, {})
        metrics = report.get('aggregate_metrics', {})
        
        context += f"""
{country['rank']}. {code} (Score: {country['overall_score']:.1f})
   - IRR: {metrics.get('average_irr', 0):.2f}%
   - LCOE: ${metrics.get('average_lcoe', 0):.2f}/MWh
   - NPV: ${metrics.get('average_npv', 0)/1e6:.1f}M
"""
    
    # Call GPT-4
    try:
        logger.info("Generating ranking explanation...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are explaining investment rankings to executives. Be clear, specific, and actionable."
                },
                {
                    "role": "user",
                    "content": f"""{context}

Explain this ranking in 4-5 sentences:
1. Why is #1 the best choice? (cite specific metrics)
2. What distinguishes the top performers?
3. What are the key decision factors?
4. Any concerns or caveats?

Write for executives who need clear recommendations."""
                }
            ],
            temperature=0.3,
            max_tokens=400
        )
        
        explanation = response.choices[0].message.content
        
        logger.info("✓ Generated ranking explanation")
        
        return {
            "ranking_explanation": {
                "explanation": explanation,
                "methodology": ranking.get("methodology", "Weighted scoring"),
                "confidence": "high",
                "source": "GPT-4o"
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to generate ranking explanation: {str(e)}")
        return {
            "ranking_explanation": {
                "explanation": "Explanation unavailable",
                "error": str(e)
            }
        }


# Create __init__.py
import os
os.makedirs("business_units/insights_team", exist_ok=True)
with open("business_units/insights_team/__init__.py", "w") as f:
    f.write("")

print("✅ GPT-4 Insight Agents registered!")
