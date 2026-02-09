"""
Gradio UI for Renewable Energy Investment Ranking System

Beautiful web interface for running multi-agent analysis workflows.

Author: Kanauija
Date: 2024-12-08
"""

import asyncio
import gradio as gr
import os
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import pandas as pd
from pathlib import Path

# Import workflows
from src.workflows.phase1_workflow_langgraph import run_phase1_langgraph
from src.workflows.phase2_workflow_langgraph import run_phase2_langgraph

# Import services
from api.services.research_service import (
    generate_research_data,
    get_supported_countries,
    validate_countries
)

# Configure
SUPPORTED_COUNTRIES = get_supported_countries()


# ============================================================================
# Helper Functions
# ============================================================================

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def create_ranking_dataframe(rankings: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert rankings to pandas DataFrame for display."""
    if not rankings:
        return pd.DataFrame()

    data = []
    for r in rankings:
        row = {
            "Rank": f"#{r['rank']}" if r['rank'] <= 3 else str(r['rank']),
            "Country": r['country_code'],
            "Consensus Score": f"{r['consensus_score']:.2f}/10",
            "Avg Peer Score": f"{r.get('average_peer_score', 0):.2f}/10",
            "Agreement": r.get('agreement_level', 'unknown'),
            "Expert Rec": r.get('expert_recommendation', 'N/A')
        }

        # Add debate markers
        if r.get('debate_winner'):
            row['Rank'] = f"🏆 {row['Rank']}"
        elif r.get('debate_loser'):
            row['Rank'] = f"📉 {row['Rank']}"

        data.append(row)

    return pd.DataFrame(data)


def create_execution_summary(result: Dict[str, Any]) -> str:
    """Create execution summary markdown."""
    metadata = result.get('execution_metadata', {})

    total_duration = metadata.get('total_duration_seconds', 0)
    stage_timings = metadata.get('stage_timings', {})

    lines = ["## ⏱️ Execution Summary", ""]
    lines.append(f"**Total Duration:** {format_duration(total_duration)}")
    lines.append("")

    if stage_timings:
        lines.append("**Stage Breakdown:**")
        lines.append("")
        for stage, duration in sorted(stage_timings.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total_duration * 100) if total_duration > 0 else 0
            lines.append(f"- **{stage.capitalize()}**: {format_duration(duration)} ({percentage:.1f}%)")

    lines.append("")
    lines.append(f"**Countries Analyzed:** {metadata.get('num_countries', 0)}")
    lines.append(f"**Peer Rankers:** {metadata.get('num_peer_rankers', 0)}")

    if metadata.get('debate_triggered'):
        lines.append(f"**Debate Rounds:** {len(result.get('debate_result', {}).get('rounds', []))}")
        lines.append(f"**Verdict:** {result.get('debate_result', {}).get('verdict', 'Unknown')}")

    return "\n".join(lines)


def create_debate_summary(debate_result: Dict[str, Any]) -> str:
    """Create debate summary markdown."""
    if not debate_result:
        return "No debate data available."

    lines = ["## 🔥 Debate Summary", ""]

    verdict = debate_result.get('verdict', 'Unknown')
    recommendation = debate_result.get('recommendation', '')

    if verdict == "OVERTURNED":
        lines.append(f"**🔄 OVERTURNED** - {recommendation}")
    else:
        lines.append(f"**✅ UPHELD** - {recommendation}")

    lines.append("")

    statistics = debate_result.get('statistics', {})
    rounds = debate_result.get('rounds', [])

    total_rounds = statistics.get('total_rounds', len(rounds))
    challenger_wins = statistics.get('challenger_wins', 0)
    defender_wins = statistics.get('defender_wins', 0)

    lines.append(f"- **Total Rounds:** {total_rounds}")
    lines.append(f"- **Challenger Wins:** {challenger_wins}")
    lines.append(f"- **Defender Wins:** {defender_wins}")

    return "\n".join(lines)


# ============================================================================
# Workflow Execution Functions
# ============================================================================

async def run_phase1_async(
        countries: List[str],
        num_peer_rankers: int,
        progress=gr.Progress()
) -> tuple:
    """Run Phase 1 workflow with progress tracking."""

    progress(0, desc="Validating inputs...")

    # Validate countries
    valid_codes, invalid = validate_countries(countries)

    if invalid:
        error_msg = f"❌ Invalid countries: {', '.join(invalid)}"
        return error_msg, None, None, None

    if len(valid_codes) < 2:
        return "❌ Need at least 2 valid countries", None, None, None

    progress(0.1, desc="Generating research data...")

    try:
        # Generate research
        research_data = generate_research_data(valid_codes)

        progress(0.2, desc="Starting workflow...")

        # Run Phase 1
        result = await run_phase1_langgraph(
            countries=valid_codes,
            research_json_data=research_data,
            num_peer_rankers=num_peer_rankers
        )

        progress(1.0, desc="Complete!")

        # Format outputs
        rankings = result.get('final_ranking', [])

        # Create summary
        summary_lines = ["# 🎯 Analysis Complete!", ""]
        if rankings:
            winner = rankings[0]
            summary_lines.append(f"## Winner: **{winner['country_code']}**")
            summary_lines.append(f"**Score:** {winner['consensus_score']:.2f}/10")
            summary_lines.append(f"**Agreement:** {winner.get('agreement_level', 'unknown')}")

        summary = "\n".join(summary_lines)

        # Create rankings table
        df = create_ranking_dataframe(rankings)

        # Create execution summary
        exec_summary = create_execution_summary(result)

        # Get report content
        report_content = result.get('report_markdown', '')

        return summary, df, exec_summary, report_content

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        return error_msg, None, None, None


async def run_phase2_async(
        countries: List[str],
        num_peer_rankers: int,
        debate_enabled: bool,
        debate_threshold: str,
        num_challengers: int,
        progress=gr.Progress()
) -> tuple:
    """Run Phase 2 workflow with progress tracking."""

    progress(0, desc="Validating inputs...")

    # Validate countries
    valid_codes, invalid = validate_countries(countries)

    if invalid:
        error_msg = f"❌ Invalid countries: {', '.join(invalid)}"
        return error_msg, None, None, None, None

    if len(valid_codes) < 2:
        return "❌ Need at least 2 valid countries", None, None, None, None

    progress(0.1, desc="Generating research data...")

    try:
        # Generate research
        research_data = generate_research_data(valid_codes)

        progress(0.2, desc="Starting workflow...")

        # Run Phase 2
        result = await run_phase2_langgraph(
            countries=valid_codes,
            research_json_data=research_data,
            num_peer_rankers=num_peer_rankers,
            debate_enabled=debate_enabled,
            debate_threshold=debate_threshold.lower().replace(" ", "_"),
            num_challengers=num_challengers
        )

        progress(1.0, desc="Complete!")

        # Format outputs
        rankings = result.get('final_ranking', [])

        # Create summary
        summary_lines = ["# 🎯 Analysis Complete!", ""]
        if rankings:
            winner = rankings[0]
            summary_lines.append(f"## Winner: **{winner['country_code']}**")
            summary_lines.append(f"**Score:** {winner['consensus_score']:.2f}/10")
            summary_lines.append(f"**Agreement:** {winner.get('agreement_level', 'unknown')}")

            if result.get('debate_triggered'):
                verdict = result.get('debate_result', {}).get('verdict', 'Unknown')
                summary_lines.append("")
                summary_lines.append(f"**Debate Verdict:** {verdict}")

        summary = "\n".join(summary_lines)

        # Create rankings table
        df = create_ranking_dataframe(rankings)

        # Create execution summary
        exec_summary = create_execution_summary(result)

        # Create debate summary
        debate_summary = ""
        if result.get('debate_triggered') and result.get('debate_result'):
            debate_summary = create_debate_summary(result['debate_result'])

        # Get report content
        report_content = result.get('report_markdown', '')

        return summary, df, exec_summary, debate_summary, report_content

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        return error_msg, None, None, None, None


# ============================================================================
# Gradio Interface
# ============================================================================

def create_gradio_interface():
    """Create Gradio interface."""

    with gr.Blocks(
            theme=gr.themes.Soft(),
            title="Renewable Energy Investment Ranking",
            css="""
        .gradio-container {
            max-width: 1400px !important;
        }
        .header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        """
    ) as demo:
        # Header
        gr.HTML("""
        <div class="header">
            <h1>🌍 Renewable Energy Investment Ranking System</h1>
            <p>Multi-Agent AI Analysis for Optimal Investment Decisions</p>
        </div>
        """)

        # Tabs for Phase 1 and Phase 2
        with gr.Tabs():
            # ================================================================
            # Phase 1 Tab
            # ================================================================

            with gr.Tab("Phase 1 - Initial Rankings"):
                gr.Markdown("""
                ## Phase 1: Expert Analysis & Peer Consensus

                Generate expert presentations for each country and aggregate peer rankings to identify the top investment destination.
                """)

                with gr.Row():
                    with gr.Column(scale=1):
                        # Inputs
                        gr.Markdown("### 🎯 Configuration")

                        countries_phase1 = gr.Dropdown(
                            choices=SUPPORTED_COUNTRIES,
                            multiselect=True,
                            label="Select Countries (2-15)",
                            info="Choose countries to analyze",
                            value=["USA", "IND", "CHN"]
                        )

                        num_peer_rankers_phase1 = gr.Slider(
                            minimum=2,
                            maximum=5,
                            value=3,
                            step=1,
                            label="Number of Peer Rankers",
                            info="Independent agents that evaluate presentations"
                        )

                        run_phase1_btn = gr.Button(
                            "🚀 Run Phase 1 Analysis",
                            variant="primary",
                            size="lg"
                        )

                    with gr.Column(scale=2):
                        # Outputs
                        gr.Markdown("### 📊 Results")

                        summary_phase1 = gr.Markdown()

                        with gr.Row():
                            rankings_table_phase1 = gr.Dataframe(
                                label="Final Rankings",
                                interactive=False
                            )

                        with gr.Accordion("⏱️ Execution Details", open=False):
                            exec_summary_phase1 = gr.Markdown()

                        with gr.Accordion("📄 Full Report", open=False):
                            report_phase1 = gr.Markdown()

                # Connect Phase 1
                run_phase1_btn.click(
                    fn=lambda *args: asyncio.run(run_phase1_async(*args)),
                    inputs=[
                        countries_phase1,
                        num_peer_rankers_phase1
                    ],
                    outputs=[
                        summary_phase1,
                        rankings_table_phase1,
                        exec_summary_phase1,
                        report_phase1
                    ]
                )

            # ================================================================
            # Phase 2 Tab
            # ================================================================

            with gr.Tab("Phase 2 - Hot Seat Debate"):
                gr.Markdown("""
                ## Phase 2: Adversarial Debate & Final Verdict

                Challenge the top-ranked country with adversarial agents to stress-test the recommendation.
                """)

                with gr.Row():
                    with gr.Column(scale=1):
                        # Inputs
                        gr.Markdown("### 🎯 Configuration")

                        countries_phase2 = gr.Dropdown(
                            choices=SUPPORTED_COUNTRIES,
                            multiselect=True,
                            label="Select Countries (2-15)",
                            info="Choose countries to analyze",
                            value=["USA", "IND", "CHN"]
                        )

                        num_peer_rankers_phase2 = gr.Slider(
                            minimum=2,
                            maximum=5,
                            value=3,
                            step=1,
                            label="Number of Peer Rankers",
                            info="Independent agents that evaluate presentations"
                        )

                        gr.Markdown("#### 🔥 Debate Settings")

                        debate_enabled = gr.Checkbox(
                            value=True,
                            label="Enable Hot Seat Debate",
                            info="Challenge top-ranked country"
                        )

                        debate_threshold = gr.Radio(
                            choices=["Very High", "High", "Medium", "Low"],
                            value="High",
                            label="Debate Trigger Threshold",
                            info="Trigger debate if consensus is below this level"
                        )

                        num_challengers = gr.Slider(
                            minimum=1,
                            maximum=3,
                            value=2,
                            step=1,
                            label="Number of Challengers",
                            info="Adversarial agents in debate"
                        )

                        run_phase2_btn = gr.Button(
                            "🔥 Run Phase 2 Analysis",
                            variant="primary",
                            size="lg"
                        )

                    with gr.Column(scale=2):
                        # Outputs
                        gr.Markdown("### 📊 Results")

                        summary_phase2 = gr.Markdown()

                        with gr.Row():
                            rankings_table_phase2 = gr.Dataframe(
                                label="Final Rankings",
                                interactive=False
                            )

                        with gr.Accordion("🔥 Debate Analysis", open=True):
                            debate_summary = gr.Markdown()

                        with gr.Accordion("⏱️ Execution Details", open=False):
                            exec_summary_phase2 = gr.Markdown()

                        with gr.Accordion("📄 Full Report", open=False):
                            report_phase2 = gr.Markdown()

                # Connect Phase 2
                run_phase2_btn.click(
                    fn=lambda *args: asyncio.run(run_phase2_async(*args)),
                    inputs=[
                        countries_phase2,
                        num_peer_rankers_phase2,
                        debate_enabled,
                        debate_threshold,
                        num_challengers
                    ],
                    outputs=[
                        summary_phase2,
                        rankings_table_phase2,
                        exec_summary_phase2,
                        debate_summary,
                        report_phase2
                    ]
                )

            # ================================================================
            # About Tab
            # ================================================================

            with gr.Tab("About"):
                gr.Markdown("""
                # 🌍 Renewable Energy Investment Ranking System

                ## Overview

                This multi-agent AI system analyzes renewable energy investment opportunities across countries using:

                - **Expert Agents**: Specialized agents that build investment cases for each country
                - **Peer Rankers**: Independent evaluators that rank all presentations
                - **Aggregation**: Hybrid scoring combining Borda count and average scores
                - **Hot Seat Debate** (Phase 2): Adversarial testing of top recommendations

                ## Methodology

                ### Phase 1: Initial Rankings
                1. **Research Loading**: Country-specific renewable energy data
                2. **Expert Presentations**: AI agents build detailed investment cases
                3. **Peer Rankings**: Independent agents evaluate all presentations
                4. **Aggregation**: Consensus ranking using hybrid methodology
                5. **Report Generation**: Comprehensive markdown report

                ### Phase 2: Hot Seat Debate
                - All Phase 1 stages, plus:
                - **Conditional Debate**: Triggered when consensus is below threshold
                - **Adversarial Challenge**: Challenger agents attack top-ranked country
                - **Defense**: Defender agent protects the ranking
                - **Final Verdict**: Ranking upheld or overturned

                ## Technology Stack

                - **LangGraph**: Workflow orchestration
                - **LangChain**: LLM integration
                - **Azure OpenAI**: Language model provider
                - **Gradio**: User interface
                - **FastAPI**: REST API backend

                ## Supported Countries

                USA, India, China, Brazil, Germany, Japan, UK, France, Canada, Australia, South Africa, Mexico, Spain, Italy

                ## Author

                **Kanauija** - Python Institute LLP

                ## License

                Proprietary - All Rights Reserved
                """)

        # Footer
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #666;">
            <p>Powered by LangGraph + Azure OpenAI | Built with Gradio</p>
            <p>© 2024 Python Institute LLP. All rights reserved.</p>
        </div>
        """)

    return demo


# ============================================================================
# Main
# ============================================================================

def main():
    """Launch Gradio app."""
    demo = create_gradio_interface()

    # Launch
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Set to True to create public link
        show_error=True
    )


if __name__ == "__main__":
    main()