"""Test LangChain GPT-4 agents."""

from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

# Import all agents
import business_units.data_team.nasa_agent
import business_units.finance_team.financial_agents
import business_units.insights_team.gpt4_agents  # Now LangChain!
import business_units.ranking_team.agents


def test_langchain_upgrade():
    """Test upgraded LangChain agents."""
    
    print("="*70)
    print("🔄 LANGCHAIN UPGRADE TEST")
    print("="*70)
    
    # Show registered agents
    registry = get_registry()
    print("\n📊 Registered Agents:")
    registry.print_summary()
    
    # Check framework types - FIXED
    print("\n🔍 Agent Frameworks:")
    for agent_id, agent_data in registry._agents.items():
        agent = agent_data['metadata']  # Fixed: access metadata
        print(f"   {agent.name}: {agent.framework.value}")
    
    # Run workflow
    print("\n" + "="*70)
    print("🚀 Running Complete Pipeline with LangChain Agents")
    print("="*70)
    
    workflow = CountryComparisonWorkflow()
    
    result = workflow.run(
        countries=["USA", "BRA"],
        query="Investment analysis with LangChain"
    )
    
    # Generate insights with LangChain
    print("\n🤖 Generating LangChain AI Insights...")
    
    from business_units.insights_team.gpt4_agents import (
        langchain_country_analyzer,
        langchain_ranking_explainer
    )
    
    insights = langchain_country_analyzer(result)
    result.update(insights)
    
    explanation = langchain_ranking_explainer(result)
    result.update(explanation)
    
    # Show results
    print("\n" + "="*70)
    print("📊 RESULTS WITH LANGCHAIN")
    print("="*70)
    
    # Show cost tracking (LangChain feature!)
    insights_meta = result.get('insights_metadata', {})
    print(f"\n💰 LangChain Cost Tracking:")
    print(f"   Total Tokens: {insights_meta.get('total_tokens', 0)}")
    print(f"   Total Cost: ${insights_meta.get('total_cost_usd', 0):.4f}")
    print(f"   Model: {insights_meta.get('model', 'N/A')}")
    print(f"   Framework: {insights_meta.get('framework', 'N/A')}")
    
    # Show ranking
    print(f"\n🏆 Rankings:")
    ranking = result.get('ranking', {})
    for country in ranking.get('ranked_countries', []):
        print(f"   {country['rank']}. {country['country_code']} (Score: {country['overall_score']:.1f})")
    
    # Show country reports briefly
    print(f"\n📊 Country Analysis:")
    for code, report in result.get('country_reports', {}).items():
        metrics = report.get('aggregate_metrics', {})
        print(f"   {code}: IRR={metrics.get('average_irr', 0):.2f}%, "
              f"LCOE=${metrics.get('average_lcoe', 0):.2f}/MWh")
    
    # Show AI insights
    print(f"\n🤖 LangChain Country Insights:")
    country_insights = result.get('country_insights', {})
    for code, insight in country_insights.items():
        print(f"\n   {code}:")
        analysis = insight.get('analysis', 'N/A')
        # Print first 150 chars
        print(f"      {analysis[:150]}...")
        print(f"      💰 Cost: ${insight.get('cost_usd', 0):.4f}, "
              f"Tokens: {insight.get('tokens_used', 0)}")
    
    # Show ranking explanation
    print(f"\n🤖 LangChain Ranking Explanation:")
    explanation = result.get('ranking_explanation', {})
    expl_text = explanation.get('explanation', 'N/A')
    print(f"\n{expl_text}")
    
    # Show explanation cost
    print(f"\n   💰 Explanation Cost: ${explanation.get('cost_usd', 0):.4f}, "
          f"Tokens: {explanation.get('tokens_used', 0)}")
    
    print("\n" + "="*70)
    print("✅ LANGCHAIN UPGRADE TEST COMPLETE!")
    print("="*70)
    
    print("\n📋 LangChain Benefits Demonstrated:")
    print("   ✅ Prompt templates (cleaner code)")
    print("   ✅ Automatic cost tracking (per agent!)")
    print("   ✅ Token usage monitoring")
    print("   ✅ Built-in retry logic")
    print("   ✅ Clean chain syntax (prompt | llm | parser)")
    
    print("\n🎯 Multi-Framework System:")
    print("   ✅ Custom: 4 agents (NASA, Financial, Ranking)")
    print("   ✅ LangChain: 2 agents (GPT-4 insights)")
    print("   ✅ LangGraph: 1 workflow (orchestration)")
    
    return result


if __name__ == "__main__":
    test_langchain_upgrade()
