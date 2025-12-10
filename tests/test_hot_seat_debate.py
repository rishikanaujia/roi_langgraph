"""
Test Hot Seat Debate Module

Tests the Phase 2 hot seat debate functionality including:
- Challenge generation
- Defense generation
- Debate scoring
- Verdict determination
- Conditional triggering logic

Run with: python tests/test_hot_seat_debate.py

Author: Kanauija
Date: 2024-12-08
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from business_units.ranking_team.hot_seat_debate import (
    HotSeatDebate,
    execute_hot_seat_debate,
    should_trigger_debate
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestHotSeatDebate")

# Sample Data
# ============================================================================

SAMPLE_EXPERT_PRESENTATIONS = [
    {
        "country": "USA",
        "expert_id": 1,
        "content": """
**Investment Recommendation: STRONG BUY**

The United States presents exceptional renewable energy opportunities driven by the Inflation Reduction Act (IRA) providing 30% Investment Tax Credits. Key strengths include:

**Strengths:**
1. **Policy Support**: IRA provides $369B in clean energy incentives
2. **Resource Quality**: Southwest solar averages 6-7 kWh/m²/day, offshore wind capacity factors exceed 40%
3. **Market Size**: $100B+ annual renewable energy market with strong growth trajectory
4. **Infrastructure**: Advanced grid systems and established supply chains
5. **Innovation**: Leading in energy storage and smart grid technologies

**Opportunities:**
- Utility-scale solar projects in Texas, California, Arizona
- Offshore wind development on East Coast (30+ GW pipeline)
- Battery storage systems (projected 30 GW by 2025)

**Risks:**
- Regulatory complexity varies by state
- Grid interconnection delays in some regions
- Supply chain dependencies

**Overall Assessment**: Strong policy support, excellent resource quality, and mature market infrastructure make the USA a top-tier renewable energy investment destination.
"""
    },
    {
        "country": "CHN",
        "expert_id": 2,
        "content": """
**Investment Recommendation: STRONG BUY**

China dominates global renewable energy with unmatched manufacturing capacity and aggressive deployment targets. Key strengths include:

