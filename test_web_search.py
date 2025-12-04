"""Test web search enhancement."""

from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

import business_units.data_team.nasa_agent
import business_units.finance_team.financial_agents
import business_units.insights_team.gpt4_agents  # Now with search!
import business_units.ranking_team.agents


def test_web_search():
    """Test Country Analyzer with web search."""
    
    print("="*70)
    print("🔍 WEB SEARCH ENHANCEMENT TEST")
    print("="*70)
    
    registry = get_registry()
    print("\n📊 Registered Agents:")
    registry.print_summary()
    
    # Run workflow
    workflow = CountryComparisonWorkflow()
    
    result = workflow.run(
        countries=["USA", "IND"],
        query="Investment analysis with real-time web search"
    )
    
    # Generate insights with web search
    print("\n🔍 Generating insights with WEB SEARCH...")
    
    from business_units.insights_team.gpt4_agents import (
        langchain_country_analyzer_with_search,
        langchain_ranking_explainer
    )
    
    insights = langchain_country_analyzer_with_search(result)
    result.update(insights)
    
    explanation = langchain_ranking_explainer(result)
    result.update(explanation)
    
    # Show results
    print("\n" + "="*70)
    print("📊 RESULTS WITH WEB SEARCH")
    print("="*70)
    
    # Show metadata
    meta = result.get('insights_metadata', {})
    print(f"\n💰 Enhanced Analysis Metadata:")
    print(f"   Tokens: {meta.get('total_tokens', 0)}")
    print(f"   Cost: ${meta.get('total_cost_usd', 0):.4f}")
    print(f"   Web Searches: {meta.get('total_web_searches', 0)}")
    print(f"   Search Tool: {meta.get('search_tool', 'none')}")
    
    # Show insights with sources
    print(f"\n🤖 Enhanced Country Insights:")
    country_insights = result.get('country_insights', {})
    
    for code, insight in country_insights.items():
        print(f"\n{'='*70}")
        print(f"🌍 {code}")
        print(f"{'='*70}")
        
        # Show if web search was used
        search_used = insight.get('web_search_performed', False)
        sources = insight.get('sources', [])
        
        print(f"\n🔍 Web Search: {'YES' if search_used else 'NO'}")
        if sources:
            print(f"📚 Sources ({len(sources)}):")
            for i, source in enumerate(sources[:3], 1):
                print(f"   {i}. {source}")
        
        # Show analysis
        print(f"\n📝 Analysis:")
        analysis = insight.get('analysis', 'N/A')
        print(f"{analysis}")
        
        print(f"\n💰 Cost: ${insight.get('cost_usd', 0):.4f}")
        print(f"🎯 Confidence: {insight.get('confidence', 'unknown')}")
    
    print("\n" + "="*70)
    print("✅ WEB SEARCH TEST COMPLETE!")
    print("="*70)
    
    print("\n📋 New Capabilities:")
    print("   ✅ Real-time web search for policy updates")
    print("   ✅ Source citation and transparency")
    print("   ✅ Enhanced context awareness")
    print("   ✅ Graceful fallback if search fails")
    
    return result


if __name__ == "__main__":
    test_web_search()
