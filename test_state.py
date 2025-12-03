"""Test shared state system."""

from src.state.shared_state import (
    create_initial_state,
    merge_state_updates,
    add_location_analysis,
    add_error,
    log_agent_execution
)


def test_initial_state():
    """Test initial state creation."""
    state = create_initial_state(
        countries=["USA", "DEU"],
        query="Compare renewable energy"
    )
    
    assert state["countries"] == ["USA", "DEU"]
    assert state["query"] == "Compare renewable energy"
    assert state["location_analyses"] == []
    assert state["country_reports"] == {}
    print("✅ Initial state creation works!")


def test_state_updates():
    """Test state update merging."""
    state = create_initial_state(["USA"])
    
    # Add location analysis (should append to list)
    updates1 = add_location_analysis(state, {"location": "Texas", "result": "good"})
    state = merge_state_updates(state, updates1)
    
    updates2 = add_location_analysis(state, {"location": "California", "result": "great"})
    state = merge_state_updates(state, updates2)
    
    assert len(state["location_analyses"]) == 2
    print("✅ State updates work!")


def test_error_logging():
    """Test error logging."""
    state = create_initial_state(["USA"])
    
    # Add errors
    updates1 = add_error(state, "Error 1")
    state = merge_state_updates(state, updates1)
    
    updates2 = add_error(state, "Error 2")
    state = merge_state_updates(state, updates2)
    
    assert len(state["errors"]) == 2
    assert "Error 1" in state["errors"]
    print("✅ Error logging works!")


def test_agent_execution_logging():
    """Test agent execution logging."""
    state = create_initial_state(["USA"])
    
    # Log agent execution
    updates = log_agent_execution(state, "agent_1", 1.5, True)
    state = merge_state_updates(state, updates)
    
    executions = state["execution_metadata"]["agent_executions"]
    assert len(executions) == 1
    assert executions[0]["agent_id"] == "agent_1"
    assert executions[0]["execution_time"] == 1.5
    print("✅ Agent execution logging works!")


if __name__ == "__main__":
    test_initial_state()
    test_state_updates()
    test_error_logging()
    test_agent_execution_logging()
    
    print("\n" + "="*70)
    print("ALL STATE TESTS PASSED! ✅")
    print("="*70)
