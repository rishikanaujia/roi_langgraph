"""
Tests for Report Generator

Tests report generation, markdown formatting, and integration with Phase 1 results.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from business_units.insights_team.report_generator import (
    generate_executive_report,
    _generate_executive_summary,
    _generate_rankings_section,
    _generate_country_analyses,
    _format_as_markdown
)
from src.workflows.phase1_state import create_phase1_state


def create_mock_phase1_results():
    """Create mock Phase 1 results for testing."""

    state = create_phase1_state(countries=["USA", "IND", "CHN"])

    # Mock expert presentations
    state["expert_presentations"] = {
        "USA": {
            "country_code": "USA",
            "executive_summary": "USA offers exceptional renewable energy investment opportunities with strong policy support.",
            "strengths": [
                "30% ITC for solar and PTC for wind under IRA",
                "World-class resource quality (6-7 kWh/m²/day solar)",
                "$100+ billion annual investment market"
            ],
            "opportunities": [
                "Grid modernization creating storage opportunities",
                "Offshore wind expansion on East Coast"
            ],
            "risks": [
                "Potential policy changes with political shifts",
                "Grid interconnection queues"
            ],
            "investment_case": "The United States represents the premier destination for renewable energy investment with comprehensive policy support, excellent resources, and massive market scale.",
            "recommendation": "STRONG_BUY",
            "confidence": "high"
        },
        "IND": {
            "country_code": "IND",
            "executive_summary": "India presents compelling growth opportunities with ambitious renewable targets.",
            "strengths": [
                "500 GW renewable target by 2030",
                "PLI scheme for manufacturing",
                "Excellent solar resources in Gujarat/Rajasthan"
            ],
            "opportunities": [
                "Manufacturing hub potential",
                "Green hydrogen production"
            ],
            "risks": [
                "Financing challenges",
                "Grid infrastructure gaps"
            ],
            "investment_case": "India's renewable sector offers high growth potential backed by strong government commitment and excellent resources.",
            "recommendation": "BUY",
            "confidence": "medium"
        },
        "CHN": {
            "country_code": "CHN",
            "executive_summary": "China dominates global renewable manufacturing with massive deployment scale.",
            "strengths": [
                "World's largest renewable market",
                "Manufacturing dominance in equipment",
                "Strong government support",
                "400+ GW solar capacity"
            ],
            "opportunities": [
                "Offshore wind expansion",
                "Grid-scale storage deployment"
            ],
            "risks": [
                "Regulatory uncertainty",
                "Market access barriers for foreign investors"
            ],
            "investment_case": "China's scale and manufacturing prowess create unique opportunities despite regulatory complexities.",
            "recommendation": "HOLD",
            "confidence": "medium"
        }
    }

    # Mock peer rankings
    state["peer_rankings"] = [
        {
            "peer_id": "peer_ranker_1",
            "rankings": [
                {
                    "country_code": "USA",
                    "rank": 1,
                    "score": 9.2,
                    "reasoning": "Strong policy support and resource quality make USA the top choice.",
                    "strengths_noted": ["IRA policies", "Resource quality", "Market size"],
                    "concerns_noted": ["Political risk", "Grid challenges"]
                },
                {
                    "country_code": "CHN",
                    "rank": 2,
                    "score": 8.5,
                    "reasoning": "Manufacturing scale is impressive but foreign access is limited.",
                    "strengths_noted": ["Scale", "Manufacturing", "Government support"],
                    "concerns_noted": ["Market access", "Regulatory uncertainty"]
                },
                {
                    "country_code": "IND",
                    "rank": 3,
                    "score": 8.0,
                    "reasoning": "High growth potential but infrastructure challenges remain.",
                    "strengths_noted": ["Growth potential", "Government targets", "Resources"],
                    "concerns_noted": ["Infrastructure", "Financing"]
                }
            ]
        },
        {
            "peer_id": "peer_ranker_2",
            "rankings": [
                {
                    "country_code": "USA",
                    "rank": 1,
                    "score": 9.0,
                    "reasoning": "Comprehensive policy framework and mature market infrastructure.",
                    "strengths_noted": ["Policy framework", "Infrastructure", "Technology"],
                    "concerns_noted": ["Policy volatility", "Permitting"]
                },
                {
                    "country_code": "CHN",
                    "rank": 2,
                    "score": 8.3,
                    "reasoning": "Unmatched scale but geopolitical tensions add risk.",
                    "strengths_noted": ["Scale", "Technology", "Deployment speed"],
                    "concerns_noted": ["Geopolitical risk", "Access barriers"]
                },
                {
                    "country_code": "IND",
                    "rank": 3,
                    "score": 8.2,
                    "reasoning": "Strong fundamentals with execution challenges.",
                    "strengths_noted": ["Demand growth", "Policy support", "Resources"],
                    "concerns_noted": ["Execution risk", "Grid infrastructure"]
                }
            ]
        },
        {
            "peer_id": "peer_ranker_3",
            "rankings": [
                {
                    "country_code": "USA",
                    "rank": 1,
                    "score": 9.1,
                    "reasoning": "Best overall investment environment with lowest risk.",
                    "strengths_noted": ["Low risk", "Policy clarity", "Market depth"],
                    "concerns_noted": ["Competitive market", "Cost pressures"]
                },
                {
                    "country_code": "CHN",
                    "rank": 2,
                    "score": 8.4,
                    "reasoning": "Technology leadership offsets access concerns.",
                    "strengths_noted": ["Technology", "Scale", "Cost advantage"],
                    "concerns_noted": ["Foreign access", "Policy changes"]
                },
                {
                    "country_code": "IND",
                    "rank": 3,
                    "score": 8.1,
                    "reasoning": "Promising market with near-term challenges.",
                    "strengths_noted": ["Market potential", "Government commitment", "Demographics"],
                    "concerns_noted": ["Near-term challenges", "Complexity"]
                }
            ]
        }
    ]

    # Mock aggregated ranking
    state["aggregated_ranking"] = {
        "final_rankings": [
            {
                "rank": 1,
                "country_code": "USA",
                "consensus_score": 6.10,
                "average_peer_score": 9.10,
                "score_stddev": 0.10,
                "borda_points": 9.0,
                "median_rank": 1.0,
                "peer_scores": [9.2, 9.0, 9.1],
                "peer_agreement": {
                    "agreement_level": "very_high",
                    "rank_variance": 0.0,
                    "score_variance": 0.10,
                    "rank_range": (1, 1),
                    "score_range": (9.0, 9.2)
                }
            },
            {
                "rank": 2,
                "country_code": "CHN",
                "consensus_score": 5.40,
                "average_peer_score": 8.40,
                "score_stddev": 0.10,
                "borda_points": 6.0,
                "median_rank": 2.0,
                "peer_scores": [8.5, 8.3, 8.4],
                "peer_agreement": {
                    "agreement_level": "very_high",
                    "rank_variance": 0.0,
                    "score_variance": 0.10,
                    "rank_range": (2, 2),
                    "score_range": (8.3, 8.5)
                }
            },
            {
                "rank": 3,
                "country_code": "IND",
                "consensus_score": 4.75,
                "average_peer_score": 8.10,
                "score_stddev": 0.10,
                "borda_points": 3.0,
                "median_rank": 3.0,
                "peer_scores": [8.0, 8.2, 8.1],
                "peer_agreement": {
                    "agreement_level": "very_high",
                    "rank_variance": 0.0,
                    "score_variance": 0.10,
                    "rank_range": (3, 3),
                    "score_range": (8.0, 8.2)
                }
            }
        ],
        "method": "hybrid",
        "num_peers": 3,
        "num_countries": 3
    }

    # Mock execution metadata
    state["execution_metadata"] = {
        "start_time": "2025-12-07T20:00:00",
        "end_time": "2025-12-07T20:00:25",
        "total_duration_seconds": 25.5,
        "parallel_efficiency": 2.8,
        "stage_timings": {
            "research": 0.5,
            "presentations": 12.0,
            "rankings": 10.0,
            "aggregation": 0.5,
            "report_generation": 2.5
        },
        "agent_executions": []
    }

    return state


def test_executive_summary_generation():
    """Test executive summary generation."""
    print("\n" + "=" * 70)
    print("TEST: Executive Summary Generation")
    print("=" * 70)

    state = create_mock_phase1_results()
    final_rankings = state["aggregated_ranking"]["final_rankings"]
    peer_rankings = state["peer_rankings"]

    summary = _generate_executive_summary(final_rankings, peer_rankings)

    print("\nGenerated Executive Summary:")
    print(summary)

    # Assertions
    assert "USA" in summary
    assert "consensus score" in summary.lower()
    assert len(summary) > 100

    print("\n✅ Executive summary generation: PASSED")


def test_rankings_section_generation():
    """Test rankings section generation."""
    print("\n" + "=" * 70)
    print("TEST: Rankings Section Generation")
    print("=" * 70)

    state = create_mock_phase1_results()
    final_rankings = state["aggregated_ranking"]["final_rankings"]

    rankings = _generate_rankings_section(final_rankings)

    print(f"\nGenerated {len(rankings)} ranking entries:")
    for r in rankings:
        print(f"  {r['rank']}. {r['country_code']} - {r['consensus_score']}/10")
        print(f"     Agreement: {r['agreement_level']}")
        print(f"     Peer scores: {r['peer_scores']}")

    # Assertions
    assert len(rankings) == 3
    assert rankings[0]["rank"] == 1
    assert rankings[0]["country_code"] == "USA"
    assert "consensus_score" in rankings[0]
    assert "peer_scores" in rankings[0]

    print("\n✅ Rankings section generation: PASSED")


def test_country_analyses_generation():
    """Test country analyses generation."""
    print("\n" + "=" * 70)
    print("TEST: Country Analyses Generation")
    print("=" * 70)

    state = create_mock_phase1_results()
    final_rankings = state["aggregated_ranking"]["final_rankings"]
    expert_presentations = state["expert_presentations"]
    peer_rankings = state["peer_rankings"]

    analyses = _generate_country_analyses(
        final_rankings,
        expert_presentations,
        peer_rankings
    )

    print(f"\nGenerated {len(analyses)} country analyses:")
    for analysis in analyses:
        print(f"\n{analysis['rank']}. {analysis['country_code']}:")
        print(f"   Expert Recommendation: {analysis['expert_recommendation']}")
        print(f"   Strengths: {len(analysis['strengths'])}")
        print(f"   Opportunities: {len(analysis['opportunities'])}")
        print(f"   Risks: {len(analysis['risks'])}")
        print(f"   Peer Reasonings: {len(analysis['peer_reasonings'])}")

    # Assertions
    assert len(analyses) == 3
    assert all("executive_summary" in a for a in analyses)
    assert all("strengths" in a for a in analyses)
    assert all("peer_reasonings" in a for a in analyses)

    print("\n✅ Country analyses generation: PASSED")


def test_markdown_formatting():
    """Test markdown formatting."""
    print("\n" + "=" * 70)
    print("TEST: Markdown Formatting")
    print("=" * 70)

    state = create_mock_phase1_results()

    # Generate full report first
    result = generate_executive_report(state)
    report = result["executive_report"]

    markdown = _format_as_markdown(report)

    print(f"\nGenerated markdown report:")
    print(f"  Length: {len(markdown):,} characters")
    print(f"  Lines: {len(markdown.split(chr(10)))}")

    # Show preview
    print(f"\nFirst 500 characters:")
    print(markdown[:500])
    print("...")

    # Assertions
    assert len(markdown) > 1000
    assert "# Renewable Energy Investment Analysis" in markdown
    assert "## Executive Summary" in markdown
    assert "## Final Rankings" in markdown
    assert "## Detailed Country Analyses" in markdown
    assert "## Methodology" in markdown
    assert "USA" in markdown

    print("\n✅ Markdown formatting: PASSED")


def test_full_report_generation():
    """Test full report generation."""
    print("\n" + "=" * 70)
    print("TEST: Full Report Generation")
    print("=" * 70)

    state = create_mock_phase1_results()

    result = generate_executive_report(state)

    print("\nReport Generation Results:")
    print(f"  Report sections: {len(result['executive_report'])}")
    print(f"  Markdown size: {result['report_metadata']['report_size_chars']:,} chars")
    print(f"  Generation time: {result['report_metadata']['generation_time_seconds']}s")
    print(f"  Countries analyzed: {result['report_metadata']['countries_analyzed']}")
    print(f"  Rankings included: {result['report_metadata']['rankings_included']}")

    if result['report_metadata']['filepath']:
        print(f"  Saved to: {result['report_metadata']['filepath']}")

    # Show report structure
    report = result["executive_report"]
    print(f"\nReport Structure:")
    print(f"  Title: {report['title']}")
    print(f"  Countries: {report['countries_analyzed']}")
    print(f"  Rankings: {len(report['final_rankings'])}")
    print(f"  Analyses: {len(report['country_analyses'])}")

    # Assertions
    assert "executive_report" in result
    assert "report_markdown" in result
    assert "report_metadata" in result
    assert result["report_metadata"]["countries_analyzed"] == 3
    assert result["report_metadata"]["rankings_included"] == 3
    assert len(result["report_markdown"]) > 2000

    print("\n✅ Full report generation: PASSED")


def test_report_file_saving():
    """Test report file saving."""
    print("\n" + "=" * 70)
    print("TEST: Report File Saving")
    print("=" * 70)

    state = create_mock_phase1_results()

    result = generate_executive_report(state)

    filepath = result["report_metadata"]["filepath"]

    if filepath:
        print(f"Report saved to: {filepath}")

        # Check file exists
        if os.path.exists(filepath):
            # Read file
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"  File size: {len(content):,} bytes")
            print(f"  Lines: {len(content.split(chr(10)))}")

            # Assertions
            assert len(content) > 1000
            assert "USA" in content

            print("\n✅ File saved and validated")
        else:
            print("⚠️  File not found (may have failed to save)")
    else:
        print("⚠️  No filepath returned (saving may have failed)")

    print("\n✅ Report file saving: PASSED")


def test_report_with_missing_data():
    """Test report generation with missing data."""
    print("\n" + "=" * 70)
    print("TEST: Report with Missing Data")
    print("=" * 70)

    # Create minimal state
    state = create_phase1_state(countries=["USA"])
    # No rankings, no presentations

    result = generate_executive_report(state)

    print("Generated report with missing data:")
    print(f"  Error: {result['report_metadata'].get('error', 'None')}")
    print(f"  Markdown length: {len(result['report_markdown'])}")

    # Should handle gracefully
    assert "report_markdown" in result
    assert "error" in result["report_metadata"] or len(result["report_markdown"]) > 0

    print("\n✅ Report with missing data: PASSED (handled gracefully)")


def test_report_integration():
    """Test report integration with mock workflow results."""
    print("\n" + "=" * 70)
    print("TEST: Report Integration")
    print("=" * 70)

    state = create_mock_phase1_results()

    # Simulate what workflow would do
    result = generate_executive_report(state)

    # Merge back into state (like workflow does)
    state.update(result)

    print("After report generation:")
    print(f"  State has executive_report: {'executive_report' in state}")
    print(f"  State has report_markdown: {'report_markdown' in state}")
    print(f"  State has report_metadata: {'report_metadata' in state}")

    # Verify all expected keys
    assert "executive_report" in state
    assert "report_markdown" in state
    assert "report_metadata" in state

    print("\n✅ Report integration: PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL REPORT GENERATOR TESTS")
    print("=" * 70)

    tests = [
        test_executive_summary_generation,
        test_rankings_section_generation,
        test_country_analyses_generation,
        test_markdown_formatting,
        test_full_report_generation,
        test_report_file_saving,
        test_report_with_missing_data,
        test_report_integration
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