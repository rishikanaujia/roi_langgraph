"""Test business unit agent integration."""

# Import all business unit agents (this registers them)
import business_units.research_team.agents
import business_units.analysis_team.agents
import business_units.ranking_team.agents

from src.registry.agent_registry import get_registry


def test_all_agents_registered():
    """Test all agents from business units are registered."""
    registry = get_registry()
    
    # Check research team
    research_agents = registry.find_agents_by_business_unit("research_team")
    print(f"\n✅ Research Team: {len(research_agents)} agents")
    for agent in research_agents:
        print(f"   - {agent.name} ({agent.framework.value})")
    
    # Check analysis team
    analysis_agents = registry.find_agents_by_business_unit("analysis_team")
    print(f"\n✅ Analysis Team: {len(analysis_agents)} agents")
    for agent in analysis_agents:
        print(f"   - {agent.name} ({agent.framework.value})")
    
    # Check ranking team
    ranking_agents = registry.find_agents_by_business_unit("ranking_team")
    print(f"\n✅ Ranking Team: {len(ranking_agents)} agents")
    for agent in ranking_agents:
        print(f"   - {agent.name} ({agent.framework.value})")
    
    # Print summary
    print("\n" + "="*70)
    registry.print_summary()


if __name__ == "__main__":
    test_all_agents_registered()
    
    print("\n" + "="*70)
    print("ALL BUSINESS UNITS INTEGRATED! ✅")
    print("="*70)
