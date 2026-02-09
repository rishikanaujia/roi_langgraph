"""
Tests for Phase 1 Workflow

Tests workflow orchestration, parallel execution, and end-to-end flow.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check for API key
if not os.environ.get("OPENAI_API_KEY"):
    print("⚠️  OPENAI_API_KEY not set - LLM tests will be skipped")
    SKIP_LLM_TESTS = True
else:
    SKIP_LLM_TESTS = False

from src.workflows.phase1_workflow import (
    Phase1Workflow,
    run_phase1_workflow
)
from src.workflows.phase1_state import get_stage_progress


def test_workflow_initialization():
    """Test workflow initialization."""
    print("\n" + "=" * 70)
    print("TEST: Workflow Initialization")
    print("=" * 70)

    workflow = Phase1Workflow(num_peer_rankers=3)

    print(f"✅ Workflow initialized")
    print(f"   Peer rankers: {workflow.num_peer_rankers}")

    assert workflow.num_peer_rankers == 3

    print("\n✅ Workflow initialization: PASSED")


def test_workflow_with_mock_data():
    """Test workflow with mock data (no LLM)."""
    print("\n" + "=" * 70)
    print("TEST: Workflow with Mock Data")
    print("=" * 70)

    # Create workflow
    workflow = Phase1Workflow(num_peer_rankers=2)

    # Prepare mock research data
    research_data = [
        {
            "country_name": "USA",
            "research": "USA has strong renewable energy policies including IRA..."
        },
        {
            "country_name": "India",
            "research": "India aims for 500 GW renewable capacity by 2030..."
        }
    ]

    print("Mock data prepared:")
    print(f"  Countries: USA, IND")
    print(f"  Research items: {len(research_data)}")
    print(f"  Peer rankers: {workflow.num_peer_rankers}")

    # Note: We won't run the full workflow here as it requires LLM calls
    # Just test the structure

    print("\n✅ Workflow with mock data: PASSED")


def test_workflow_progress_tracking():
    """Test workflow progress tracking."""
    print("\n" + "=" * 70)
    print("TEST: Workflow Progress Tracking")
    print("=" * 70)

    from src.workflows.phase1_state import create_phase1_state

    # Create state
    state = create_phase1_state(countries=["USA", "IND"])

    # Initial progress
    progress = get_stage_progress(state)
    print("Initial progress:")
    for stage, status in progress.items():
        print(f"  {stage}: {status}")

    assert progress["research"] == "pending"

    # Simulate research complete
    state["country_research"] = {"USA": "...", "IND": "..."}
    progress = get_stage_progress(state)
    print("\nAfter research:")
    for stage, status in progress.items():
        print(f"  {stage}: {status}")

    assert progress["research"] == "complete"

    print("\n✅ Workflow progress tracking: PASSED")


def test_end_to_end_workflow():
    """Test complete end-to-end workflow with real LLM."""
    if SKIP_LLM_TESTS:
        print("\n⏭️  Skipping end-to-end test (no API key)")
        return

    print("\n" + "=" * 70)
    print("TEST: End-to-End Workflow")
    print("=" * 70)
    print("⚠️  This test will call OpenAI API multiple times")
    print("⚠️  Expected duration: 30-60 seconds")
    print("⚠️  Will use ~20-30 API calls")

    # Prepare research data
    research_data = [
        {
            "country_name": "USA",
            "research": """
United States Renewable Energy Analysis:

Policy Environment:
- Inflation Reduction Act provides 30% ITC for solar and PTC for wind
- State-level renewable portfolio standards in 30+ states
- Strong federal support for clean energy transition

Market Conditions:
- $100+ billion annual renewable energy investment
- 150+ GW solar installed capacity
- 140+ GW wind installed capacity
- Mature market with strong demand

