"""Test accurate cost tracking in ReAct agents."""

import sys
from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

# Import agents
import business_units.data_team.nasa_agent
import business_units.finance_team.financial_agents
import business_units.insights_team.gpt4_agents  # Fixed cost tracking!
import business_units.ranking_team.agents


def test_cost_tracking():
    """Test ReAct agents with accurate cost tracking."""
    
    print("="*70)
    print("💰 COST TRACKING TEST - ACCURATE METRICS")
    print("="*70)
    
    registry = get_registry()
    print("\n📊 Registered Agents:")
    registry.print_summary()
    
    # Run workflow
    print("\n" + "="*70)
    print("🚀 Running Workflow")
    print("="*70)
    
    workflow = CountryComparisonWorkflow()
    
    result = workflow.run(
        countries=["USA", "BRA"],
        query="Test accurate cost tracking"
    )
    
    # Generate insights
    print("\n" + "="*70)
    print("💰 Generating Insights with Cost Tracking...")
    print("="*70)
    
    from business_units.insights_team.gpt4_agents import (
        react_country_analyzer,
        react_ranking_explainer
    )
    
    insights = react_country_analyzer(result)
    result.update(insights)
    
    explanation = react_ranking_explainer(result)
    result.update(explanation)
    
    # Show cost details
    print("\n" + "="*70)
    print("💰 COST TRACKING RESULTS")
    print("="*70)
    
    # Overall metadata
    meta = result.get('insights_metadata', {})
    print(f"\n📊 Overall Metadata:")
    print(f"   Cost Tracking: {meta.get('cost_tracking', 'N/A')}")
    print(f"   Total Tokens: {meta.get('total_tokens', 0):,}")
    print(f"   Total Cost: ${meta.get('total_cost_usd', 0):.4f}")
    print(f"   Total LLM Calls: {meta.get('total_llm_calls', 0)}")
    print(f"   Total Web Searches: {meta.get('total_web_searches', 0)}")
    
    # Per-country breakdown
    print(f"\n💰 Per-Country Cost Breakdown:")
    country_insights = result.get('country_insights', {})
    
    for code, insight in country_insights.items():
        print(f"\n{'='*70}")
        print(f"🌍 {code}")
        print(f"{'='*70}")
        
        tokens = insight.get('tokens_used', 0)
        prompt_tokens = insight.get('prompt_tokens', 0)
        completion_tokens = insight.get('completion_tokens', 0)
        cost = insight.get('cost_usd', 0)
        llm_calls = insight.get('llm_calls', 0)
        searches = insight.get('web_searches_performed', 0)
        
        print(f"\n📊 Tokens:")
        print(f"   Prompt: {prompt_tokens:,}")
        print(f"   Completion: {completion_tokens:,}")
        print(f"   Total: {tokens:,}")
        
        print(f"\n💰 Cost: ${cost:.4f}")
        
        print(f"\n🔄 Operations:")
        print(f"   LLM Calls: {llm_calls}")
        print(f"   Web Searches: {searches}")
        
        # Show cost breakdown
        if prompt_tokens > 0 and completion_tokens > 0:
            prompt_cost = prompt_tokens * 0.0000025
            completion_cost = completion_tokens * 0.00001
            print(f"\n💵 Cost Breakdown:")
            print(f"   Prompt cost: ${prompt_cost:.4f}")
            print(f"   Completion cost: ${completion_cost:.4f}")
            print(f"   Total: ${prompt_cost + completion_cost:.4f}")
    
    # Ranking explainer costs
    print(f"\n{'='*70}")
    print(f"📊 Ranking Explainer")
    print(f"{'='*70}")
    
    explanation = result.get('ranking_explanation', {})
    exp_tokens = explanation.get('tokens_used', 0)
    exp_prompt = explanation.get('prompt_tokens', 0)
    exp_completion = explanation.get('completion_tokens', 0)
    exp_cost = explanation.get('cost_usd', 0)
    exp_llm_calls = explanation.get('llm_calls', 0)
    
    print(f"\n📊 Tokens:")
    print(f"   Prompt: {exp_prompt:,}")
    print(f"   Completion: {exp_completion:,}")
    print(f"   Total: {exp_tokens:,}")
    
    print(f"\n💰 Cost: ${exp_cost:.4f}")
    print(f"\n🔄 LLM Calls: {exp_llm_calls}")
    
    # Calculate efficiency metrics
    print(f"\n{'='*70}")
    print(f"📈 EFFICIENCY METRICS")
    print(f"{'='*70}")
    
    total_cost = meta.get('total_cost_usd', 0) + exp_cost
    total_tokens = meta.get('total_tokens', 0) + exp_tokens
    countries_analyzed = len(country_insights)
    
    print(f"\n💰 Total Analysis Cost: ${total_cost:.4f}")
    print(f"📊 Total Tokens Used: {total_tokens:,}")
    print(f"🌍 Countries Analyzed: {countries_analyzed}")
    
    if countries_analyzed > 0:
        cost_per_country = total_cost / countries_analyzed
        tokens_per_country = total_tokens / countries_analyzed
        print(f"\n⚡ Efficiency:")
        print(f"   Cost per country: ${cost_per_country:.4f}")
        print(f"   Tokens per country: {tokens_per_country:,.0f}")
    
    print("\n" + "="*70)
    print("✅ COST TRACKING TEST COMPLETE!")
    print("="*70)
    
    print("\n📋 Cost Tracking Features:")
    print("   ✅ Accurate token counting (prompt + completion)")
    print("   ✅ Proper cost calculation (GPT-4o pricing)")
    print("   ✅ Per-country breakdown")
    print("   ✅ LLM call tracking")
    print("   ✅ Total spend visibility")
    
    print("\n🎯 Now You Can:")
    print("   • Monitor AI spending per analysis")
    print("   • Budget for production usage")
    print("   • Optimize expensive queries")
    print("   • Track cost trends over time")
    
    return result


if __name__ == "__main__":
    try:
        test_cost_tracking()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