**Strengths:**
1. **Manufacturing Dominance**: Produces 80% of global solar panels and 60% of wind turbines
2. **Deployment Scale**: 1,200+ GW renewable capacity installed (world's largest)
3. **Government Support**: 14th Five-Year Plan commits to 1,200 GW by 2030
4. **Supply Chain Integration**: Complete vertical integration from raw materials to installation
5. **Cost Leadership**: Lowest production costs globally for solar and wind equipment

**Opportunities:**
- Massive onshore wind expansion in Northern provinces
- Utility-scale solar in Gobi Desert and Western regions
- Offshore wind development (targeting 70 GW by 2025)
- Green hydrogen production infrastructure

**Risks:**
- Regulatory restrictions on foreign investment
- Grid curtailment issues in some regions
- Geopolitical considerations for international investors

**Overall Assessment**: China's scale, manufacturing prowess, and government commitment create unique opportunities, though regulatory navigation is essential.
"""
    },
    {
        "country": "IND",
        "expert_id": 3,
        "content": """
**Investment Recommendation: STRONG BUY**

India offers tremendous renewable energy growth potential with ambitious government targets and improving investment climate. Key strengths include:

**Strengths:**
1. **Ambitious Targets**: 500 GW renewable capacity by 2030 (currently ~170 GW)
2. **Resource Potential**: Excellent solar irradiation (5-7 kWh/m²/day) across most regions
3. **Policy Support**: Production-Linked Incentives (PLI) for solar manufacturing
4. **Growing Demand**: Electricity demand growing 6-7% annually
5. **Market Opening**: Increasing private sector participation and FDI allowances

**Opportunities:**
- Large-scale solar parks (50+ GW pipeline)
- Rooftop solar expansion (targeting 40 GW by 2026)
- Offshore wind development (30 GW potential)
- Green hydrogen initiatives

**Risks:**
- Grid infrastructure challenges in rural areas
- Land acquisition complexities
- Payment delays from some distribution companies
- Regulatory inconsistencies across states

**Overall Assessment**: India's massive growth trajectory and supportive policies create compelling opportunities, though investors must navigate infrastructure and regulatory challenges.
"""
    }
]

SAMPLE_PEER_RANKINGS = [
    {
        "peer_id": 1,
        "rankings": [
            {"rank": 1, "country": "USA", "score": 9.2, "reasoning": "Superior policy support and market maturity"},
            {"rank": 2, "country": "CHN", "score": 8.8, "reasoning": "Unmatched scale but regulatory concerns"},
            {"rank": 3, "country": "IND", "score": 8.0, "reasoning": "High growth potential with execution risks"}
        ]
    },
    {
        "peer_id": 2,
        "rankings": [
            {"rank": 1, "country": "USA", "score": 9.2, "reasoning": "Best risk-adjusted returns"},
            {"rank": 2, "country": "CHN", "score": 8.8, "reasoning": "Manufacturing leadership"},
            {"rank": 3, "country": "IND", "score": 8.5, "reasoning": "Emerging market with high upside"}
        ]
    },
    {
        "peer_id": 3,
        "rankings": [
            {"rank": 1, "country": "USA", "score": 9.0, "reasoning": "Stable regulatory environment"},
            {"rank": 2, "country": "CHN", "score": 8.5, "reasoning": "Scale advantages"},
            {"rank": 3, "country": "IND", "score": 8.0, "reasoning": "Long-term growth story"}
        ]
    }
]

SAMPLE_AGGREGATED_RANKING = [
    {
        "rank": 1,
        "country_code": "USA",
        "consensus_score": 6.1,
        "average_peer_score": 9.13,
        "agreement_level": "high",  # Not "very_high" - should trigger debate
        "peer_scores": [9.2, 9.2, 9.0],
        "expert_recommendation": "STRONG_BUY",
        "score_details": {
            "borda_points": 9,
            "score_stddev": 0.094,
            "median_rank": 1.0,
            "rank_variance": 0.0,
            "score_variance": 0.009
        }
    },
    {
        "rank": 2,
        "country_code": "CHN",
        "consensus_score": 5.42,
        "average_peer_score": 8.7,
        "agreement_level": "very_high",
        "peer_scores": [8.8, 8.8, 8.5],
        "expert_recommendation": "STRONG_BUY",
        "score_details": {
            "borda_points": 6,
            "score_stddev": 0.141,
            "median_rank": 2.0,
            "rank_variance": 0.0,
            "score_variance": 0.02
        }
    },
    {
        "rank": 3,
        "country_code": "IND",
        "consensus_score": 4.75,
        "average_peer_score": 8.17,
        "agreement_level": "very_high",
        "peer_scores": [8.0, 8.5, 8.0],
        "expert_recommendation": "STRONG_BUY",
        "score_details": {
            "borda_points": 3,
            "score_stddev": 0.236,
            "median_rank": 3.0,
            "rank_variance": 0.0,
            "score_variance": 0.056
        }
    }
]


# Test Functions
# ============================================================================

async def test_single_debate_round():
    """Test execution of a single debate round."""
    logger.info("=" * 70)
    logger.info("TEST 1: Single Debate Round")
    logger.info("=" * 70)

    debate_system = HotSeatDebate(model="gpt-4o", temperature=0.7)

    top_ranked = SAMPLE_AGGREGATED_RANKING[0]
    runner_up = SAMPLE_AGGREGATED_RANKING[1]

    result = await debate_system._execute_single_debate(
        challenger_id=1,
        top_ranked=top_ranked,
        runner_up=runner_up,
        expert_presentations=SAMPLE_EXPERT_PRESENTATIONS,
        peer_rankings=SAMPLE_PEER_RANKINGS
    )

    logger.info("\n" + "=" * 70)
    logger.info("DEBATE ROUND RESULTS")
    logger.info("=" * 70)
    logger.info(f"Challenger ID: {result['challenger_id']}")
    logger.info(f"Duration: {result['duration_seconds']}s")
    logger.info(f"\nChallenge Strength: {result['challenge'].get('strength_score', 'N/A')}/10")
    logger.info(f"Defense Strength: {result['defense'].get('defense_strength', 'N/A')}/10")
    logger.info(f"\nScores:")
    logger.info(f"  Challenger: {result['score']['challenger_score']}/10")
    logger.info(f"  Defender: {result['score']['defender_score']}/10")
    logger.info(f"  Winner: {result['score']['winner']}")
    logger.info(f"  Confidence: {result['score']['confidence']}")
    logger.info(f"\nReasoning: {result['score']['reasoning']}")

    # Validate structure
    assert 'challenger_id' in result
    assert 'challenge' in result
    assert 'defense' in result
    assert 'score' in result
    assert 'duration_seconds' in result

    assert 'main_argument' in result['challenge']
    assert 'supporting_points' in result['challenge']
    assert 'weaknesses_identified' in result['challenge']

    assert 'rebuttal' in result['defense']
    assert 'counter_arguments' in result['defense']
    assert 'reaffirmed_strengths' in result['defense']

    assert 'challenger_score' in result['score']
    assert 'defender_score' in result['score']
    assert 'winner' in result['score']
    assert result['score']['winner'] in ['CHALLENGER', 'DEFENDER']

    logger.info("\n✅ TEST 1 PASSED: Single debate round executed successfully")
    return result


async def test_full_debate():
    """Test full hot seat debate with multiple challengers."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Full Hot Seat Debate (2 Challengers)")
    logger.info("=" * 70)

    top_ranked = SAMPLE_AGGREGATED_RANKING[0]
    runner_up = SAMPLE_AGGREGATED_RANKING[1]

    result = await execute_hot_seat_debate(
        top_ranked_country=top_ranked,
        runner_up_country=runner_up,
        expert_presentations=SAMPLE_EXPERT_PRESENTATIONS,
        peer_rankings=SAMPLE_PEER_RANKINGS,
        num_challengers=2,
        model="gpt-4o"
    )

    logger.info("\n" + "=" * 70)
    logger.info("FULL DEBATE RESULTS")
    logger.info("=" * 70)
    logger.info(f"Number of Rounds: {len(result['debate_rounds'])}")
    logger.info(f"Verdict: {result['verdict']}")
    logger.info(f"Final Recommendation: {result['final_recommendation']}")
    logger.info(f"Confidence: {result['confidence_level']}")
    logger.info(f"\nScores:")
    logger.info(f"  Challenger Average: {result['challenger_scores']['challenger_avg']}/10")
    logger.info(f"  Defender Average: {result['challenger_scores']['defender_avg']}/10")
    logger.info(f"  Challenger Wins: {result['challenger_scores']['challenger_wins']}")
    logger.info(f"  Defender Wins: {result['challenger_scores']['defender_wins']}")
    logger.info(f"\nExecution Metadata:")
    logger.info(f"  Duration: {result['execution_metadata']['duration_seconds']}s")
    logger.info(f"  Model: {result['execution_metadata']['model']}")
    logger.info(f"  Timestamp: {result['execution_metadata']['timestamp']}")

    # Log individual round summaries
    logger.info("\n" + "-" * 70)
    logger.info("INDIVIDUAL ROUND SUMMARIES")
    logger.info("-" * 70)
    for i, round_result in enumerate(result['debate_rounds'], 1):
        logger.info(f"\nRound {i}:")
        logger.info(f"  Winner: {round_result['score']['winner']}")
        logger.info(
            f"  Scores: {round_result['score']['challenger_score']} vs {round_result['score']['defender_score']}")
        logger.info(f"  Duration: {round_result['duration_seconds']}s")

    # Validate structure
    assert 'debate_rounds' in result
    assert 'verdict' in result
    assert 'final_recommendation' in result
    assert 'challenger_scores' in result
    assert 'confidence_level' in result
    assert 'execution_metadata' in result

    assert len(result['debate_rounds']) == 2
    assert result['verdict'] in ['UPHELD', 'OVERTURNED']
    assert result['confidence_level'] in ['high', 'medium', 'low']

    logger.info("\n✅ TEST 2 PASSED: Full debate executed successfully")
    return result


