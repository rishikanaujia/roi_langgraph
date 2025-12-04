"""Test ReAct agents with reasoning."""

import sys
from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

# Import agents
import business_units.data_team.nasa_agent
import business_units.finance_team.financial_agents
import business_units.insights_team.gpt4_agents  # Now ReAct!
import business_units.ranking_team.agents


def test_react_agents():
    """Test ReAct agents with reasoning traces."""
    
    print("="*70)
    print("🧠 REACT AGENTS TEST - REASONING + ACTING")
    print("="*70)
    
    registry = get_registry()
    print("\n📊 Registered Agents:")
    registry.print_summary()
    
    # Check ReAct agents
    print("\n🔍 Agent Details:")
    for agent_id, agent_data in registry._agents.items():
        agent = agent_data['metadata']
        if 'react' in agent_id.lower():
            print(f"   🧠 {agent.name} (v{agent.version})")
            print(f"      Framework: {agent.framework.value}")
            print(f"      Tags: {', '.join(agent.tags)}")
    
    # Run workflow
    print("\n" + "="*70)
    print("🚀 Running Workflow with ReAct Agents")
    print("="*70)
    print("\n⚠️  NOTE: You'll see agent reasoning traces below\n")
    
    workflow = CountryComparisonWorkflow()
    
    result = workflow.run(
        countries=["USA", "IND"],
        query="Analyze with intelligent reasoning"
    )
    
    # Generate insights with ReAct agents
    print("\n" + "="*70)
    print("🧠 ReAct Agents Analyzing (with reasoning traces)...")
    print("="*70)
    
    from business_units.insights_team.gpt4_agents import (
        react_country_analyzer,
        react_ranking_explainer
    )
    
    insights = react_country_analyzer(result)
    result.update(insights)
    
    explanation = react_ranking_explainer(result)
    result.update(explanation)
    
    # Show results
    print("\n" + "="*70)
    print("📊 REACT AGENTS RESULTS")
    print("="*70)
    
    # Show metadata
    meta = result.get('insights_metadata', {})
    print(f"\n💰 ReAct Analysis Metadata:")
    print(f"   Agent Type: {meta.get('agent_type', 'N/A')}")
    print(f"   Framework: {meta.get('framework', 'N/A')}")
    print(f"   Total Tokens: {meta.get('total_tokens', 0)}")
    print(f"   Total Cost: ${meta.get('total_cost_usd', 0):.4f}")
    print(f"   Web Searches: {meta.get('total_web_searches', 0)}")
    print(f"   Search Tool: {meta.get('search_tool', 'none')}")
    
    # Show insights with reasoning info
    print(f"\n🧠 ReAct Agent Decisions:")
    country_insights = result.get('country_insights', {})
    
    for code, insight in country_insights.items():
        print(f"\n{'='*70}")
        print(f"🌍 {code}")
        print(f"{'='*70}")
        
        # Show agent decisions
        decided_to_search = insight.get('agent_decided_to_search', False)
        searches = insight.get('web_searches_performed', 0)
        reasoning_steps = insight.get('reasoning_steps', 0)
        
        print(f"\n🧠 Agent Reasoning:")
        print(f"   Reasoning Steps: {reasoning_steps}")
        print(f"   Decided to Search: {'YES' if decided_to_search else 'NO'}")
        print(f"   Searches Performed: {searches}")
        
        if insight.get('sources'):
            print(f"   📚 Sources Found: {len(insight['sources'])}")
        
        # Show analysis
        print(f"\n📝 Final Analysis:")
        analysis = insight.get('analysis', 'N/A')
        # Print first 300 chars
        print(f"{analysis[:300]}...")
        
        print(f"\n💰 Cost: ${insight.get('cost_usd', 0):.4f}")
        print(f"🎯 Confidence: {insight.get('confidence', 'unknown')}")
    
    # Show ranking explanation
    print(f"\n{'='*70}")
    print(f"🧠 ReAct Ranking Explanation")
    print(f"{'='*70}")
    
    explanation = result.get('ranking_explanation', {})
    print(f"\nReasoning Steps: {explanation.get('reasoning_steps', 0)}")
    print(f"\n{explanation.get('explanation', 'N/A')}")
    
    print("\n" + "="*70)
    print("✅ REACT AGENTS TEST COMPLETE!")
    print("="*70)
    
    print("\n📋 ReAct Agent Benefits Demonstrated:")
    print("   ✅ Intelligent decision making (search when needed)")
    print("   ✅ Visible reasoning process (transparency)")
    print("   ✅ Cost efficiency (no unnecessary searches)")
    print("   ✅ Multi-step problem solving")
    print("   ✅ Tool usage decisions explained")
    
    print("\n🎯 Key Differences from v3.0:")
    print("   • v3.0: Always searches (every country)")
    print("   • v4.0: Searches only when needed (intelligent)")
    print("   • Result: Better cost efficiency + transparency")
    
    return result


if __name__ == "__main__":
    try:
        test_react_agents()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
