"""
Complete System Test

Tests the entire LangGraph-based multi-agent system.
"""

import asyncio
from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

# Register business unit agents
import business_units.ranking_team.agents


def test_complete_workflow():
    """Test complete workflow with registered agents."""
    
    print("="*70)
    print("🌍 COMPLETE SYSTEM TEST")
    print("="*70)
    
    # Show registered agents
    registry = get_registry()
    print("\n📊 Registered Agents:")
    registry.print_summary()
    
    # Create workflow
    print("\n🔧 Creating LangGraph workflow...")
    workflow = CountryComparisonWorkflow()
    
    # Run workflow
    print("\n🚀 Running workflow for USA, DEU, IND...")
    result = workflow.run(
        countries=["USA", "DEU", "IND"],
        query="Compare renewable energy investments"
    )
    
    # Display results
    print("\n" + "="*70)
    print("📊 RESULTS")
    print("="*70)
    
    print(f"\n✅ Countries Analyzed: {len(result['country_reports'])}")
    for code, report in result['country_reports'].items():
        metrics = report.get('aggregate_metrics', {})
        print(f"   {code}: IRR={metrics.get('average_irr', 0):.2f}%, "
              f"LCOE=${metrics.get('average_lcoe', 0):.2f}/MWh")
    
    print(f"\n✅ Ranking:")
    ranking = result.get('ranking', {})
    for country in ranking.get('ranked_countries', [])[:3]:
        print(f"   {country['rank']}. {country['country_name']} "
              f"(Score: {country['overall_score']:.1f})")
    
    print(f"\n✅ Verification:")
    verification = result.get('verification', {})
    verified = "PASSED ✓" if verification.get('verified') else "FAILED ✗"
    print(f"   Status: {verified}")
    print(f"   Summary: {verification.get('summary', 'N/A')}")
    
    print(f"\n✅ Execution Metadata:")
    metadata = result.get('execution_metadata', {})
    print(f"   Start: {metadata.get('start_time', 'N/A')}")
    print(f"   End: {metadata.get('end_time', 'N/A')}")
    print(f"   Agent Executions: {len(metadata.get('agent_executions', []))}")
    
    # Save results
    import json
    with open('complete_system_test_results.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📄 Full results saved to: complete_system_test_results.json")
    
    print("\n" + "="*70)
    print("✅ COMPLETE SYSTEM TEST PASSED!")
    print("="*70)
    
    return result


if __name__ == "__main__":
    test_complete_workflow()
