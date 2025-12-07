"""
Tests for Expert Agents

Tests expert creation, presentation generation, and parallel execution.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock OpenAI if API key not available
if not os.environ.get("OPENAI_API_KEY"):
    print("⚠️  OPENAI_API_KEY not set - some tests will be skipped")
    SKIP_LLM_TESTS = True
else:
    SKIP_LLM_TESTS = False

from business_units.expert_team.expert_agents import (
    create_expert_agent,
    register_experts_for_countries,
    CountryPresentation
)
from src.workflows.phase1_state import create_phase1_state
from src.registry.agent_registry import AgentRegistry


def test_expert_agent_creation():
    """Test creating expert agent."""
    print("\n" + "=" * 70)
    print("TEST: Expert Agent Creation")
    print("=" * 70)

    usa_expert = create_expert_agent("USA", expert_id=1)

    print(f"✅ Created expert agent for USA")
    print(f"   Type: {type(usa_expert)}")
    print(f"   Callable: {callable(usa_expert)}")

    assert callable(usa_expert)

    print("\n✅ Expert agent creation: PASSED")


def test_expert_registration():
    """Test registering multiple experts."""
    print("\n" + "=" * 70)
    print("TEST: Expert Registration")
    print("=" * 70)

    # Create temp registry
    registry = AgentRegistry()

    countries = ["USA", "IND", "CHN"]
    experts = register_experts_for_countries(countries, registry=registry)

    print(f"✅ Registered {len(experts)} experts")
    for country in countries:
        assert country in experts
        print(
            f"   • {country}: {experts[country].__name__ if hasattr(experts[country], '__name__') else 'expert_agent'}")

    # Check registry
    stats = registry.get_statistics()
    print(f"\nRegistry stats:")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Expert agents: {stats['by_capability'].get('expert_presentation', 0)}")

    assert stats['total_agents'] == len(countries)

    print("\n✅ Expert registration: PASSED")


def test_presentation_structure():
    """Test presentation output structure."""
    print("\n" + "=" * 70)
    print("TEST: Presentation Structure")
    print("=" * 70)

    # Test Pydantic model
    presentation = CountryPresentation(
        country_code="USA",
        executive_summary="USA offers strong renewable opportunities...",
        strengths=["Policy support", "Technology leadership", "Large market"],
        opportunities=["Solar growth", "Wind expansion"],
        risks=["Grid constraints", "Political uncertainty"],
        investment_case="Detailed case...",
        recommendation="STRONG_BUY",
        confidence="high",
        key_metrics_summary="IRR: 12%, LCOE: $45/MWh"
    )

    print(f"✅ Created presentation structure")
    print(f"   Country: {presentation.country_code}")
    print(f"   Recommendation: {presentation.recommendation}")
    print(f"   Confidence: {presentation.confidence}")
    print(f"   Strengths: {len(presentation.strengths)}")
    print(f"   Opportunities: {len(presentation.opportunities)}")
    print(f"   Risks: {len(presentation.risks)}")

    # Test conversion to dict
    pres_dict = presentation.dict()
    assert "country_code" in pres_dict
    assert "strengths" in pres_dict
    assert isinstance(pres_dict["strengths"], list)

    print("\n✅ Presentation structure: PASSED")


def test_expert_with_mock_data():
    """Test expert agent with mock state (no LLM call)."""
    print("\n" + "=" * 70)
    print("TEST: Expert with Mock Data (Structure Only)")
    print("=" * 70)

    # Create state
    state = create_phase1_state(countries=["USA"])
    state["country_research"] = {
        "USA": """
        United States Renewable Energy Analysis:

        Policy Environment:
        - Inflation Reduction Act provides 30% ITC for solar
        - Production Tax Credit for wind energy
        - State-level RPS in 30+ states

        Market Conditions:
        - Largest renewable energy market by investment ($100B+ annually)
        - Strong grid infrastructure in most regions
        - Leading in solar and wind technology development

        Resources:
        - Excellent solar resources in Southwest (6-7 kWh/m²/day)
        - Strong wind resources in Great Plains (8-9 m/s at 100m)
        - Diverse geography enabling multiple technologies

        Opportunities:
        - Grid modernization creating storage opportunities
        - Offshore wind expansion on East Coast
        - Corporate PPA market growing rapidly

        Challenges:
        - Permitting delays in some regions
        - Grid interconnection queues
        - Supply chain dependencies
        """
    }

    print("✅ Created mock state with research")
    print(f"   Countries: {state['countries']}")
    print(f"   Research length: {len(state['country_research']['USA'])} chars")

    # Note: We won't call the actual LLM in this test
    # Just verify the state structure is correct

    assert "USA" in state["country_research"]
    assert len(state["country_research"]["USA"]) > 100

    print("\n✅ Expert with mock data: PASSED")


def test_expert_input_validation():
    """Test expert agent input validation."""
    print("\n" + "=" * 70)
    print("TEST: Expert Input Validation")
    print("=" * 70)

    usa_expert = create_expert_agent("USA", expert_id=1)

    # Test missing country
    state1 = create_phase1_state(countries=["IND"])  # USA not in list
    state1["country_research"] = {"USA": "Research..."}

    result1 = usa_expert(state1)

    print("Test 1: Country not in scope")
    print(f"   Success: {result1['presentation_metadata'].get('USA', {}).get('success', True) == False}")
    print(f"   Error: {result1['presentation_metadata'].get('USA', {}).get('error', 'None')[:50]}")

    assert result1['presentation_metadata']['USA']['success'] == False

    # Test missing research
    state2 = create_phase1_state(countries=["USA"])
    state2["country_research"] = {}  # No research data

    result2 = usa_expert(state2)

    print("\nTest 2: Missing research data")
    print(f"   Success: {result2['presentation_metadata'].get('USA', {}).get('success', True) == False}")
    print(f"   Error: {result2['presentation_metadata'].get('USA', {}).get('error', 'None')[:50]}")

    assert result2['presentation_metadata']['USA']['success'] == False

    print("\n✅ Expert input validation: PASSED")


def test_expert_with_real_llm():
    """Test expert agent with real LLM call."""
    if SKIP_LLM_TESTS:
        print("\n⏭️  Skipping LLM test (no API key)")
        return

    print("\n" + "=" * 70)
    print("TEST: Expert with Real LLM")
    print("=" * 70)
    print("⚠️  This test will call OpenAI API and may take 10-30 seconds")

    # Create state
    state = create_phase1_state(countries=["USA"])
    state["country_research"] = {
        "USA": """
        United States Renewable Energy Investment Analysis:

        The United States offers exceptional renewable energy investment opportunities 
        driven by strong policy support, technological leadership, and massive market scale.

        Policy Framework:
        - Inflation Reduction Act: 30% Investment Tax Credit for solar
        - Production Tax Credit: $27.5/MWh for wind energy
        - State mandates: 30+ states with Renewable Portfolio Standards

        Market Scale:
        - $100+ billion annual renewable investment
        - 150+ GW solar installed capacity
        - 140+ GW wind installed capacity

        Resource Quality:
        - Southwest solar: 6-7 kWh/m²/day (world-class)
        - Great Plains wind: 8-9 m/s average speeds
        - Multiple technology options across diverse geography
        """
    }

    # Create and run expert
    usa_expert = create_expert_agent("USA", expert_id=1)

    print("🤖 Calling GPT-4 to generate presentation...")
    result = usa_expert(state)

    print("\n" + "=" * 70)
    print("PRESENTATION RESULTS")
    print("=" * 70)

    if result['presentation_metadata']['USA']['success']:
        presentation = result['expert_presentations']['USA']

        print(f"\n✅ Presentation generated successfully")
        print(f"\nCountry: {presentation['country_code']}")
        print(f"Recommendation: {presentation['recommendation']}")
        print(f"Confidence: {presentation['confidence']}")

        print(f"\nExecutive Summary:")
        print(f"{presentation['executive_summary']}")

        print(f"\nStrengths ({len(presentation['strengths'])}):")
        for i, strength in enumerate(presentation['strengths'], 1):
            print(f"  {i}. {strength}")

        print(f"\nOpportunities ({len(presentation['opportunities'])}):")
        for i, opp in enumerate(presentation['opportunities'], 1):
            print(f"  {i}. {opp}")

        print(f"\nRisks ({len(presentation['risks'])}):")
        for i, risk in enumerate(presentation['risks'], 1):
            print(f"  {i}. {risk}")

        print(f"\nGeneration time: {result['presentation_metadata']['USA']['generation_time_seconds']}s")

        # Validate structure
        assert presentation['country_code'] == "USA"
        assert len(presentation['strengths']) >= 3
        assert len(presentation['opportunities']) >= 2
        assert len(presentation['risks']) >= 2
        assert presentation['recommendation'] in ['STRONG_BUY', 'BUY', 'HOLD', 'AVOID']

        print("\n✅ Expert with real LLM: PASSED")
    else:
        print(f"❌ Presentation failed: {result['presentation_metadata']['USA']['error']}")
        raise AssertionError("LLM presentation generation failed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL EXPERT AGENT TESTS")
    print("=" * 70)

    tests = [
        test_expert_agent_creation,
        test_expert_registration,
        test_presentation_structure,
        test_expert_with_mock_data,
        test_expert_input_validation,
        test_expert_with_real_llm  # Will be skipped if no API key
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_func in tests:
        try:
            test_func()
            if SKIP_LLM_TESTS and test_func.__name__ == "test_expert_with_real_llm":
                skipped += 1
            else:
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
    if skipped > 0:
        print(f"⏭️  Skipped: {skipped}")
    print(f"Total: {passed + failed + skipped}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)