"""
Tests for Phase 1 LangGraph Workflow
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflows.phase1_workflow_langgraph import (
    run_phase1_langgraph_sync,
    visualize_phase1_graph
)


def test_langgraph_workflow():
    """Test full LangGraph workflow."""
    print("\n" + "=" * 70)
    print("TEST: Phase 1 LangGraph Workflow")
    print("=" * 70)
    print("⚠️  This test will take ~20-30 seconds")
    print("⚠️  Will make real API calls to OpenAI")

    # Prepare research data
    research_data = [
        {
            "country_name": "USA",
            "research": "The United States offers exceptional renewable energy opportunities..."
        },
        {
            "country_name": "India",
            "research": "India presents compelling growth opportunities..."
        },
        {
            "country_name": "China",
            "research": "China dominates global renewable manufacturing..."
        }
    ]

    # Run workflow
    result = run_phase1_langgraph_sync(
        countries=["USA", "IND", "CHN"],
        research_json_data=research_data,
        num_peer_rankers=3
    )

    # Verify results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"Duration: {result['execution_metadata']['total_duration_seconds']}s")
    print(f"Errors: {len(result['errors'])}")
    print(f"Rankings: {len(result['aggregated_ranking'].get('final_rankings', []))}")
    print(f"Report generated: {'report_markdown' in result and len(result['report_markdown']) > 0}")

    # Assertions
    assert len(result['errors']) == 0, f"Errors occurred: {result['errors']}"
    assert len(result['aggregated_ranking'].get('final_rankings', [])) == 3
    assert len(result['report_markdown']) > 1000

    print("\n✅ LangGraph workflow test: PASSED")


def test_graph_visualization():
    """Test graph visualization."""
    print("\n" + "=" * 70)
    print("TEST: Graph Visualization")
    print("=" * 70)

    mermaid = visualize_phase1_graph()

    assert mermaid is not None
    assert "research_loading" in mermaid
    assert "expert_presentations" in mermaid
    assert "peer_rankings" in mermaid

    print("\n✅ Graph visualization test: PASSED")


if __name__ == "__main__":
    test_graph_visualization()
    test_langgraph_workflow()
    print("\n🎉 ALL LANGGRAPH TESTS PASSED!")