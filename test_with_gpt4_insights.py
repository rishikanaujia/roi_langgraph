"""Test complete pipeline with GPT-4 insights."""

from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

# Import all agents
import business_units.data_team.nasa_agent
import business_units.finance_team.financial_agents
import business_units.insights_team.gpt4_agents
import business_units.ranking_team.agents


def test_with_insights():
    """Test with NASA + Financial + GPT-4 Insights."""
    
    print("="*70)
    print("🤖 COMPLETE SYSTEM: NASA + Finance + GPT-4 Insights")
    print("="*70)
    
    workflow = CountryComparisonWorkflow()
    
    print("\n🚀 Running complete pipeline...")
    print("   1. Fetch real NASA data")
    print("   2. Calculate financial metrics")
    print("   3. Rank countries")
    print("   4. Generate GPT-4 insights")
    print("⏳ This takes ~60-90 seconds...\n")
    
    result = workflow.run(
        countries=["USA", "IND", "BRA"],
        query="Best renewable energy investment with detailed insights"
    )
    
    # Run GPT-4 analysis on results
    from business_units.insights_team.gpt4_agents import (
        gpt4_country_analyzer,
        gpt4_ranking_explainer
    )
    
    print("\n🤖 Generating AI insights...")
    insights_result = gpt4_country_analyzer(result)
    result.update(insights_result)
    
    explanation_result = gpt4_ranking_explainer(result)
    result.update(explanation_result)
    
    print("\n" + "="*70)
    print("📊 INVESTMENT ANALYSIS WITH AI INSIGHTS")
    print("="*70)
    
    # Show rankings first
    print("\n🏆 RANKINGS:")
    ranking = result.get('ranking', {})
    for country in ranking.get('ranked_countries', []):
        print(f"   {country['rank']}. {country['country_code']} (Score: {country['overall_score']:.1f})")
    
    # Show AI explanation
    print("\n🤖 AI EXPLANATION:")
    explanation = result.get('ranking_explanation', {})
    print(f"\n{explanation.get('explanation', 'N/A')}\n")
    
    # Show country insights
    print("\n" + "="*70)
    print("🌍 DETAILED COUNTRY INSIGHTS")
    print("="*70)
    
    country_insights = result.get('country_insights', {})
    
    for code, report in result['country_reports'].items():
        metrics = report.get('aggregate_metrics', {})
        insight = country_insights.get(code, {})
        
        print(f"\n🌍 {code}:")
        print(f"   📈 IRR:  {metrics.get('average_irr', 0):.2f}%")
        print(f"   💵 LCOE: ${metrics.get('average_lcoe', 0):.2f}/MWh")
        print(f"   💰 NPV:  ${metrics.get('average_npv', 0)/1e6:.1f}M")
        
        print(f"\n   🤖 AI Analysis:")
        analysis = insight.get('analysis', 'N/A')
        for line in analysis.split('\n'):
            if line.strip():
                print(f"      {line.strip()}")
    
    print("\n" + "="*70)
    print("✅ COMPLETE AI-POWERED ANALYSIS READY!")
    print("="*70)
    
    # Save results
    import json
    with open('complete_analysis_with_ai.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print("\n📄 Full results saved to: complete_analysis_with_ai.json")


if __name__ == "__main__":
    test_with_insights()
