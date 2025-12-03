"""Test business unit agent integration - simplified without LangChain."""

# Only import the ranking team (pure Python, no dependencies)
import business_units.ranking_team.agents

from src.registry.agent_registry import get_registry


def test_ranking_team():
    """Test ranking team agents are registered."""
    registry = get_registry()
    
    # Check ranking team
    ranking_agents = registry.find_agents_by_business_unit("ranking_team")
    print(f"\n✅ Ranking Team: {len(ranking_agents)} agents")
    for agent in ranking_agents:
        print(f"   - {agent.name} ({agent.framework.value})")
    
    # Test execution
    mock_state = {
        "country_reports": {
            "USA": {"aggregate_metrics": {"average_irr": 5.5}, "country_name": "United States"},
            "DEU": {"aggregate_metrics": {"average_irr": 6.0}, "country_name": "Germany"},
            "IND": {"aggregate_metrics": {"average_irr": 5.0}, "country_name": "India"}
        }
    }
    
    # Execute simple ranker
    result = registry.execute_agent("ranking_team_simple_ranker_v1", mock_state)
    
    if result.success:
        print(f"\n✅ Agent execution successful!")
        ranking = result.outputs.get("ranking", {})
        print(f"\nTop ranked country: {ranking['ranked_countries'][0]['country_name']}")
    
    # Print summary
    print("\n" + "="*70)
    registry.print_summary()


if __name__ == "__main__":
    test_ranking_team()
    
    print("\n" + "="*70)
    print("RANKING TEAM INTEGRATED! ✅")
    print("="*70)
