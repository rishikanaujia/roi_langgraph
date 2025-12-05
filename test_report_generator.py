"""
Test Executive Report Generator
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

# Import all agents
import business_units.data_team.nasa_agent
import business_units.data_team.research_loader
import business_units.finance_team.financial_agents
import business_units.insights_team.gpt4_agents
import business_units.insights_team.report_generator  # NEW
import business_units.ranking_team.agents

from src.workflows.country_comparison_with_research import workflow_with_research
from src.registry.agent_registry import get_registry

def main():
    """Test report generation."""
    
    print("=" * 70)
    print("🧪 EXECUTIVE REPORT GENERATOR TEST")
    print("=" * 70)
    print()
    
    # Sample research data
    research_data = [
        {
            "country_name": "United States",
            "research": "IRA provides 30% ITC for solar and PTC for wind. Strong state-level support in California, Texas, and Iowa."
        },
        {
            "country_name": "India",
            "research": "500 GW renewable target by 2030. PLI scheme for manufacturing. Gujarat and Rajasthan lead solar development."
        },
        {
            "country_name": "Brazil",
            "research": "Strong wind resources in Northeast. Energy auctions drive development. 23% non-hydro renewable target."
        }
    ]
    
    print("🚀 Running workflow with 3 countries...")
    print("   Countries: USA, IND, BRA")
    print()
    
    # Run workflow
    result = workflow_with_research.run(
        countries=["USA", "IND", "BRA"],
        research_json_data=research_data
    )
    
    # Generate report using the agent directly
    print("\n" + "=" * 70)
    print("📊 GENERATING EXECUTIVE REPORT")
    print("=" * 70)
    print()
    
    registry = get_registry()
    report_result = registry.execute_agent(
        "insights_team_report_generator_v1",
        result
    )
    
    if report_result.success:
        report_metadata = report_result.outputs.get("report_metadata", {})
        
        print("✅ Report Generated Successfully!")
        print()
        print(f"📄 Filename: {report_metadata.get('filename', 'N/A')}")
        print(f"📊 Countries: {report_metadata.get('countries_analyzed', 0)}")
        print(f"🔍 Total Sources: {report_metadata.get('total_sources', 0)}")
        print(f"🌐 Web Searches: {report_metadata.get('web_searches_performed', 0)}")
        print()
        
        # Show preview of markdown report
        markdown = report_result.outputs.get("report_markdown", "")
        if markdown:
            lines = markdown.split('\n')
            preview_lines = lines[:50]  # First 50 lines
            
            print("=" * 70)
            print("📝 REPORT PREVIEW (First 50 lines)")
            print("=" * 70)
            print()
            print('\n'.join(preview_lines))
            print()
            print(f"... ({len(lines) - 50} more lines)")
            print()
        
        print("=" * 70)
        print("✅ TEST COMPLETE!")
        print("=" * 70)
        print()
        print("💡 Check the generated markdown file for the full report!")
        print()
    
    else:
        print(f"❌ Report generation failed: {report_result.error}")


if __name__ == "__main__":
    main()
