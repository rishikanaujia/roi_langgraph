"""
Tests for Ranking Aggregation Logic

Tests aggregation methods, consensus calculation, and agreement analysis.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from business_units.ranking_team.aggregation_logic import (
    calculate_borda_count,
    calculate_average_scores,
    calculate_median_ranks,
    calculate_peer_agreement,
    aggregate_peer_rankings,
    ranking_aggregator
)
from src.workflows.phase1_state import create_phase1_state


def create_mock_peer_rankings():
    """Create mock peer rankings for testing."""
    return [
        # Peer 1
        {
            "peer_id": "peer_ranker_1",
            "rankings": [
                {"country_code": "USA", "rank": 1, "score": 9.5, "reasoning": "Top choice"},
                {"country_code": "IND", "rank": 2, "score": 8.0, "reasoning": "Strong growth"},
                {"country_code": "CHN", "rank": 3, "score": 7.5, "reasoning": "Scale leader"}
            ]
        },
        # Peer 2
        {
            "peer_id": "peer_ranker_2",
            "rankings": [
                {"country_code": "USA", "rank": 1, "score": 9.2, "reasoning": "Policy strength"},
                {"country_code": "CHN", "rank": 2, "score": 8.0, "reasoning": "Manufacturing"},
                {"country_code": "IND", "rank": 3, "score": 7.8, "reasoning": "Growing market"}
            ]
        },
        # Peer 3
        {
            "peer_id": "peer_ranker_3",
            "rankings": [
                {"country_code": "USA", "rank": 1, "score": 9.0, "reasoning": "Best overall"},
                {"country_code": "IND", "rank": 2, "score": 8.2, "reasoning": "High potential"},
                {"country_code": "CHN", "rank": 3, "score": 7.2, "reasoning": "Geopolitical risk"}
            ]
        }
    ]


def test_borda_count():
    """Test Borda count calculation."""
    print("\n" + "=" * 70)
    print("TEST: Borda Count Calculation")
    print("=" * 70)

    peer_rankings = create_mock_peer_rankings()
    borda_scores = calculate_borda_count(peer_rankings)

    print("Borda scores:")
    for country, score in sorted(borda_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {country}: {score} points")

    # With 3 countries:
    # Rank 1 = 3 points, Rank 2 = 2 points, Rank 3 = 1 point
    # USA: 3+3+3 = 9 points (ranked #1 by all)
    # IND: 2+1+2 = 5 points
    # CHN: 1+2+1 = 4 points

    assert borda_scores["USA"] == 9
    assert borda_scores["IND"] == 5
    assert borda_scores["CHN"] == 4

    print("\n✅ Borda count calculation: PASSED")


def test_average_scores():
    """Test average score calculation."""
    print("\n" + "=" * 70)
    print("TEST: Average Score Calculation")
    print("=" * 70)

    peer_rankings = create_mock_peer_rankings()
    avg_scores = calculate_average_scores(peer_rankings)

    print("Average scores (with stddev):")
    for country, (avg, std) in sorted(avg_scores.items(), key=lambda x: x[1][0], reverse=True):
        print(f"  {country}: {avg:.2f} ± {std:.2f}")

    # USA: (9.5 + 9.2 + 9.0) / 3 = 9.23
    assert 9.2 <= avg_scores["USA"][0] <= 9.3

    # All peers agree on USA strongly (low stddev)
    assert avg_scores["USA"][1] < 0.3

    print("\n✅ Average score calculation: PASSED")


def test_median_ranks():
    """Test median rank calculation."""
    print("\n" + "=" * 70)
    print("TEST: Median Rank Calculation")
    print("=" * 70)

    peer_rankings = create_mock_peer_rankings()
    median_ranks = calculate_median_ranks(peer_rankings)

    print("Median ranks:")
    for country, rank in sorted(median_ranks.items(), key=lambda x: x[1]):
        print(f"  {country}: rank {rank}")

    # USA: [1, 1, 1] -> median = 1
    # IND: [2, 3, 2] -> median = 2
    # CHN: [3, 2, 3] -> median = 3

    assert median_ranks["USA"] == 1.0
    assert median_ranks["IND"] == 2.0
    assert median_ranks["CHN"] == 3.0

    print("\n✅ Median rank calculation: PASSED")


def test_peer_agreement():
    """Test peer agreement calculation."""
    print("\n" + "=" * 70)
    print("TEST: Peer Agreement Analysis")
    print("=" * 70)

    peer_rankings = create_mock_peer_rankings()

    # Check agreement for each country
    for country in ["USA", "IND", "CHN"]:
        agreement = calculate_peer_agreement(peer_rankings, country)

        print(f"\n{country}:")
        print(f"  Agreement level: {agreement['agreement_level']}")
        print(f"  Rank variance: {agreement['rank_variance']}")
        print(f"  Score variance: {agreement['score_variance']}")
        print(f"  Rank range: {agreement['rank_range']}")
        print(f"  Score range: {agreement['score_range']}")

    # USA should have very high agreement (all peers rank it #1)
    usa_agreement = calculate_peer_agreement(peer_rankings, "USA")
    assert usa_agreement["rank_variance"] == 0.0
    assert usa_agreement["agreement_level"] == "very_high"

    print("\n✅ Peer agreement analysis: PASSED")


def test_aggregate_rankings():
    """Test full aggregation."""
    print("\n" + "=" * 70)
    print("TEST: Full Ranking Aggregation")
    print("=" * 70)

    peer_rankings = create_mock_peer_rankings()
    result = aggregate_peer_rankings(peer_rankings, method="hybrid")

    print(f"\nAggregation method: {result['method']}")
    print(f"Number of peers: {result['num_peers']}")
    print(f"Number of countries: {result['num_countries']}")

    print("\nFinal Rankings:")
    for ranking in result['final_rankings']:
        print(f"\n  {ranking['rank']}. {ranking['country_code']}")
        print(f"     Consensus Score: {ranking['consensus_score']}/10")
        print(f"     Peer Scores: {ranking['peer_scores']}")
        print(f"     Agreement: {ranking['peer_agreement']['agreement_level']}")

    # Assertions
    assert len(result['final_rankings']) == 3
    assert result['final_rankings'][0]['country_code'] == "USA"
    assert result['final_rankings'][0]['rank'] == 1

    print("\n✅ Full ranking aggregation: PASSED")


def test_aggregation_agent():
    """Test aggregation agent."""
    print("\n" + "=" * 70)
    print("TEST: Aggregation Agent")
    print("=" * 70)

    # Create state
    state = create_phase1_state(countries=["USA", "IND", "CHN"])
    state["peer_rankings"] = create_mock_peer_rankings()

    # Run aggregator
    result = ranking_aggregator(state)

    print("\nAgent Results:")
    print(f"  Success: {result['aggregation_metadata']['success']}")
    print(f"  Top choice: {result['aggregation_metadata']['top_choice']}")
    print(f"  Average agreement: {result['aggregation_metadata']['average_agreement']}")
    print(f"  Time: {result['aggregation_metadata']['aggregation_time_seconds']}s")

    print("\nConsensus Scores:")
    for country, score in sorted(result['consensus_scores'].items(), key=lambda x: x[1], reverse=True):
        variance = result['score_variance'][country]
        print(f"  {country}: {score}/10 (±{variance})")

    # Assertions
    assert result['aggregation_metadata']['success'] == True
    assert result['aggregation_metadata']['top_choice'] == "USA"
    assert "USA" in result['consensus_scores']
    assert len(result['consensus_scores']) == 3

    print("\n✅ Aggregation agent: PASSED")


def test_tie_handling():
    """Test handling of tied scores."""
    print("\n" + "=" * 70)
    print("TEST: Tie Handling")
    print("=" * 70)

    # Create tie scenario
    tied_rankings = [
        {
            "peer_id": "peer_1",
            "rankings": [
                {"country_code": "USA", "rank": 1, "score": 9.0},
                {"country_code": "IND", "rank": 2, "score": 9.0}  # Same score
            ]
        },
        {
            "peer_id": "peer_2",
            "rankings": [
                {"country_code": "IND", "rank": 1, "score": 9.0},
                {"country_code": "USA", "rank": 2, "score": 9.0}  # Reversed
            ]
        }
    ]

    result = aggregate_peer_rankings(tied_rankings, method="borda")

    print("\nTied scenario results:")
    for ranking in result['final_rankings']:
        print(f"  {ranking['rank']}. {ranking['country_code']} - {ranking['consensus_score']}")

    # With Borda count, both should get same points
    # Both get rank 1 once (2 points) and rank 2 once (1 point) = 3 points each
    borda_usa = result['final_rankings'][0]['borda_points']
    borda_ind = result['final_rankings'][1]['borda_points']

    print(f"\nBorda points: USA={borda_usa}, IND={borda_ind}")

    assert borda_usa == borda_ind  # Should be tied

    print("\n✅ Tie handling: PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL AGGREGATION LOGIC TESTS")
    print("=" * 70)

    tests = [
        test_borda_count,
        test_average_scores,
        test_median_ranks,
        test_peer_agreement,
        test_aggregate_rankings,
        test_aggregation_agent,
        test_tie_handling
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