def test_should_trigger_debate():
    """Test the debate triggering logic."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Debate Triggering Logic")
    logger.info("=" * 70)

    test_cases = [
        {
            "ranking": [
                {"country_code": "USA", "agreement_level": "very_high"},
                {"country_code": "CHN", "agreement_level": "high"}
            ],
            "threshold": "high",
            "expected": False,
            "description": "Very high agreement should skip debate with 'high' threshold"
        },
        {
            "ranking": [
                {"country_code": "USA", "agreement_level": "high"},
                {"country_code": "CHN", "agreement_level": "medium"}
            ],
            "threshold": "high",
            "expected": False,
            "description": "High agreement should skip debate with 'high' threshold"
        },
        {
            "ranking": [
                {"country_code": "USA", "agreement_level": "medium"},
                {"country_code": "CHN", "agreement_level": "low"}
            ],
            "threshold": "high",
            "expected": True,
            "description": "Medium agreement should trigger debate with 'high' threshold"
        },
        {
            "ranking": [
                {"country_code": "USA", "agreement_level": "low"},
                {"country_code": "CHN", "agreement_level": "medium"}
            ],
            "threshold": "high",
            "expected": True,
            "description": "Low agreement should trigger debate with 'high' threshold"
        },
        {
            "ranking": [
                {"country_code": "USA", "agreement_level": "medium"},
                {"country_code": "CHN", "agreement_level": "low"}
            ],
            "threshold": "medium",
            "expected": False,
            "description": "Medium agreement should skip debate with 'medium' threshold"
        },
        {
            "ranking": [
                {"country_code": "USA", "agreement_level": "low"},
                {"country_code": "CHN", "agreement_level": "medium"}
            ],
            "threshold": "medium",
            "expected": True,
            "description": "Low agreement should trigger debate with 'medium' threshold"
        },
        {
            "ranking": [],
            "threshold": "high",
            "expected": False,
            "description": "Empty ranking should not trigger debate"
        },
        {
            "ranking": [{"country_code": "USA", "agreement_level": "very_high"}],
            "threshold": "high",
            "expected": False,
            "description": "Single country should not trigger debate (need 2+ countries)"
        },
        {
            "ranking": [
                {"country_code": "USA", "agreement_level": "very_high"},
                {"country_code": "CHN", "agreement_level": "high"}
            ],
            "threshold": "very_high",
            "expected": False,
            "description": "Very high agreement should skip debate with 'very_high' threshold"
        },
        {
            "ranking": [
                {"country_code": "USA", "agreement_level": "high"},
                {"country_code": "CHN", "agreement_level": "medium"}
            ],
            "threshold": "very_high",
            "expected": True,
            "description": "High agreement should trigger debate with 'very_high' threshold"
        }
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        result = should_trigger_debate(
            test_case["ranking"],
            test_case["threshold"]
        )

        status = "✅ PASS" if result == test_case["expected"] else "❌ FAIL"

        logger.info(f"\nTest Case {i}: {status}")
        logger.info(f"  Description: {test_case['description']}")
        logger.info(f"  Expected: {test_case['expected']}, Got: {result}")

        if result == test_case["expected"]:
            passed += 1
        else:
            failed += 1

    logger.info("\n" + "=" * 70)
    logger.info(f"TRIGGERING LOGIC TEST RESULTS: {passed}/{len(test_cases)} passed")
    logger.info("=" * 70)

    assert failed == 0, f"{failed} test cases failed"

    logger.info("\n✅ TEST 3 PASSED: All triggering logic tests passed")


async def test_verdict_determination():
    """Test verdict determination with mock debate results."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Verdict Determination Logic")
    logger.info("=" * 70)

    debate_system = HotSeatDebate()

    # Test Case 1: Defender wins decisively
    logger.info("\nTest Case 1: Defender wins decisively")
    mock_results_1 = [
        {
            "challenger_id": 1,
            "score": {"challenger_score": 7.0, "defender_score": 8.5, "winner": "DEFENDER"}
        },
        {
            "challenger_id": 2,
            "score": {"challenger_score": 6.5, "defender_score": 8.8, "winner": "DEFENDER"}
        }
    ]

    verdict_1 = debate_system._determine_verdict(
        mock_results_1,
        SAMPLE_AGGREGATED_RANKING[0],
        SAMPLE_AGGREGATED_RANKING[1]
    )

    logger.info(f"  Verdict: {verdict_1['verdict']}")
    logger.info(f"  Recommendation: {verdict_1['recommendation']}")
    logger.info(f"  Confidence: {verdict_1['confidence']}")

    assert verdict_1['verdict'] == 'UPHELD'
    assert verdict_1['confidence'] == 'high'

    # Test Case 2: Challenger wins decisively
    logger.info("\nTest Case 2: Challenger wins decisively")
    mock_results_2 = [
        {
            "challenger_id": 1,
            "score": {"challenger_score": 8.5, "defender_score": 7.0, "winner": "CHALLENGER"}
        },
        {
            "challenger_id": 2,
            "score": {"challenger_score": 8.8, "defender_score": 6.5, "winner": "CHALLENGER"}
        }
    ]

    verdict_2 = debate_system._determine_verdict(
        mock_results_2,
        SAMPLE_AGGREGATED_RANKING[0],
        SAMPLE_AGGREGATED_RANKING[1]
    )

    logger.info(f"  Verdict: {verdict_2['verdict']}")
    logger.info(f"  Recommendation: {verdict_2['recommendation']}")
    logger.info(f"  Confidence: {verdict_2['confidence']}")

    assert verdict_2['verdict'] == 'OVERTURNED'
    assert verdict_2['confidence'] == 'high'

    # Test Case 3: Mixed results (1-1 split)
    logger.info("\nTest Case 3: Mixed results (1-1 split)")
    mock_results_3 = [
        {
            "challenger_id": 1,
            "score": {"challenger_score": 8.0, "defender_score": 7.5, "winner": "CHALLENGER"}
        },
        {
            "challenger_id": 2,
            "score": {"challenger_score": 7.5, "defender_score": 8.0, "winner": "DEFENDER"}
        }
    ]

    verdict_3 = debate_system._determine_verdict(
        mock_results_3,
        SAMPLE_AGGREGATED_RANKING[0],
        SAMPLE_AGGREGATED_RANKING[1]
    )

    logger.info(f"  Verdict: {verdict_3['verdict']}")
    logger.info(f"  Recommendation: {verdict_3['recommendation']}")
    logger.info(f"  Confidence: {verdict_3['confidence']}")

    # With 1-1 split, defender should win (tie goes to current ranking)
    assert verdict_3['verdict'] == 'UPHELD'

    logger.info("\n✅ TEST 4 PASSED: Verdict determination logic validated")


async def run_all_tests():
    """Run all hot seat debate tests."""
    logger.info("=" * 70)
    logger.info("HOT SEAT DEBATE - COMPREHENSIVE TEST SUITE")
    logger.info("=" * 70)
    logger.info("Testing Phase 2 debate functionality")
    logger.info("")

    try:
        # Test 1: Single debate round
        await test_single_debate_round()

        # Test 2: Full debate
        await test_full_debate()

        # Test 3: Triggering logic
        test_should_trigger_debate()

        # Test 4: Verdict determination
        await test_verdict_determination()

        logger.info("\n" + "=" * 70)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 70)
        logger.info("✅ Single debate round execution")
        logger.info("✅ Full multi-challenger debate")
        logger.info("✅ Debate triggering logic")
        logger.info("✅ Verdict determination")
        logger.info("")
        logger.info("The hot seat debate system is ready for integration!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())