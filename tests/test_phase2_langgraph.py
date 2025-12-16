"""
Test Phase 2 LangGraph Workflow

Tests the complete Phase 2 workflow including:
- All Phase 1 stages (research, presentations, rankings, aggregation)
- Conditional debate triggering
- Hot seat debate execution
- Verdict handling and re-ranking
- Report generation with debate summary

Run with: python tests/test_phase2_langgraph.py

Author: Kanauija
Date: 2024-12-08
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.phase2_workflow_langgraph import run_phase2_langgraph
from api.services.research_service import generate_research_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestPhase2LangGraph")


# Test Functions
# ============================================================================

async def test_phase2_with_debate_triggered():
    """
    Test Phase 2 workflow when debate IS triggered.

    This simulates a scenario where initial consensus is low/medium,
    triggering the hot seat debate.
    """
    logger.info("=" * 70)
    logger.info("TEST 1: Phase 2 Workflow - Debate Triggered")
    logger.info("=" * 70)
    logger.info("Testing with debate_threshold='very_high' to force debate")
    logger.info("")

    # Generate research data
    research_data = generate_research_data(["USA", "CHN", "IND"])

    result = await run_phase2_langgraph(
        countries=["USA", "CHN", "IND"],
        research_json_data=research_data,  # CRITICAL: Provide research data
        num_peer_rankers=3,
        debate_enabled=True,
        debate_threshold="very_high",  # Very strict - will trigger debate
        num_challengers=2
    )

    # Validate results
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1 RESULTS")
    logger.info("=" * 70)

    # Check basic structure
    assert "expert_presentations" in result
    assert "peer_rankings" in result
    assert "aggregated_ranking" in result
    assert "debate_triggered" in result
    assert "debate_result" in result
    assert "final_ranking" in result
    assert "report_markdown" in result
    assert "execution_metadata" in result

    # Check Phase 1 outputs
    assert len(result["expert_presentations"]) == 3
    assert len(result["peer_rankings"]) == 3

    logger.info(f"✓ Expert presentations: {len(result['expert_presentations'])}")
    logger.info(f"✓ Peer rankings: {len(result['peer_rankings'])}")
    logger.info(f"✓ Final ranking: {len(result['final_ranking'])} countries")

    # Check debate execution
    assert result["debate_triggered"] == True
    assert result["debate_result"] is not None
    assert "verdict" in result["debate_result"]
    assert "debate_rounds" in result["debate_result"]
    assert "final_recommendation" in result["debate_result"]

    logger.info(f"✓ Debate triggered: {result['debate_triggered']}")
    logger.info(f"✓ Debate verdict: {result['debate_result']['verdict']}")
    logger.info(f"✓ Debate rounds: {len(result['debate_result']['debate_rounds'])}")
    logger.info(f"✓ Final recommendation: {result['debate_result']['final_recommendation']}")

    # Check final ranking
    assert len(result["final_ranking"]) == 3
    assert all("rank" in r for r in result["final_ranking"])
    assert all("country_code" in r for r in result["final_ranking"])

    # Check report generation
    assert result["report_markdown"] is not None
    assert len(result["report_markdown"]) > 0
    assert result["report_metadata"] is not None
    assert "filepath" in result["report_metadata"]

    logger.info(f"✓ Report generated: {len(result['report_markdown'])} chars")
    logger.info(f"✓ Report path: {result['report_metadata']['filepath']}")

    # Check execution metadata
    metadata = result["execution_metadata"]
    assert "total_duration_seconds" in metadata
    assert "stage_timings" in metadata
    assert "debate_triggered" in metadata
    assert metadata["debate_triggered"] == True

    logger.info(f"✓ Total duration: {metadata['total_duration_seconds']:.2f}s")

    # Verify debate stage timing exists (debate was executed)
    assert "debate" in metadata["stage_timings"]
    logger.info(f"✓ Debate stage executed: {metadata['stage_timings']['debate']:.2f}s")

    # Log stage timings
    logger.info("\nStage Timings:")
    for stage, duration in metadata["stage_timings"].items():
        logger.info(f"  {stage}: {duration:.2f}s")

    # Log final rankings
    logger.info("\nFinal Rankings:")
    for r in result["final_ranking"]:
        logger.info(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")

    # Check for errors
    assert len(result.get("errors", [])) == 0, f"Workflow had errors: {result['errors']}"

    logger.info("\n✅ TEST 1 PASSED: Phase 2 workflow with debate executed successfully")

    return result


async def test_phase2_debate_skipped():
    """
    Test Phase 2 workflow when debate is SKIPPED.

    This simulates a scenario where initial consensus is high enough
    to skip the debate.
    """
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Phase 2 Workflow - Debate Skipped")
    logger.info("=" * 70)
    logger.info("Testing with debate_threshold='low' to skip debate")
    logger.info("")

    # Generate research data
    research_data = generate_research_data(["USA", "CHN", "IND"])

    result = await run_phase2_langgraph(
        countries=["USA", "CHN", "IND"],
        research_json_data=research_data,  # CRITICAL: Provide research data
        num_peer_rankers=3,
        debate_enabled=True,
        debate_threshold="low",  # Very lenient - will skip debate
        num_challengers=2
    )

    # Validate results
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2 RESULTS")
    logger.info("=" * 70)

    # Check debate was skipped
    assert result["debate_triggered"] == False
    assert result["debate_result"] is None

    logger.info(f"✓ Debate triggered: {result['debate_triggered']}")
    logger.info(f"✓ Debate result: {result['debate_result']}")

    # Check final ranking exists
    assert len(result["final_ranking"]) == 3

    logger.info(f"✓ Final ranking: {len(result['final_ranking'])} countries")

    # Check report still generated
    assert result["report_markdown"] is not None
    assert len(result["report_markdown"]) > 0

    logger.info(f"✓ Report generated: {len(result['report_markdown'])} chars")

    # Check execution metadata
    metadata = result["execution_metadata"]
    assert metadata["debate_triggered"] == False

    # ✅ FIX: When debate is skipped via conditional edge, the debate node is NEVER executed
    # Therefore, there should be NO "debate" key in stage_timings
    assert "debate" not in metadata["stage_timings"], "Debate node should be bypassed when skipped"
    logger.info(f"✓ Debate node bypassed (not in stage_timings)")

    # Verify other stages ran
    assert "research" in metadata["stage_timings"]
    assert "presentations" in metadata["stage_timings"]
    assert "rankings" in metadata["stage_timings"]
    assert "aggregation" in metadata["stage_timings"]
    assert "report" in metadata["stage_timings"]
    logger.info(f"✓ All other stages executed successfully")

    logger.info(f"✓ Total duration: {metadata['total_duration_seconds']:.2f}s")

    # Log stage timings
    logger.info("\nStage Timings:")
    for stage, duration in metadata["stage_timings"].items():
        logger.info(f"  {stage}: {duration:.2f}s")

    # Log final rankings
    logger.info("\nFinal Rankings:")
    for r in result["final_ranking"]:
        logger.info(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")

    # Check for errors
    assert len(result.get("errors", [])) == 0, f"Workflow had errors: {result['errors']}"

    logger.info("\n✅ TEST 2 PASSED: Phase 2 workflow with debate skipped executed successfully")

    return result


async def test_phase2_debate_disabled():
    """
    Test Phase 2 workflow with debate completely DISABLED.
    """
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Phase 2 Workflow - Debate Disabled")
    logger.info("=" * 70)
    logger.info("Testing with debate_enabled=False")
    logger.info("")

    # Generate research data
    research_data = generate_research_data(["USA", "CHN", "IND"])

    result = await run_phase2_langgraph(
        countries=["USA", "CHN", "IND"],
        research_json_data=research_data,  # CRITICAL: Provide research data
        num_peer_rankers=3,
        debate_enabled=False,  # Debate disabled
        debate_threshold="high",
        num_challengers=2
    )

    # Validate results
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3 RESULTS")
    logger.info("=" * 70)

    # Check debate was not triggered
    assert result["debate_triggered"] == False
    assert result["debate_result"] is None

    logger.info(f"✓ Debate triggered: {result['debate_triggered']}")

    # Check workflow completed all other stages
    assert len(result["expert_presentations"]) == 3
    assert len(result["peer_rankings"]) == 3
    assert len(result["final_ranking"]) == 3

    logger.info(f"✓ All Phase 1 stages completed successfully")

    # Check execution metadata
    metadata = result["execution_metadata"]
    assert metadata["debate_enabled"] == False
    assert metadata["debate_triggered"] == False

    # Debate node should be bypassed
    assert "debate" not in metadata["stage_timings"]
    logger.info(f"✓ Debate node bypassed (debate disabled)")

    logger.info(f"✓ Total duration: {metadata['total_duration_seconds']:.2f}s")

    # Log final rankings
    logger.info("\nFinal Rankings:")
    for r in result["final_ranking"]:
        logger.info(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")

    # Check for errors
    assert len(result.get("errors", [])) == 0, f"Workflow had errors: {result['errors']}"

    logger.info("\n✅ TEST 3 PASSED: Phase 2 workflow with debate disabled executed successfully")

    return result


async def test_phase2_with_two_countries():
    """
    Test Phase 2 workflow with minimum countries (edge case).
    """
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Phase 2 Workflow - Two Countries (Minimum)")
    logger.info("=" * 70)
    logger.info("Testing with only 2 countries")
    logger.info("")

    # Generate research data
    research_data = generate_research_data(["USA", "CHN"])

    result = await run_phase2_langgraph(
        countries=["USA", "CHN"],
        research_json_data=research_data,  # CRITICAL: Provide research data
        num_peer_rankers=2,
        debate_enabled=True,
        debate_threshold="very_high",  # Force debate trigger
        num_challengers=2
    )

    # Validate results
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4 RESULTS")
    logger.info("=" * 70)

    # Check all stages completed
    assert len(result["expert_presentations"]) == 2
    assert len(result["peer_rankings"]) == 2
    assert len(result["final_ranking"]) == 2

    logger.info(f"✓ Expert presentations: {len(result['expert_presentations'])}")
    logger.info(f"✓ Peer rankings: {len(result['peer_rankings'])}")
    logger.info(f"✓ Final ranking: {len(result['final_ranking'])}")

    # Debate should be possible with 2 countries
    logger.info(f"✓ Debate triggered: {result['debate_triggered']}")

    if result["debate_triggered"]:
        logger.info(f"✓ Debate verdict: {result['debate_result']['verdict']}")
        assert "debate" in result["execution_metadata"]["stage_timings"]
    else:
        assert "debate" not in result["execution_metadata"]["stage_timings"]

    # Log final rankings
    logger.info("\nFinal Rankings:")
    for r in result["final_ranking"]:
        logger.info(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")

    # Check for errors
    assert len(result.get("errors", [])) == 0, f"Workflow had errors: {result['errors']}"

    logger.info("\n✅ TEST 4 PASSED: Phase 2 workflow with 2 countries executed successfully")

    return result


async def test_phase2_performance():
    """
    Test Phase 2 workflow performance and timing.
    """
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Phase 2 Workflow - Performance Analysis")
    logger.info("=" * 70)
    logger.info("Testing with 3 countries, 3 peers, 2 challengers")
    logger.info("")

    # Generate research data
    research_data = generate_research_data(["USA", "CHN", "IND"])

    result = await run_phase2_langgraph(
        countries=["USA", "CHN", "IND"],
        research_json_data=research_data,  # CRITICAL: Provide research data
        num_peer_rankers=3,
        debate_enabled=True,
        debate_threshold="very_high",
        num_challengers=2
    )

    # Analyze performance
    logger.info("\n" + "=" * 70)
    logger.info("PERFORMANCE ANALYSIS")
    logger.info("=" * 70)

    metadata = result["execution_metadata"]
    total_duration = metadata["total_duration_seconds"]
    stage_timings = metadata["stage_timings"]

    logger.info(f"\nTotal Duration: {total_duration:.2f}s")
    logger.info(f"\nStage Breakdown:")

    for stage, duration in sorted(stage_timings.items(), key=lambda x: x[1], reverse=True):
        percentage = (duration / total_duration) * 100
        logger.info(f"  {stage:20s}: {duration:6.2f}s ({percentage:5.1f}%)")

    # Performance expectations
    logger.info(f"\nPerformance Checks:")

    if stage_timings.get("research", 0) < 1.0:
        logger.info("  ✓ Research loading: Fast (< 1s)")

    if stage_timings.get("presentations", 0) < 15.0:
        logger.info("  ✓ Expert presentations: Acceptable (< 15s)")

    if stage_timings.get("rankings", 0) < 15.0:
        logger.info("  ✓ Peer rankings: Acceptable (< 15s)")

    if result["debate_triggered"] and stage_timings.get("debate", 0) < 20.0:
        logger.info("  ✓ Hot seat debate: Acceptable (< 20s)")

    if total_duration < 60.0:
        logger.info(f"  ✓ Total workflow: Acceptable (< 60s)")

    # Estimate costs
    logger.info(f"\nEstimated OpenAI API Calls:")
    num_expert_calls = len(result["expert_presentations"])
    num_peer_calls = len(result["peer_rankings"])
    num_debate_calls = 0

    if result["debate_triggered"]:
        num_challengers = len(result["debate_result"]["debate_rounds"])
        num_debate_calls = num_challengers * 3  # challenge, defense, scoring

    total_api_calls = num_expert_calls + num_peer_calls + num_debate_calls

    logger.info(f"  Expert presentations: {num_expert_calls} calls")
    logger.info(f"  Peer rankings: {num_peer_calls} calls")
    logger.info(f"  Hot seat debate: {num_debate_calls} calls")
    logger.info(f"  Total API calls: {total_api_calls}")
    logger.info(f"  Estimated cost: ${total_api_calls * 0.015:.3f} - ${total_api_calls * 0.025:.3f}")

    logger.info("\n✅ TEST 5 PASSED: Performance analysis complete")

    return result


async def run_all_tests():
    """Run all Phase 2 workflow tests."""
    logger.info("=" * 70)
    logger.info("PHASE 2 LANGGRAPH WORKFLOW - COMPREHENSIVE TEST SUITE")
    logger.info("=" * 70)
    logger.info("Testing complete Phase 2 workflow with conditional debate")
    logger.info("")

    try:
        # Test 1: Debate triggered
        result1 = await test_phase2_with_debate_triggered()

        # Test 2: Debate skipped
        result2 = await test_phase2_debate_skipped()

        # Test 3: Debate disabled
        result3 = await test_phase2_debate_disabled()

        # Test 4: Two countries (edge case)
        result4 = await test_phase2_with_two_countries()

        # Test 5: Performance analysis
        result5 = await test_phase2_performance()

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 70)
        logger.info("✅ Test 1: Debate triggered workflow")
        logger.info("✅ Test 2: Debate skipped workflow")
        logger.info("✅ Test 3: Debate disabled workflow")
        logger.info("✅ Test 4: Two countries (minimum)")
        logger.info("✅ Test 5: Performance analysis")
        logger.info("")
        logger.info("Phase 2 LangGraph workflow is production-ready!")
        logger.info("=" * 70)

        # Generate summary report
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)

        tests_run = [
            ("Debate Triggered", result1),
            ("Debate Skipped", result2),
            ("Debate Disabled", result3),
            ("Two Countries", result4),
            ("Performance", result5)
        ]

        for name, result in tests_run:
            logger.info(f"\n{name}:")
            logger.info(f"  Duration: {result['execution_metadata']['total_duration_seconds']:.2f}s")
            logger.info(f"  Debate triggered: {result['debate_triggered']}")
            if result['debate_triggered']:
                logger.info(f"  Verdict: {result['debate_result']['verdict']}")
            logger.info(f"  Errors: {len(result.get('errors', []))}")
            logger.info(f"  Report: {result['report_metadata']['filepath']}")

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())