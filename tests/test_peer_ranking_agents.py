"""
Tests for Peer Ranking Agents

Tests peer ranker creation, ranking logic, and parallel execution.
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

from business_units.ranking_team.peer_ranking_agents import (
    create_peer_ranker_agent,
    register_peer_rankers,
    format_presentations_for_ranking,
    PeerRankingResult,
    CountryRanking
)
from src.workflows.phase1_state import create_phase1_state
from src.registry.agent_registry import AgentRegistry


def test_peer_ranker_creation():
    """Test creating peer ranker agent."""
    print("\n" + "=" * 70)
    print("TEST: Peer Ranker Creation")
    print("=" * 70)

    peer_1 = create_peer_ranker_agent(ranker_id=1)

    print(f"✅ Created peer ranker #1")
    print(f"   Type: {type(peer_1)}")
    print(f"   Callable: {callable(peer_1)}")

    assert callable(peer_1)

    print("\n✅ Peer ranker creation: PASSED")


def test_peer_registration():
    """Test registering multiple peer rankers."""
    print("\n" + "=" * 70)
    print("TEST: Peer Ranker Registration")
    print("=" * 70)

    # Create temp registry
    registry = AgentRegistry()

    num_peers = 5
    peers = register_peer_rankers(num_peers=num_peers, registry=registry)

    print(f"✅ Registered {len(peers)} peer rankers")
    for peer_id in range(1, num_peers + 1):
        assert peer_id in peers
        print(f"   • Peer #{peer_id}: registered")

    # Check registry
    stats = registry.get_statistics()
    print(f"\nRegistry stats:")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Peer rankers: {stats['by_capability'].get('peer_ranking', 0)}")

    assert stats['total_agents'] == num_peers

    print("\n✅ Peer ranker registration: PASSED")


def test_ranking_structure():
    """Test ranking output structure."""
    print("\n" + "=" * 70)
    print("TEST: Ranking Structure")
    print("=" * 70)

    # Test individual country ranking
    country_ranking = CountryRanking(
        country_code="USA",
        rank=1,
        score=9.2,
        reasoning="Strong policy support and resource quality make USA the top choice.",
        strengths_noted=["Policy support", "Resource quality", "Market size"],
        concerns_noted=["Grid constraints", "Political uncertainty"]
    )

    print(f"✅ Created country ranking")
    print(f"   Country: {country_ranking.country_code}")
    print(f"   Rank: {country_ranking.rank}")
    print(f"   Score: {country_ranking.score}/10")

    # Test complete peer ranking
    peer_ranking = PeerRankingResult(
        peer_id="peer_ranker_1",
        rankings=[country_ranking],
        methodology="Weighted scoring across financial, resource, and risk factors",
        top_choice_justification="USA combines strong policy with excellent resources"
    )

    print(f"\n✅ Created peer ranking result")
    print(f"   Peer: {peer_ranking.peer_id}")
    print(f"   Countries ranked: {len(peer_ranking.rankings)}")
    print(f"   Methodology: {peer_ranking.methodology[:50]}...")

    # Test conversion to dict
    ranking_dict = peer_ranking.model_dump()
    assert "peer_id" in ranking_dict
    assert "rankings" in ranking_dict
    assert isinstance(ranking_dict["rankings"], list)

    print("\n✅ Ranking structure: PASSED")


def test_presentation_formatting():
    """Test formatting presentations for peer review."""
    print("\n" + "=" * 70)
    print("TEST: Presentation Formatting")
    print("=" * 70)

    # Create mock presentations
    presentations = {
        "USA": {
            "country_code": "USA",
            "executive_summary": "USA offers strong renewable opportunities...",
            "strengths": ["Policy support", "Technology", "Market scale"],
            "opportunities": ["Solar growth", "Wind expansion"],
            "risks": ["Grid issues", "Political"],
            "investment_case": "Detailed case for USA investment...",
            "recommendation": "STRONG_BUY",
            "confidence": "high"
        },
        "IND": {
            "country_code": "IND",
            "executive_summary": "India has rapid growth potential...",
            "strengths": ["Growth rate", "Manufacturing", "Demand"],
            "opportunities": ["Capacity expansion", "Export hub"],
            "risks": ["Financing", "Infrastructure"],
            "investment_case": "Detailed case for India investment...",
            "recommendation": "BUY",
            "confidence": "medium"
        }
    }

    formatted = format_presentations_for_ranking(presentations)

    print(f"✅ Formatted {len(presentations)} presentations")
    print(f"   Total length: {len(formatted)} chars")
    print(f"\nFormatted text preview:")
    print(formatted[:500] + "...\n")

    # Verify all countries are included
    assert "USA" in formatted
    assert "IND" in formatted
    assert "Policy support" in formatted
    assert "STRONG_BUY" in formatted

    print("✅ Presentation formatting: PASSED")


def test_peer_input_validation():
    """Test peer ranker input validation."""
    print("\n" + "=" * 70)
    print("TEST: Peer Ranker Input Validation")
    print("=" * 70)

    peer_1 = create_peer_ranker_agent(ranker_id=1)

    # Test missing presentations
    state = create_phase1_state(countries=["USA", "IND"])
    # No expert_presentations provided

    result = peer_1(state)

    print("Test: Missing presentations")
    print(f"   Success: {result['ranking_metadata'].get('peer_1', {}).get('success', True) == False}")
    print(f"   Error: {result['ranking_metadata'].get('peer_1', {}).get('error', 'None')[:50]}")

    assert result['ranking_metadata']['peer_1']['success'] == False
    assert "No expert presentations" in result['ranking_metadata']['peer_1']['error']

    print("\n✅ Peer ranker input validation: PASSED")


def test_peer_with_real_llm():
    """Test peer ranker with real LLM call."""
    if SKIP_LLM_TESTS:
        print("\n⏭️  Skipping LLM test (no API key)")
        return

    print("\n" + "=" * 70)
    print("TEST: Peer Ranker with Real LLM")
    print("=" * 70)
    print("⚠️  This test will call OpenAI API and may take 15-30 seconds")

    # Create state with mock presentations
    state = create_phase1_state(countries=["USA", "IND", "CHN"])
    state["expert_presentations"] = {
        "USA": {
            "country_code": "USA",
            "executive_summary": "USA offers exceptional renewable energy investment opportunities with strong policy support, technological leadership, and massive market scale.",
            "strengths": [
                "30% ITC for solar and $27.5/MWh PTC for wind under IRA",
                "$100+ billion annual renewable investment with 290+ GW installed capacity",
                "World-class solar (6-7 kWh/m²/day) and wind (8-9 m/s) resources"
            ],
            "opportunities": [
                "State RPS mandates in 30+ states driving expansion",
                "Technological diversification and grid modernization"
            ],
            "risks": [
                "Potential policy changes with political shifts",
                "Grid integration and transmission challenges"
            ],
            "investment_case": "The United States represents the premier destination for renewable energy investment...",
            "recommendation": "STRONG_BUY",
            "confidence": "high",
            "key_metrics_summary": "IRR: 12-15%, LCOE: $35-45/MWh"
        },
        "IND": {
            "country_code": "IND",
            "executive_summary": "India presents compelling growth opportunities with ambitious 500 GW renewable target by 2030 and strong manufacturing incentives.",
            "strengths": [
                "500 GW renewable target with PLI manufacturing scheme",
                "Rapidly growing demand in emerging economy",
                "Gujarat and Rajasthan offer excellent solar resources"
            ],
            "opportunities": [
                "Green hydrogen production potential",
                "Export hub for renewable equipment"
            ],
            "risks": [
                "Financing challenges and currency volatility",
                "Land acquisition and grid infrastructure gaps"
            ],
            "investment_case": "India's renewable sector offers high growth potential with government backing...",
            "recommendation": "BUY",
            "confidence": "medium",
            "key_metrics_summary": "IRR: 10-14%, LCOE: $30-40/MWh"
        },
        "CHN": {
            "country_code": "CHN",
            "executive_summary": "China dominates global renewable manufacturing and deployment with massive scale and government support.",
            "strengths": [
                "World's largest renewable market with 400+ GW solar capacity",
                "Manufacturing dominance in solar panels and wind turbines",
                "Strong government policy support and subsidies"
            ],
            "opportunities": [
                "Offshore wind expansion in coastal regions",
                "Grid storage development at scale"
            ],
            "risks": [
                "Regulatory uncertainty and policy changes",
                "Market access barriers for foreign investors",
                "Geopolitical tensions affecting supply chains"
            ],
            "investment_case": "China's scale and manufacturing prowess create unique opportunities...",
            "recommendation": "HOLD",
            "confidence": "medium",
            "key_metrics_summary": "IRR: 8-12%, LCOE: $25-35/MWh"
        }
    }

    # Create and run peer ranker
    peer_1 = create_peer_ranker_agent(ranker_id=1)

    print("🤖 Calling GPT-4 to generate rankings...")
    result = peer_1(state)

    print("\n" + "=" * 70)
    print("RANKING RESULTS")
    print("=" * 70)

    if result['ranking_metadata']['peer_1']['success']:
        ranking = result['peer_rankings'][0]

        print(f"\n✅ Peer #1 ranking generated successfully")
        print(f"\nPeer ID: {ranking['peer_id']}")
        print(f"Methodology: {ranking['methodology']}")
        print(f"\nTop Choice Justification:")
        print(f"{ranking['top_choice_justification']}")

        print(f"\nComplete Rankings:")
        for r in ranking['rankings']:
            print(f"\n  {r['rank']}. {r['country_code']} - Score: {r['score']}/10")
            print(f"     Reasoning: {r['reasoning']}")
            print(f"     Strengths: {', '.join(r['strengths_noted'])}")
            print(f"     Concerns: {', '.join(r['concerns_noted'])}")

        print(f"\nGeneration time: {result['ranking_metadata']['peer_1']['generation_time_seconds']}s")

        # Validate structure
        assert len(ranking['rankings']) == 3
        assert ranking['rankings'][0]['rank'] == 1
        assert ranking['rankings'][1]['rank'] == 2
        assert ranking['rankings'][2]['rank'] == 3

        # Verify all countries ranked
        ranked_countries = [r['country_code'] for r in ranking['rankings']]
        assert set(ranked_countries) == {"USA", "IND", "CHN"}

        print("\n✅ Peer ranker with real LLM: PASSED")
    else:
        print(f"❌ Ranking failed: {result['ranking_metadata']['peer_1']['error']}")
        raise AssertionError("LLM ranking generation failed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL PEER RANKING AGENT TESTS")
    print("=" * 70)

    tests = [
        test_peer_ranker_creation,
        test_peer_registration,
        test_ranking_structure,
        test_presentation_formatting,
        test_peer_input_validation,
        test_peer_with_real_llm
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_func in tests:
        try:
            test_func()
            if SKIP_LLM_TESTS and test_func.__name__ == "test_peer_with_real_llm":
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