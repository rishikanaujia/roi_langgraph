"""
Executive Report Generator

Generates comprehensive investment reports with rankings, insights, and references.

Version: 1.0.1 (Fixed dict access issues)
Author: ROI Analysis Team
"""

from typing import Dict, Any, List
from datetime import datetime
from src.registry.agent_registry import get_registry
from src.registry.agent_metadata import (
    AgentMetadata,
    AgentFramework,
    AgentCapability
)


def generate_executive_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive executive report.
    
    Input State Keys:
    - countries: List[str] - Country codes
    - country_reports: Dict - Financial metrics per country
    - ranking: Dict - Ranking results
    - country_insights: Dict - AI analysis per country
    - country_research: Dict - Research context per country
    - insights_metadata: Dict - Sources and metadata
    
    Output State Keys:
    - executive_report: Dict with report sections
    - report_markdown: str - Formatted markdown report
    - report_metadata: Dict with generation info
    """
    
    # Extract data from state
    countries = state.get("countries", [])
    country_reports = state.get("country_reports", {})
    ranking = state.get("ranking", {})
    country_insights = state.get("country_insights", {})
    country_research = state.get("country_research", {})
    insights_metadata = state.get("insights_metadata", {})
    
    ranked_countries = ranking.get("ranked_countries", [])
    
    # Generate report sections
    report = {
        "title": "Renewable Energy Investment Analysis Report",
        "generated_at": datetime.now().isoformat(),
        "countries_analyzed": len(countries),
        "executive_summary": _generate_executive_summary(ranked_countries, country_insights),
        "rankings": _generate_rankings_section(ranked_countries, country_reports),
        "country_analyses": _generate_country_analyses(ranked_countries, country_reports, country_insights, country_research),
        "methodology": _generate_methodology_section(insights_metadata),
        "references": _generate_references_section(country_insights, insights_metadata)
    }
    
    # Generate markdown version
    markdown_report = _format_as_markdown(report)
    
    # Save to file (optional)
    filename = f"investment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w") as f:
        f.write(markdown_report)
    
    return {
        "executive_report": report,
        "report_markdown": markdown_report,
        "report_metadata": {
            "filename": filename,
            "generated_at": report["generated_at"],
            "countries_analyzed": len(countries),
            "total_sources": _count_total_sources(country_insights),
            "web_searches_performed": insights_metadata.get("total_web_searches", 0)
        }
    }


def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get value from dict or return default."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _generate_executive_summary(ranked_countries: List[Dict], country_insights: Dict) -> str:
    """Generate executive summary."""
    if not ranked_countries:
        return "No countries analyzed."
    
    top_country = ranked_countries[0]
    top_code = top_country.get("country_code")
    top_score = top_country.get("overall_score", 0)
    
    summary = f"""
Based on comprehensive analysis of {len(ranked_countries)} countries, **{top_code}** emerges as the 
top investment destination with an overall score of {top_score:.1f}. This ranking is based on 
financial metrics (IRR, LCOE, NPV), resource quality, and policy environment analysis.

