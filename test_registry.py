"""Test the agent registry."""

from src.registry.agent_registry import (
    AgentRegistry,
    get_registry,
    register_agent
)
from src.registry.agent_metadata import (
    AgentMetadata,
    AgentFramework,
    AgentCapability
)


def test_basic_registration():
    """Test basic agent registration."""
    registry = AgentRegistry()
    
    # Create simple agent
    def dummy_agent(state):
        return {"output": "success"}
    
    # Create metadata
    metadata = AgentMetadata(
        agent_id="test_agent_1",
        name="Test Agent",
        description="A tests agent",
        framework=AgentFramework.CUSTOM,
        capabilities=[AgentCapability.RESEARCH],
        business_unit="test_team",
        contact="tests@company.com"
    )
    
    # Register
    registry.register_agent(metadata, dummy_agent)
    
    # Verify
    assert registry.get_agent("test_agent_1") is not None
    print("✅ Basic registration works!")


def test_decorator_registration():
    """Test decorator-based registration."""
    
    @register_agent(
        agent_id="decorated_agent",
        name="Decorated Agent",
        description="Registered via decorator",
        framework=AgentFramework.CUSTOM,
        capabilities=[AgentCapability.ANALYSIS],
        business_unit="test_team",
        contact="tests@company.com"
    )
    def my_agent(state):
        return {"result": state.get("input", 0) * 2}
    
    # Test it works
    registry = get_registry()
    result = registry.execute_agent("decorated_agent", {"input": 5})
    
    assert result.success
    assert result.outputs["result"] == 10
    print("✅ Decorator registration works!")


def test_discovery():
    """Test agent discovery."""
    registry = AgentRegistry()
    
    # Register multiple agents
    for i in range(3):
        metadata = AgentMetadata(
            agent_id=f"agent_{i}",
            name=f"Agent {i}",
            description=f"Test agent {i}",
            framework=AgentFramework.CUSTOM,
            capabilities=[AgentCapability.RESEARCH],
            business_unit="team_a" if i < 2 else "team_b",
            contact="tests@company.com"
        )
        registry.register_agent(metadata, lambda s: {"done": True})
    
    # Test discovery
    all_agents = registry.list_agents()
    assert len(all_agents) == 3
    
    team_a_agents = registry.find_agents_by_business_unit("team_a")
    assert len(team_a_agents) == 2
    
    print("✅ Discovery works!")


def test_execution():
    """Test agent execution."""
    registry = AgentRegistry()
    
    # Register agent with specific inputs/outputs
    def calculator_agent(state):
        a = state["a"]
        b = state["b"]
        return {"sum": a + b, "product": a * b}
    
    metadata = AgentMetadata(
        agent_id="calculator",
        name="Calculator",
        description="Does math",
        framework=AgentFramework.CUSTOM,
        capabilities=[AgentCapability.ANALYSIS],
        business_unit="math_team",
        contact="math@company.com",
        required_inputs=["a", "b"],
        output_keys=["sum", "product"]
    )
    
    registry.register_agent(metadata, calculator_agent)
    
    # Execute
    result = registry.execute_agent("calculator", {"a": 5, "b": 3})
    
    assert result.success
    assert result.outputs["sum"] == 8
    assert result.outputs["product"] == 15
    print("✅ Execution works!")


if __name__ == "__main__":
    test_basic_registration()
    test_decorator_registration()
    test_discovery()
    test_execution()
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✅")
    print("="*70)
    
    # Show summary
    registry = get_registry()
    registry.print_summary()
