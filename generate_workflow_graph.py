"""
Generate Visual Graph of Country Comparison Workflow with Research
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

# Import agents to register them
import business_units.data_team.nasa_agent
import business_units.data_team.research_loader
import business_units.finance_team.financial_agents
import business_units.insights_team.gpt4_agents
import business_units.ranking_team.agents

from src.workflows.country_comparison_with_research import workflow_with_research

def generate_mermaid_graph():
    """Generate Mermaid diagram (text-based)."""
    print("=" * 70)
    print("WORKFLOW GRAPH - MERMAID FORMAT")
    print("=" * 70)
    print()
    
    try:
        graph = workflow_with_research.graph
        mermaid = graph.get_graph().draw_mermaid()
        
        print(mermaid)
        print()
        
        with open("workflow_graph.mmd", "w") as f:
            f.write(mermaid)
        
        print("✅ Mermaid diagram saved to: workflow_graph.mmd")
        print("   View at: https://mermaid.live/")
        print()
        
    except Exception as e:
        print(f"❌ Error generating Mermaid: {str(e)}")
        print()

def generate_ascii_graph():
    """Generate ASCII art representation."""
    print("=" * 70)
    print("WORKFLOW GRAPH - ASCII ART")
    print("=" * 70)
    print()
    
    ascii_graph = """
    START
      ↓
    1. Validate Input
      ↓
    2. Load Research Data ⭐
      ↓
    3. Load NASA Locations
      ↓
    4. Analyze Locations
      ↓
    5. Aggregate by Country
      ↓
    6. Rank Countries
      ↓
    7. Verify Ranking
      ↓
    8. Generate Insights ⭐
      ↓
    END
    """
    
    print(ascii_graph)
    
    with open("workflow_graph_ascii.txt", "w") as f:
        f.write(ascii_graph)
    
    print("✅ ASCII diagram saved to: workflow_graph_ascii.txt")
    print()

def main():
    """Generate all graph formats."""
    print("\n" + "=" * 70)
    print("WORKFLOW GRAPH GENERATOR")
    print("=" * 70)
    print()
    
    generate_ascii_graph()
    generate_mermaid_graph()
    
    print("=" * 70)
    print("✅ GRAPHS GENERATED!")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
