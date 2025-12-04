"""
Test Country Comparison Workflow with Research Data
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

# Import agents with correct file names
import business_units.data_team.nasa_agent
import business_units.data_team.research_loader
import business_units.finance_team.financial_agents
import business_units.insights_team.gpt4_agents
import business_units.ranking_team.agents

from src.workflows.country_comparison_with_research import workflow_with_research
from src.registry.agent_registry import get_registry


def main():
    """Test workflow with research data."""
    
    print("=" * 70)
    print("🧪 WORKFLOW WITH RESEARCH TEST")
    print("=" * 70)
    print()
    
    # Verify agents are registered
    registry = get_registry()
    all_agents = registry.list_agents(enabled_only=False)
    
    print("📋 Registered Agents:")
    print(f"   Total: {len(all_agents)}")
    for agent in sorted(all_agents, key=lambda a: a.agent_id):
        print(f"   • {agent.agent_id}")
    print()
    
    # Sample research data
    research_data = [
        {
            "country_name": "United States",
            "research": """The US renewable energy sector benefits from the 
            Inflation Reduction Act providing 30% ITC for solar and PTC for wind. 
            Strong state-level support in California, Texas, and Iowa. Grid 
            interconnection improving with FERC Order 2023."""
        },
        {
            "country_name": "India",
            "research": """India targets 500 GW renewable capacity by 2030. 
            PLI scheme offers manufacturing subsidies. Gujarat and Rajasthan lead 
            solar development. Green Energy Open Access Rules facilitate corporate 
            procurement. Land acquisition and grid evacuation challenges persist."""
        }
    ]
    
    print("🚀 Running workflow with research data...")
    print(f"   Countries: USA, IND")
    print(f"   Research: {len(research_data)} countries")
    print()
    
    # Run workflow
    result = workflow_with_research.run(
        countries=["USA", "IND"],
        research_json_data=research_data
    )
    
    print("\n" + "=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    
    # Research loaded
    research_metadata = result.get("research_metadata", {})
    country_research = result.get("country_research", {})
    print(f"\n📚 Research Loaded:")
    print(f"   Countries: {len(country_research)}")
    print(f"   Total chars: {research_metadata.get('total_characters', 0):,}")
    
    if country_research:
        print(f"\n   Research by country:")
        for code, text in country_research.items():
            print(f"      {code}: {len(text):,} characters")
    
    # Locations loaded
    locations = result.get("locations", [])
    print(f"\n🗺️  Locations Loaded:")
    print(f"   Total locations: {len(locations)}")
    if locations:
        for loc in locations[:4]:
            print(f"      {loc.get('name')} ({loc.get('technology')})")
    
    # Financial analysis
    location_analyses = result.get("location_analyses", [])
    print(f"\n💰 Financial Analysis:")
    print(f"   Locations analyzed: {len(location_analyses)}")
    
    # Country reports
    country_reports = result.get("country_reports", {})
    print(f"\n📊 Country Reports:")
    print(f"   Countries: {len(country_reports)}")
    
    if country_reports:
        for code, report in country_reports.items():
            metrics = report.get("aggregate_metrics", {})
            print(f"\n   {code}:")
            print(f"      IRR: {metrics.get('average_irr', 0):.2f}%")
            print(f"      LCOE: ${metrics.get('average_lcoe', 0):.2f}/MWh")
            print(f"      NPV: ${metrics.get('average_npv', 0)/1e6:.1f}M")
    
    # Insights generated
    insights = result.get("country_insights", {})
    insights_metadata = result.get("insights_metadata", {})
    
    print(f"\n🧠 Insights Generated:")
    print(f"   Countries analyzed: {len(insights)}")
    print(f"   Web searches: {insights_metadata.get('total_web_searches', 0)}")
    
    if insights:
        for country_code, insight in insights.items():
            print(f"\n   {country_code}:")
            print(f"      Confidence: {insight.get('confidence', 'unknown')}")
            print(f"      Searches: {insight.get('web_searches_performed', 0)}")
            print(f"      Sources: {len(insight.get('sources', []))}")
            
            analysis = insight.get('analysis', '')
            if analysis and analysis != "Agent stopped due to iteration limit or time limit.":
                preview = analysis[:200].replace('\n', ' ')
                print(f"      Preview: {preview}...")
    
    # Ranking
    ranking = result.get("ranking", {})
    ranked_countries = ranking.get("ranked_countries", [])
    
    print(f"\n🏆 Ranking:")
    if ranked_countries:
        for country in ranked_countries:
            print(f"   {country['rank']}. {country['country_code']} "
                  f"(Score: {country['overall_score']:.1f})")
    else:
        print("   No ranking generated")
    
    # Ranking explanation
    ranking_explanation = result.get("ranking_explanation", {})
    if ranking_explanation:
        print(f"\n📝 Ranking Explanation:")
        explanation = ranking_explanation.get('explanation', '')
        if explanation and explanation != "Agent stopped due to iteration limit or time limit.":
            preview = explanation[:300].replace('\n', ' ')
            print(f"   {preview}...")
    
    print("\n" + "=" * 70)
    print("✅ WORKFLOW WITH RESEARCH TEST COMPLETE!")
    print("=" * 70)
    print()
    
    # Summary
    print("📊 Summary:")
    print(f"   ✅ Research data: {len(country_research)} countries")
    print(f"   ✅ Locations: {len(locations)}")
    print(f"   ✅ Financial analyses: {len(location_analyses)}")
    print(f"   ✅ Country reports: {len(country_reports)}")
    print(f"   ✅ Insights: {len(insights)} countries")
    print(f"   ✅ Web searches: {insights_metadata.get('total_web_searches', 0)}")
    print(f"   ✅ Ranking: {'Generated' if ranked_countries else 'Not generated'}")
    print()


if __name__ == "__main__":
    main()