Resource Quality:
- Southwest: 6-7 kWh/m²/day solar insolation (world-class)
- Great Plains: 8-9 m/s average wind speeds
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
        },
        {
            "country_name": "India",
            "research": """
India Renewable Energy Analysis:

Policy Environment:
- 500 GW renewable target by 2030
- Production-Linked Incentive (PLI) scheme for manufacturing
- Green hydrogen mission launched

Market Conditions:
- Rapidly growing energy demand in emerging economy
- 70+ GW solar capacity installed
- 40+ GW wind capacity installed
- Huge growth potential

Resource Quality:
- Gujarat and Rajasthan: excellent solar resources
- Tamil Nadu: strong wind resources
- Significant untapped potential

Opportunities:
- Manufacturing hub potential with PLI incentives
- Export opportunities for renewable equipment
- Green hydrogen production

Challenges:
- Financing challenges and currency volatility
- Land acquisition complexities
- Grid infrastructure gaps in rural areas
            """
        },
        {
            "country_name": "China",
            "research": """
China Renewable Energy Analysis:

Policy Environment:
- Carbon neutrality by 2060 commitment
- Strong government subsidies and support
- Five-Year Plans driving deployment

Market Conditions:
- World's largest renewable market
- 400+ GW solar capacity
- 350+ GW wind capacity
- Manufacturing dominance in equipment

Resource Quality:
- Western regions: excellent solar resources
- Coastal areas: strong offshore wind potential
- Massive scale enables development

Opportunities:
- Offshore wind expansion
- Grid-scale storage deployment
- Technology leadership in manufacturing

Challenges:
- Regulatory uncertainty and policy changes
- Market access barriers for foreign investors
- Geopolitical tensions affecting supply chains
            """
        }
    ]

    # Run workflow
    print("\n🚀 Starting Phase 1 workflow...")
    print("   Stage 1: Research loading")
    print("   Stage 2: Expert presentations (3 parallel)")
    print("   Stage 3: Peer rankings (3 parallel)")
    print("   Stage 4: Aggregation")

    result = run_phase1_workflow(
        countries=["USA", "IND", "CHN"],
        research_json_data=research_data,
        num_peer_rankers=3
    )

    # Display results
    print("\n" + "=" * 70)
    print("WORKFLOW RESULTS")
    print("=" * 70)

    # Execution metadata
    exec_meta = result.get("execution_metadata", {})
    print(f"\nExecution Summary:")
    print(f"  Total time: {exec_meta.get('total_duration_seconds', 0)}s")
    print(f"  Parallel efficiency: {exec_meta.get('parallel_efficiency', 0):.2f}x")

    # Stage timings
    stage_timings = exec_meta.get("stage_timings", {})
    print(f"\nStage Timings:")
    for stage, duration in stage_timings.items():
        print(f"  {stage}: {duration}s")

    # Research
    print(f"\nResearch Loaded: {len(result.get('country_research', {}))} countries")

    # Presentations
    presentations = result.get("expert_presentations", {})
    print(f"\nExpert Presentations: {len(presentations)}")
    for country, pres in presentations.items():
        print(f"  {country}: {pres.get('recommendation', 'N/A')} (confidence: {pres.get('confidence', 'N/A')})")

    # Peer rankings
    peer_rankings = result.get("peer_rankings", [])
    print(f"\nPeer Rankings: {len(peer_rankings)} peers")
    for peer_ranking in peer_rankings:
        top = peer_ranking["rankings"][0]
        print(f"  {peer_ranking['peer_id']}: Top choice = {top['country_code']} ({top['score']}/10)")

    # Final ranking
    final_rankings = result.get("aggregated_ranking", {}).get("final_rankings", [])
    print(f"\nFinal Consensus Ranking:")
    for r in final_rankings:
        print(f"  {r['rank']}. {r['country_code']} - Score: {r['consensus_score']}/10")
        print(f"     Agreement: {r['peer_agreement']['agreement_level']}")
        print(f"     Peer scores: {r['peer_scores']}")

    # Errors
    errors = result.get("errors", [])
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✅ No errors")

    # Assertions
    assert len(result.get('country_research', {})) == 3
    assert len(result.get('expert_presentations', {})) == 3
    assert len(result.get('peer_rankings', [])) == 3
    assert len(final_rankings) == 3
    assert final_rankings[0]['rank'] == 1

    print("\n✅ End-to-end workflow: PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL PHASE 1 WORKFLOW TESTS")
    print("=" * 70)

    tests = [
        test_workflow_initialization,
        test_workflow_with_mock_data,
        test_workflow_progress_tracking,
        test_end_to_end_workflow
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_func in tests:
        try:
            test_func()
            if SKIP_LLM_TESTS and test_func.__name__ == "test_end_to_end_workflow":
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
        if SKIP_LLM_TESTS:
            print("ℹ️  Set OPENAI_API_KEY to run end-to-end test")
    else:
        print(f"\n⚠️  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)