Key findings:
- Top performer: {top_code} (Score: {top_score:.1f})
"""
    
    if len(ranked_countries) > 1:
        second = ranked_countries[1]
        summary += f"- Runner-up: {second.get('country_code')} (Score: {second.get('overall_score', 0):.1f})\n"
    
    # Add insights from top country
    if top_code in country_insights:
        insight = country_insights[top_code]
        confidence = _safe_get(insight, "confidence", "unknown")
        summary += f"- Analysis confidence: {confidence.upper()}\n"
    
    return summary.strip()


def _generate_rankings_section(ranked_countries: List[Dict], country_reports: Dict) -> List[Dict]:
    """Generate detailed rankings section."""
    rankings = []
    
    for country in ranked_countries:
        code = country.get("country_code")
        rank = country.get("rank")
        score = country.get("overall_score", 0)
        
        # Get financial metrics
        report = country_reports.get(code, {})
        metrics = report.get("aggregate_metrics", {})
        
        rankings.append({
            "rank": rank,
            "country_code": code,
            "country_name": country.get("country_name", code),
            "overall_score": score,
            "metrics": {
                "irr": metrics.get("average_irr", 0),
                "lcoe": metrics.get("average_lcoe", 0),
                "npv": metrics.get("average_npv", 0)
            }
        })
    
    return rankings


def _generate_country_analyses(
    ranked_countries: List[Dict],
    country_reports: Dict,
    country_insights: Dict,
    country_research: Dict
) -> List[Dict]:
    """Generate detailed analysis for each country."""
    analyses = []
    
    for country in ranked_countries:
        code = country.get("country_code")
        
        # Get data
        report = country_reports.get(code, {})
        insight = country_insights.get(code, {})
        research = country_research.get(code, "")
        
        metrics = report.get("aggregate_metrics", {})
        locations = report.get("location_analyses", [])
        
        # Handle both dict and string formats for insight
        if isinstance(insight, str):
            # Insight is just a string
            ai_analysis = insight
            recommendation = "N/A"
            confidence = "unknown"
            sources = []
            web_searches = 0
        else:
            # Insight is a dict
            ai_analysis = _safe_get(insight, "analysis", "No analysis available")
            recommendation = _safe_get(insight, "recommendation", "N/A")
            confidence = _safe_get(insight, "confidence", "unknown")
            sources = _safe_get(insight, "sources", [])
            web_searches = _safe_get(insight, "web_searches_performed", 0)
        
        analysis = {
            "rank": country.get("rank"),
            "country_code": code,
            "country_name": country.get("country_name", code),
            "financial_metrics": {
                "irr": metrics.get("average_irr", 0),
                "lcoe": metrics.get("average_lcoe", 0),
                "npv": metrics.get("average_npv", 0)
            },
            "locations_analyzed": len(locations),
            "ai_analysis": ai_analysis,
            "recommendation": recommendation,
            "confidence": confidence,
            "policy_context": research[:300] + "..." if len(research) > 300 else research,
            "sources": sources if isinstance(sources, list) else [],
            "web_searches": web_searches
        }
        
        analyses.append(analysis)
    
    return analyses


def _generate_methodology_section(insights_metadata: Dict) -> Dict:
    """Generate methodology section."""
    return {
        "data_sources": [
            "NASA POWER API (climate data)",
            "Pre-researched policy analysis",
            "Real-time web search (when needed)",
            "Financial modeling (IRR, LCOE, NPV)"
        ],
        "analysis_approach": [
            "1. Load representative locations (solar + wind)",
            "2. Calculate financial metrics per location",
            "3. Aggregate by country",
            "4. AI-powered analysis with ReAct reasoning",
            "5. Web search for current policy updates",
            "6. Generate investment recommendations"
        ],
        "ai_models": "GPT-4 with ReAct pattern",
        "web_searches_performed": insights_metadata.get("total_web_searches", 0)
    }


def _generate_references_section(country_insights: Dict, insights_metadata: Dict) -> List[Dict]:
    """Generate references section."""
    references = []
    ref_id = 1
    
    for country_code, insight in country_insights.items():
        # Handle both dict and other formats
        sources = _safe_get(insight, "sources", [])
        if not isinstance(sources, list):
            sources = []
            
        for source in sources:
            if isinstance(source, dict):
                references.append({
                    "id": ref_id,
                    "country": country_code,
                    "title": source.get("title", "Unknown"),
                    "url": source.get("url", ""),
                    "accessed": datetime.now().strftime("%Y-%m-%d")
                })
                ref_id += 1
    
    return references


def _count_total_sources(country_insights: Dict) -> int:
    """Count total sources across all countries."""
    total = 0
    for insight in country_insights.values():
        sources = _safe_get(insight, "sources", [])
        if isinstance(sources, list):
            total += len(sources)
    return total


def _format_as_markdown(report: Dict) -> str:
    """Format report as markdown."""
    
    md = f"""# {report['title']}

**Generated:** {report['generated_at']}  
**Countries Analyzed:** {report['countries_analyzed']}

---

## Executive Summary

{report['executive_summary']}

---

## Investment Rankings

