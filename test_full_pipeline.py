"""Test complete pipeline with NASA data + financial calculations."""

from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

# Import all agents
import business_units.data_team.nasa_agent
import business_units.finance_team.financial_agents
import business_units.ranking_team.agents


def test_full_pipeline():
    """Test with real NASA data AND real financial calculations."""
    
    print("="*70)
    print("💰 FULL PIPELINE TEST: NASA DATA + FINANCIAL MODELS")
    print("="*70)
    
    registry = get_registry()
    print("\n📊 Registered Agents:")
    registry.print_summary()
    
    workflow = CountryComparisonWorkflow()
    
    print("\n🚀 Running full pipeline...")
    print("   1. Fetch real NASA data")
    print("   2. Calculate real financial metrics")
    print("   3. Rank countries")
    print("⏳ This takes ~30-60 seconds...\n")
    
    result = workflow.run(
        countries=["USA", "IND", "BRA"],  # 3 diverse countries
        query="Best renewable energy investment"
    )
    
    print("\n" + "="*70)
    print("📊 INVESTMENT ANALYSIS RESULTS")
    print("="*70)
    
    for code, report in result['country_reports'].items():
        metrics = report.get('aggregate_metrics', {})
        
        print(f"\n🌍 {code}:")
        print(f"   📈 Average IRR:  {metrics.get('average_irr', 0):.2f}%")
        print(f"   💵 Average LCOE: ${metrics.get('average_lcoe', 0):.2f}/MWh")
        print(f"   💰 Average NPV:  ${metrics.get('average_npv', 0)/1e6:.1f}M")
        
        print(f"\n   Projects:")
        for analysis in report.get('location_analyses', []):
            loc = analysis['location']
            print(f"      {loc['name']} ({loc['technology']})")
            print(f"        IRR: {analysis['irr']:.2f}%, LCOE: ${analysis['lcoe']:.0f}/MWh")
    
    print("\n" + "="*70)
    print("🏆 RANKING")
    print("="*70)
    
    ranking = result.get('ranking', {})
    for country in ranking.get('ranked_countries', []):
        print(f"   {country['rank']}. {country['country_code']} "
              f"(Score: {country['overall_score']:.1f})")
        print(f"      {country['justification']}")
    
    print("\n" + "="*70)
    print("✅ FULL PIPELINE TEST COMPLETE!")
    print("="*70)
    print("\n💡 Now you have REAL investment analysis!")


if __name__ == "__main__":
    test_full_pipeline()
