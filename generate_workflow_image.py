"""
Generate PNG Image of Workflow Graph
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

def generate_png_image():
    """Generate PNG image of the workflow graph."""
    print("=" * 70)
    print("GENERATING WORKFLOW GRAPH IMAGE")
    print("=" * 70)
    print()
    
    try:
        # Get the graph
        graph = workflow_with_research.graph
        
        # Generate PNG
        print("📊 Generating PNG image...")
        img_data = graph.get_graph().draw_mermaid_png()
        
        # Save to file
        output_path = "workflow_graph.png"
        with open(output_path, "wb") as f:
            f.write(img_data)
        
        print(f"✅ Graph image saved to: {output_path}")
        print()
        print("📂 File size:", len(img_data), "bytes")
        print()
        print("🖼️  Open the file to view your workflow graph!")
        print()
        
    except Exception as e:
        print(f"❌ Error generating image: {str(e)}")
        print()
        print("💡 This might be because mermaid-cli is not installed.")
        print("   The graph structure is still accessible via code.")
        print()

if __name__ == "__main__":
    generate_png_image()