"""
    
    # Rankings table
    rankings = report['rankings']
    if rankings:
        md += "| Rank | Country | Score | IRR | LCOE | NPV |\n"
        md += "|------|---------|-------|-----|------|-----|\n"
        
        for r in rankings:
            md += f"| **{r['rank']}** | **{r['country_code']}** | {r['overall_score']:.1f} | "
            md += f"{r['metrics']['irr']:.2f}% | ${r['metrics']['lcoe']:.2f}/MWh | "
            md += f"${r['metrics']['npv']/1e6:.1f}M |\n"
        
        md += "\n"
    
    # Country analyses
    md += "---\n\n## Detailed Country Analyses\n\n"
    
    for analysis in report['country_analyses']:
        rank_emoji = "🥇" if analysis['rank'] == 1 else "🥈" if analysis['rank'] == 2 else "🥉" if analysis['rank'] == 3 else "📊"
        
        md += f"### {rank_emoji} #{analysis['rank']} - {analysis['country_code']}\n\n"
        
        # Financial metrics
        md += "**Financial Performance:**\n"
        md += f"- IRR: {analysis['financial_metrics']['irr']:.2f}%\n"
        md += f"- LCOE: ${analysis['financial_metrics']['lcoe']:.2f}/MWh\n"
        md += f"- NPV: ${analysis['financial_metrics']['npv']/1e6:.1f}M\n"
        md += f"- Locations Analyzed: {analysis['locations_analyzed']}\n\n"
        
        # AI Analysis
        md += "**AI Analysis:**\n\n"
        ai_text = analysis['ai_analysis']
        if ai_text and ai_text != "Agent stopped due to iteration limit or time limit.":
            # Truncate if too long
            if len(ai_text) > 1000:
                ai_text = ai_text[:1000] + "...\n\n*(Analysis truncated for brevity)*"
            md += f"{ai_text}\n\n"
        else:
            md += "*Analysis unavailable*\n\n"
        
        # Recommendation
        md += f"**Investment Recommendation:** {analysis['recommendation'].upper()}  \n"
        md += f"**Confidence Level:** {analysis['confidence'].upper()}\n\n"
        
        # Policy context
        if analysis['policy_context']:
            md += "**Policy Context:**\n\n"
            md += f"> {analysis['policy_context']}\n\n"
        
        # Sources
        if analysis['sources']:
            md += f"**Sources Referenced:** {len(analysis['sources'])} source(s)\n\n"
        
        md += "---\n\n"
    
    # Methodology
    md += "## Methodology\n\n"
    methodology = report['methodology']
    
    md += "**Data Sources:**\n"
    for source in methodology['data_sources']:
        md += f"- {source}\n"
    md += "\n"
    
    md += "**Analysis Process:**\n"
    for step in methodology['analysis_approach']:
        md += f"- {step}\n"
    md += "\n"
    
    md += f"**AI Models:** {methodology['ai_models']}  \n"
    md += f"**Web Searches Performed:** {methodology['web_searches_performed']}\n\n"
    
    # References
    references = report['references']
    if references:
        md += "---\n\n## References\n\n"
        for ref in references:
            md += f"{ref['id']}. **{ref['title']}** ({ref['country']})  \n"
            if ref['url']:
                md += f"   {ref['url']}  \n"
            md += f"   Accessed: {ref['accessed']}\n\n"
    
    # Footer
    md += "---\n\n"
    md += "*This report was generated by the ROI LangGraph Multi-Agent System*  \n"
    md += f"*Generated at: {report['generated_at']}*\n"
    
    return md


# ============================================================================
# Agent Registration
# ============================================================================

# Register the agent
registry = get_registry()

metadata = AgentMetadata(
    agent_id="insights_team_report_generator_v1",
    name="Executive Report Generator",
    description="Generates comprehensive investment reports with rankings, insights, and references",
    version="1.0.1",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    required_inputs=["countries", "country_reports", "ranking"],
    output_keys=["executive_report", "report_markdown", "report_metadata"],
    tags=["report", "executive", "markdown", "documentation"],
    contact="insights@company.com",
    enabled=True
)

registry.register_agent(metadata, generate_executive_report)

print("✅ Executive Report Generator registered (v1.0.1 - Fixed)!")
print("   📊 Generates comprehensive investment reports")
print("   📝 Includes rankings, insights, and references")
print("   💾 Saves as markdown file")
print("   🔧 Robust error handling for different data formats")
