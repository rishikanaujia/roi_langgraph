"""
Test Country Comparison Workflow with Research Data
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

# Correct import path
from src.workflows.country_comparison_with_research import workflow_with_research


def main():
    """Test workflow with research data."""
    
    print("=" * 70)
    print("🧪 WORKFLOW WITH RESEARCH TEST")
    print("=" * 70)
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
    print(f"\n📚 Research Loaded:")
    print(f"   Countries: {research_metadata.get('total_countries', 0)}")
    print(f"   Characters: {research_metadata.get('total_characters', 0):,}")
    
    # Insights generated
    insights = result.get("country_insights", {})
    print(f"\n🧠 Insights Generated:")
    print(f"   Countries analyzed: {len(insights)}")
    
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
    for country in ranked_countries:
        print(f"   {country['rank']}. {country['country_code']} "
              f"(Score: {country['overall_score']:.1f})")
    
    print("\n" + "=" * 70)
    print("✅ WORKFLOW WITH RESEARCH TEST COMPLETE!")
    print("=" * 70)
    print()
    print("💡 Key Benefits:")
    print("   • Research data automatically loaded")
    print("   • Insights agents receive research context")
    print("   • Richer, more informed analysis")
    print("   • No code changes needed in insights agents")
    print()


if __name__ == "__main__":
    main()
