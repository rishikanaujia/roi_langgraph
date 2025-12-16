"""
Tests for Research Loader

Tests JSON loading, country normalization, and Phase 1 integration.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from business_units.data_team.research_loader import (
    normalize_country_name,
    load_research_from_json,
    load_research_from_file,
    research_loader,
    COUNTRY_NAME_TO_CODE
)
from src.workflows.phase1_state import create_phase1_state


def test_country_normalization():
    """Test country name normalization."""
    print("\n" + "=" * 70)
    print("TEST: Country Name Normalization")
    print("=" * 70)

    test_cases = [
        ("United States", "USA"),
        ("usa", "USA"),
        ("US", "USA"),
        ("India", "IND"),
        ("india", "IND"),
        ("China", "CHN"),
        ("Germany", "DEU"),
        ("Unknown Country", None),
    ]

    for input_name, expected_code in test_cases:
        result = normalize_country_name(input_name)
        status = "✅" if result == expected_code else "❌"
        print(f"{status} '{input_name}' -> {result} (expected: {expected_code})")
        assert result == expected_code, f"Failed for {input_name}"

    print("\n✅ Country normalization: PASSED")


def test_load_from_json():
    """Test loading research from JSON data."""
    print("\n" + "=" * 70)
    print("TEST: Load from JSON Data")
    print("=" * 70)

    json_data = [
        {
            "country_name": "United States",
            "research": "USA has strong renewable energy policies..."
        },
        {
            "country_name": "India",
            "research": "India is rapidly expanding solar capacity..."
        },
        {
            "country_name": "China",
            "research": "China leads in renewable manufacturing..."
        }
    ]

    research = load_research_from_json(json_data)

    print(f"Loaded {len(research)} countries:")
    for code, text in research.items():
        print(f"  {code}: {len(text)} chars")

    assert len(research) == 3
    assert "USA" in research
    assert "IND" in research
    assert "CHN" in research
    assert len(research["USA"]) > 0

    print("\n✅ Load from JSON data: PASSED")


def test_load_from_file():
    """Test loading research from JSON file."""
    print("\n" + "=" * 70)
    print("TEST: Load from File")
    print("=" * 70)

    # Create temporary file
    json_data = [
        {"country_name": "USA", "research": "USA research..."},
        {"country_name": "IND", "research": "India research..."}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_data, f)
        temp_path = f.name

    try:
        research, errors = load_research_from_file(temp_path)

        print(f"Loaded {len(research)} countries from file")
        print(f"Errors: {len(errors)}")

        assert len(research) == 2
        assert "USA" in research
        assert "IND" in research
        assert len(errors) == 0

        print("\n✅ Load from file: PASSED")

    finally:
        # Clean up
        Path(temp_path).unlink()


def test_invalid_json():
    """Test handling of invalid JSON."""
    print("\n" + "=" * 70)
    print("TEST: Invalid JSON Handling")
    print("=" * 70)

    # Missing research field
    invalid_data = [
        {"country_name": "USA"}  # Missing 'research'
    ]

    research = load_research_from_json(invalid_data)

    print(f"Loaded {len(research)} countries (should be 0)")
    assert len(research) == 0

    # Invalid country name
    invalid_data2 = [
        {"country_name": "Unknown Country", "research": "Some research..."}
    ]

    research2 = load_research_from_json(invalid_data2)

    print(f"Loaded {len(research2)} countries (should be 0)")
    assert len(research2) == 0

    print("\n✅ Invalid JSON handling: PASSED")


def test_agent_with_direct_json():
    """Test research_loader agent with direct JSON."""
    print("\n" + "=" * 70)
    print("TEST: Agent with Direct JSON")
    print("=" * 70)

    # Create state
    state = create_phase1_state(countries=["USA", "IND"])

    # Add research data
    state["research_json_data"] = [
        {"country_name": "USA", "research": "USA renewable research..."},
        {"country_name": "India", "research": "India renewable research..."}
    ]

    # Run agent
    result = research_loader(state)

    print(f"\nAgent results:")
    print(f"  Countries loaded: {len(result['country_research'])}")
    print(f"  Total chars: {result['research_metadata']['total_characters']}")
    print(f"  Source: {result['research_metadata']['source']}")

    assert "country_research" in result
    assert "research_metadata" in result
    assert len(result["country_research"]) == 2
    assert "USA" in result["country_research"]
    assert "IND" in result["country_research"]

    print("\n✅ Agent with direct JSON: PASSED")


def test_agent_with_file():
    """Test research_loader agent with file path."""
    print("\n" + "=" * 70)
    print("TEST: Agent with File Path")
    print("=" * 70)

    # Create temporary file
    json_data = [
        {"country_name": "USA", "research": "USA data..."},
        {"country_name": "China", "research": "China data..."},
        {"country_name": "India", "research": "India data..."}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_data, f)
        temp_path = f.name

    try:
        # Create state with file path
        state = create_phase1_state(countries=["USA", "CHN", "IND"])
        state["research_json_path"] = temp_path

        # Run agent
        result = research_loader(state)

        print(f"\nAgent results:")
        print(f"  Countries loaded: {len(result['country_research'])}")
        print(f"  Source: {result['research_metadata']['source']}")

        assert len(result["country_research"]) == 3
        assert "USA" in result["country_research"]
        assert "CHN" in result["country_research"]
        assert "IND" in result["country_research"]

        print("\n✅ Agent with file path: PASSED")

    finally:
        Path(temp_path).unlink()


def test_country_filtering():
    """Test filtering research to specific countries."""
    print("\n" + "=" * 70)
    print("TEST: Country Filtering")
    print("=" * 70)

    # Create state requesting only USA and IND
    state = create_phase1_state(countries=["USA", "IND"])

    # Provide research for 3 countries
    state["research_json_data"] = [
        {"country_name": "USA", "research": "USA..."},
        {"country_name": "India", "research": "India..."},
        {"country_name": "China", "research": "China..."}  # Should be filtered out
    ]

    result = research_loader(state)

    print(f"\nFiltered results:")
    print(f"  Requested: {state['countries']}")
    print(f"  Loaded: {list(result['country_research'].keys())}")

    assert len(result["country_research"]) == 2
    assert "USA" in result["country_research"]
    assert "IND" in result["country_research"]
    assert "CHN" not in result["country_research"]

    print("\n✅ Country filtering: PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL RESEARCH LOADER TESTS")
    print("=" * 70)

    tests = [
        test_country_normalization,
        test_load_from_json,
        test_load_from_file,
        test_invalid_json,
        test_agent_with_direct_json,
        test_agent_with_file,
        test_country_filtering
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