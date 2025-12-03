"""Test LangGraph workflow."""

from src.workflows.country_comparison_graph import CountryComparisonWorkflow


def test_workflow_creation():
    """Test workflow can be created."""
    workflow = CountryComparisonWorkflow()
    
    assert workflow.graph is not None
    print("✅ Workflow creation works!")


def test_workflow_execution():
    """Test workflow can execute."""
    workflow = CountryComparisonWorkflow()
    
    # Run workflow
    result = workflow.run(
        countries=["USA", "DEU", "IND"],
        query="Compare renewable energy investments"
    )
    
    # Check results
    assert "country_reports" in result
    assert "ranking" in result
    assert "verification" in result
    assert len(result["country_reports"]) == 3
    
    print("✅ Workflow execution works!")
    print(f"\nCountries analyzed: {list(result['country_reports'].keys())}")
    print(f"Ranking iterations: {len(result.get('ranking_iterations', []))}")
    print(f"Verified: {result.get('verification', {}).get('verified', False)}")


if __name__ == "__main__":
    test_workflow_creation()
    test_workflow_execution()
    
    print("\n" + "="*70)
    print("ALL WORKFLOW TESTS PASSED! ✅")
    print("="*70)
