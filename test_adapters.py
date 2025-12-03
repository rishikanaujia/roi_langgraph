"""Test agent adapters."""

from src.adapters.base_adapter import CustomAgentAdapter, PassthroughAdapter


def test_custom_adapter():
    """Test custom agent adapter."""
    
    # Define simple agent
    def my_agent(state):
        x = state.get("x", 0)
        return {"result": x * 2, "status": "success"}
    
    # Create adapter
    adapter = CustomAgentAdapter(
        my_agent,
        config={"required_inputs": ["x"], "output_keys": ["result", "status"]}
    )
    
    # Test execution
    state = {"x": 5}
    result = adapter.execute(state)
    
    assert result["result"] == 10
    assert result["status"] == "success"
    print("✅ Custom adapter works!")


def test_passthrough_adapter():
    """Test passthrough adapter."""
    
    def simple_agent(state):
        return {"output": state["input"].upper()}
    
    adapter = PassthroughAdapter(simple_agent)
    
    result = adapter({"input": "hello"})
    assert result["output"] == "HELLO"
    print("✅ Passthrough adapter works!")


def test_callable_adapter():
    """Test that adapters are callable."""
    
    def agent(state):
        return {"value": state["x"] + state["y"]}
    
    adapter = CustomAgentAdapter(agent)
    
    # Should work with adapter(state) syntax
    result = adapter({"x": 3, "y": 4})
    assert result["value"] == 7
    print("✅ Callable adapter works!")


if __name__ == "__main__":
    test_custom_adapter()
    test_passthrough_adapter()
    test_callable_adapter()
    
    print("\n" + "="*70)
    print("ALL ADAPTER TESTS PASSED! ✅")
    print("="*70)
