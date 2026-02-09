"""
Tests for Phase 1 State

Tests state creation, validation, and helper functions.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflows.phase1_state import (
    Phase1State,
    create_phase1_state,
    validate_phase1_state,
    get_stage_progress,
    merge_state_updates,
    extract_final_ranking,
    get_country_presentation,
    get_peer_ranking_for_country,
    state_to_json_safe
)


def test_state_creation():
    """Test creating initial Phase 1 state."""
    print("\n" + "=" * 70)
    print("TEST: State Creation")
    print("=" * 70)

    countries = ["USA", "IND", "CHN"]
    state = create_phase1_state(
        countries=countries,
        research_json_path="data/research.json"
    )

    print(f"✅ Created state for {len(countries)} countries")
    print(f"   Countries: {state['countries']}")
    print(f"   Research path: {state.get('research_json_path')}")
    print(f"   Has execution metadata: {bool(state.get('execution_metadata'))}")

    # Assertions
    assert state["countries"] == countries
    assert state.get("research_json_path") == "data/research.json"
    assert "execution_metadata" in state
    assert "start_time" in state["execution_metadata"]
    assert state["country_research"] == {}
    assert state["expert_presentations"] == {}
    assert state["peer_rankings"] == []

    print("\n✅ State creation: PASSED")


def test_state_validation():
    """Test state validation."""
    print("\n" + "=" * 70)
    print("TEST: State Validation")
    print("=" * 70)

    # Valid state
    valid_state = create_phase1_state(["USA", "IND"])
    is_valid, errors = validate_phase1_state(valid_state)

    print(f"Valid state check: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid == True
    assert len(errors) == 0

    # Invalid: lowercase country code
    invalid_state = create_phase1_state(["usa", "IND"])
    is_valid, errors = validate_phase1_state(invalid_state)

    print(f"\nInvalid state (lowercase) check: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid == False
    assert len(errors) > 0

    # Invalid: wrong length country code
    invalid_state2 = create_phase1_state(["US", "IND"])
    is_valid, errors = validate_phase1_state(invalid_state2)

    print(f"\nInvalid state (wrong length) check: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid == False

    print("\n✅ State validation: PASSED")


def test_stage_progress():
    """Test stage progress tracking."""
    print("\n" + "=" * 70)
    print("TEST: Stage Progress Tracking")
    print("=" * 70)

    state = create_phase1_state(["USA", "IND", "CHN"])

    # Initial progress
    progress = get_stage_progress(state)
    print("\nInitial progress:")
    for stage, status in progress.items():
        print(f"  {stage}: {status}")

    assert progress["research"] == "pending"
    assert progress["presentations"] == "pending"

    # Add research
    state["country_research"] = {"USA": "Research..."}
    progress = get_stage_progress(state)
    print("\nAfter adding 1/3 research:")
    for stage, status in progress.items():
        print(f"  {stage}: {status}")

    assert progress["research"] == "in_progress"

    # Complete research
    state["country_research"] = {
        "USA": "Research...",
        "IND": "Research...",
        "CHN": "Research..."
    }
    progress = get_stage_progress(state)
    print("\nAfter completing research:")
    for stage, status in progress.items():
        print(f"  {stage}: {status}")

    assert progress["research"] == "complete"

    print("\n✅ Stage progress tracking: PASSED")


def test_merge_state_updates():
    """Test merging state updates."""
    print("\n" + "=" * 70)
    print("TEST: Merge State Updates")
    print("=" * 70)

    state = create_phase1_state(["USA", "IND"])

    # Merge research data
    updates = {
        "country_research": {"USA": "USA research..."}
    }
    new_state = merge_state_updates(state, updates)

    print(f"✅ Merged research for USA")
    print(f"   Research keys: {list(new_state['country_research'].keys())}")

    assert "USA" in new_state["country_research"]
    assert new_state["country_research"]["USA"] == "USA research..."

    # Merge more research (should combine dicts)
    updates2 = {
        "country_research": {"IND": "IND research..."}
    }
    new_state = merge_state_updates(new_state, updates2)

    print(f"✅ Merged research for IND")
    print(f"   Research keys: {list(new_state['country_research'].keys())}")

    assert "USA" in new_state["country_research"]
    assert "IND" in new_state["country_research"]

    print("\n✅ Merge state updates: PASSED")


def test_extract_final_ranking():
    """Test extracting final ranking."""
    print("\n" + "=" * 70)
    print("TEST: Extract Final Ranking")
    print("=" * 70)

    state = create_phase1_state(["USA", "IND", "CHN"])

    # Add mock ranking
    state["aggregated_ranking"] = {
        "final_rankings": [
            {"rank": 1, "country_code": "USA", "consensus_score": 9.2},
            {"rank": 2, "country_code": "CHN", "consensus_score": 8.5},
            {"rank": 3, "country_code": "IND", "consensus_score": 7.8}
        ]
    }

    ranking = extract_final_ranking(state)

    print("Extracted ranking:")
    for item in ranking:
        print(f"  {item['rank']}. {item['country_code']} - {item['consensus_score']}")

    assert len(ranking) == 3
    assert ranking[0]["rank"] == 1
    assert ranking[0]["country_code"] == "USA"
    assert ranking[2]["rank"] == 3

    print("\n✅ Extract final ranking: PASSED")


def test_json_safe_serialization():
    """Test JSON-safe state serialization."""
    print("\n" + "=" * 70)
    print("TEST: JSON-Safe Serialization")
    print("=" * 70)

    state = create_phase1_state(["USA", "IND"])
    state["country_research"] = {"USA": "...", "IND": "..."}
    state["expert_presentations"] = {"USA": {...}, "IND": {...}}

    json_safe = state_to_json_safe(state)

    print("JSON-safe state:")
    for key, value in json_safe.items():
        print(f"  {key}: {value}")

    assert "countries" in json_safe
    assert json_safe["research_loaded"] == 2
    assert json_safe["presentations_complete"] == 2
    assert "progress" in json_safe

    print("\n✅ JSON-safe serialization: PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL PHASE 1 STATE TESTS")
    print("=" * 70)

    tests = [
        test_state_creation,
        test_state_validation,
        test_stage_progress,
        test_merge_state_updates,
        test_extract_final_ranking,
        test_json_safe_serialization
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ {test_func.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ {test_func.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)