"""
Insights Team - Executive Report Generator (Phase 1)

Generates comprehensive investment reports with:
- Executive summary
- Detailed rankings with consensus scores
- Expert presentations for each country
- Peer analysis and agreement metrics
- Methodology and references

Output: Professional markdown report ready for stakeholders.
"""

import os
import logging
from typing import Dict, Any, List
from datetime import datetime

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import (
    AgentFramework,
    AgentCapability
)

logger = logging.getLogger("ReportGenerator")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Report Generation
# ============================================================================

def generate_executive_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive executive report from Phase 1 results.

    Input (from state):
        - countries: List[str]
        - aggregated_ranking: Dict with final rankings
        - expert_presentations: Dict with presentations
        - peer_rankings: List of peer rankings
        - execution_metadata: Timing and metrics

    Output (to state):
        - executive_report: Dict with report sections
        - report_markdown: str - Formatted markdown
        - report_metadata: Dict with generation info
    """

    start_time = datetime.now()

    logger.info("=" * 70)
    logger.info("REPORT GENERATOR - Starting")
    logger.info("=" * 70)

    # Extract data
    countries = state.get("countries", [])
    aggregated_ranking = state.get("aggregated_ranking", {})
    expert_presentations = state.get("expert_presentations", {})
    peer_rankings = state.get("peer_rankings", [])
    exec_metadata = state.get("execution_metadata", {})

    final_rankings = aggregated_ranking.get("final_rankings", [])

    if not final_rankings:
        logger.warning("No rankings available for report")
        return {
            "executive_report": {},
            "report_markdown": "# Error: No rankings available",
            "report_metadata": {"error": "No rankings"}
        }

    # Generate report sections
    report = {
        "title": "Renewable Energy Investment Analysis - Phase 1 Rankings",
        "generated_at": datetime.now().isoformat(),
        "countries_analyzed": len(countries),
        "executive_summary": _generate_executive_summary(final_rankings, peer_rankings),
        "final_rankings": _generate_rankings_section(final_rankings),
        "country_analyses": _generate_country_analyses(
            final_rankings,
            expert_presentations,
            peer_rankings
        ),
        "methodology": _generate_methodology_section(
            aggregated_ranking,
            exec_metadata
        ),
        "execution_summary": _generate_execution_summary(exec_metadata)
    }

    # Generate markdown
    markdown_report = _format_as_markdown(report)

    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"phase1_report_{timestamp}.md"
    filepath = f"reports/{filename}"

    # Create reports directory
    os.makedirs("reports", exist_ok=True)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_report)
        logger.info(f"📄 Report saved to: {filepath}")
    except Exception as e:
        logger.warning(f"Could not save report file: {e}")
        filepath = None

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("=" * 70)
    logger.info("✅ REPORT GENERATED")
    logger.info("=" * 70)
    logger.info(f"Report size: {len(markdown_report):,} characters")
    logger.info(f"Time: {duration:.2f}s")
    if filepath:
        logger.info(f"Saved to: {filepath}")

    return {
        "executive_report": report,
        "report_markdown": markdown_report,
        "report_metadata": {
            "filename": filename,
            "filepath": filepath,
            "generated_at": end_time.isoformat(),
            "report_size_chars": len(markdown_report),
            "generation_time_seconds": round(duration, 2),
            "countries_analyzed": len(countries),
            "rankings_included": len(final_rankings)
        }
    }


def _generate_executive_summary(
        final_rankings: List[Dict],
        peer_rankings: List[Dict]
) -> str:
    """Generate executive summary."""

    if not final_rankings:
        return "No rankings available."

    top_country = final_rankings[0]
    top_code = top_country["country_code"]
    top_score = top_country["consensus_score"]
    agreement = top_country["peer_agreement"]["agreement_level"]

    summary = f"""Based on comprehensive multi-agent analysis, **{top_code}** emerges as the top investment destination with a consensus score of **{top_score}/10**.

**Key Findings:**

- **Winner**: {top_code} ranked #1 with {agreement} peer agreement
- **Peer Consensus**: {len(peer_rankings)} independent peer agents evaluated all presentations
- **Analysis Method**: Expert presentations followed by comparative peer ranking and aggregation

"""

    if len(final_rankings) > 1:
        runner_up = final_rankings[1]
        summary += f"- **Runner-up**: {runner_up['country_code']} (Score: {runner_up['consensus_score']}/10)\n"

    if len(final_rankings) > 2:
        third = final_rankings[2]
        summary += f"- **Third Place**: {third['country_code']} (Score: {third['consensus_score']}/10)\n"

    # Add peer agreement note
    all_agree = all(
        r["peer_agreement"]["agreement_level"] in ["very_high", "high"]
        for r in final_rankings
    )

    if all_agree:
        summary += f"\n**High Confidence**: All rankings show strong peer agreement, indicating robust consensus.\n"

    return summary.strip()


def _generate_rankings_section(final_rankings: List[Dict]) -> List[Dict]:
    """Generate rankings section with details."""

    rankings = []

    for ranking in final_rankings:
        rankings.append({
            "rank": ranking["rank"],
            "country_code": ranking["country_code"],
            "consensus_score": ranking["consensus_score"],
            "average_peer_score": ranking["average_peer_score"],
            "score_stddev": ranking["score_stddev"],
            "peer_scores": ranking["peer_scores"],
            "borda_points": ranking["borda_points"],
            "agreement_level": ranking["peer_agreement"]["agreement_level"],
            "rank_variance": ranking["peer_agreement"]["rank_variance"],
            "score_range": ranking["peer_agreement"]["score_range"]
        })

    return rankings


def _generate_country_analyses(
        final_rankings: List[Dict],
        expert_presentations: Dict[str, Dict],
        peer_rankings: List[Dict]
) -> List[Dict]:
    """Generate detailed country analyses."""

    analyses = []

    for ranking in final_rankings:
        country_code = ranking["country_code"]
        presentation = expert_presentations.get(country_code, {})

        # Get peer reasonings
        peer_reasonings = []
        for peer_ranking in peer_rankings:
            for country_rank in peer_ranking.get("rankings", []):
                if country_rank["country_code"] == country_code:
                    peer_reasonings.append({
                        "peer_id": peer_ranking["peer_id"],
                        "score": country_rank["score"],
                        "reasoning": country_rank.get("reasoning", "")
                    })

        analysis = {
            "rank": ranking["rank"],
            "country_code": country_code,
            "consensus_score": ranking["consensus_score"],
            "agreement": ranking["peer_agreement"]["agreement_level"],

            # From expert presentation
            "executive_summary": presentation.get("executive_summary", "N/A"),
            "strengths": presentation.get("strengths", []),
            "opportunities": presentation.get("opportunities", []),
            "risks": presentation.get("risks", []),
            "investment_case": presentation.get("investment_case", "N/A"),
            "expert_recommendation": presentation.get("recommendation", "N/A"),
            "expert_confidence": presentation.get("confidence", "N/A"),

            # From peer analysis
            "peer_reasonings": peer_reasonings,
            "peer_scores": ranking["peer_scores"]
        }

        analyses.append(analysis)

    return analyses


def _generate_methodology_section(
        aggregated_ranking: Dict,
        exec_metadata: Dict
) -> Dict:
    """Generate methodology section."""

    return {
        "workflow": "Phase 1 - Initial Rankings",
        "stages": [
            "1. Research Loading: Country-specific renewable energy research",
            "2. Expert Presentations: Dedicated expert agents build investment cases",
            "3. Peer Rankings: Independent peer agents rank all presentations",
            "4. Aggregation: Borda count + average scoring to generate consensus"
        ],
        "aggregation_method": aggregated_ranking.get("method", "hybrid"),
        "num_peers": aggregated_ranking.get("num_peers", 0),
        "ai_model": "GPT-4o (via LangChain)",
        "execution_mode": "Parallel (Stages 2 & 3)",
        "stage_timings": exec_metadata.get("stage_timings", {})
    }


def _generate_execution_summary(exec_metadata: Dict) -> Dict:
    """Generate execution summary."""

    return {
        "total_duration_seconds": exec_metadata.get("total_duration_seconds", 0),
        "parallel_efficiency": exec_metadata.get("parallel_efficiency", 0),
        "stage_timings": exec_metadata.get("stage_timings", {}),
        "start_time": exec_metadata.get("start_time", ""),
        "end_time": exec_metadata.get("end_time", "")
    }


def _format_as_markdown(report: Dict) -> str:
    """Format report as markdown."""

    md = f"""# {report['title']}

**Generated:** {report['generated_at']}  
**Countries Analyzed:** {report['countries_analyzed']}

---

## Executive Summary

{report['executive_summary']}

---

## Final Rankings

"""

    # Rankings table
    rankings = report['final_rankings']
    if rankings:
        md += "| Rank | Country | Consensus Score | Avg Peer Score | Agreement | Peer Scores |\n"
        md += "|------|---------|-----------------|----------------|-----------|-------------|\n"

        for r in rankings:
            scores_str = ", ".join([f"{s:.1f}" for s in r['peer_scores']])
            md += f"| **#{r['rank']}** | **{r['country_code']}** | **{r['consensus_score']}/10** | "
            md += f"{r['average_peer_score']:.1f}/10 | {r['agreement_level']} | {scores_str} |\n"

        md += "\n"

    # Country analyses
    md += "---\n\n## Detailed Country Analyses\n\n"

    for analysis in report['country_analyses']:
        rank_emoji = "🥇" if analysis['rank'] == 1 else "🥈" if analysis['rank'] == 2 else "🥉" if analysis[
                                                                                                    'rank'] == 3 else "📊"

        md += f"### {rank_emoji} #{analysis['rank']} - {analysis['country_code']}\n\n"
        md += f"**Consensus Score:** {analysis['consensus_score']}/10 | "
        md += f"**Agreement:** {analysis['agreement']} | "
        md += f"**Expert Recommendation:** {analysis['expert_recommendation']}\n\n"

        # Executive Summary
        md += "#### Executive Summary\n\n"
        md += f"{analysis['executive_summary']}\n\n"

        # Strengths
        if analysis['strengths']:
            md += "#### Key Strengths\n\n"
            for i, strength in enumerate(analysis['strengths'], 1):
                md += f"{i}. {strength}\n"
            md += "\n"

        # Opportunities
        if analysis['opportunities']:
            md += "#### Investment Opportunities\n\n"
            for i, opp in enumerate(analysis['opportunities'], 1):
                md += f"{i}. {opp}\n"
            md += "\n"

        # Risks
        if analysis['risks']:
            md += "#### Risks & Challenges\n\n"
            for i, risk in enumerate(analysis['risks'], 1):
                md += f"{i}. {risk}\n"
            md += "\n"

        # Investment Case
        if analysis['investment_case'] and analysis['investment_case'] != "N/A":
            md += "#### Investment Case\n\n"
            md += f"{analysis['investment_case']}\n\n"

        # Peer Analysis
        md += "#### Peer Evaluation\n\n"
        md += f"**Peer Scores:** {', '.join([f'{s:.1f}/10' for s in analysis['peer_scores']])}\n\n"

        if analysis['peer_reasonings']:
            md += "**Peer Reasonings:**\n\n"
            for pr in analysis['peer_reasonings']:
                md += f"- **{pr['peer_id']}** ({pr['score']}/10): {pr['reasoning']}\n"
            md += "\n"

        md += "---\n\n"

    # Methodology
    md += "## Methodology\n\n"
    methodology = report['methodology']

    md += f"**Workflow:** {methodology['workflow']}\n\n"

    md += "**Analysis Stages:**\n\n"
    for stage in methodology['stages']:
        md += f"- {stage}\n"
    md += "\n"

    md += f"**Aggregation Method:** {methodology['aggregation_method']}\n"
    md += f"**Number of Peer Rankers:** {methodology['num_peers']}\n"
    md += f"**AI Model:** {methodology['ai_model']}\n"
    md += f"**Execution Mode:** {methodology['execution_mode']}\n\n"

    # Execution summary
    md += "## Execution Summary\n\n"
    exec_summary = report['execution_summary']

    md += f"**Total Duration:** {exec_summary['total_duration_seconds']:.2f} seconds\n"
    md += f"**Parallel Efficiency:** {exec_summary.get('parallel_efficiency', 0):.2f}x\n\n"

    if exec_summary.get('stage_timings'):
        md += "**Stage Timings:**\n\n"
        for stage, duration in exec_summary['stage_timings'].items():
            md += f"- {stage.capitalize()}: {duration:.2f}s\n"
        md += "\n"

    # Footer
    md += "---\n\n"
    md += "*This report was generated by the Phase 1 Multi-Agent Ranking System*  \n"
    md += f"*Generated at: {report['generated_at']}*\n"
    md += "*Framework: Custom + LangChain + Async Parallel Execution*\n"

    return md


# ============================================================================
# Agent Registration
# ============================================================================

@register_agent(
    agent_id="insights_team_report_generator_phase1_v1",
    name="Executive Report Generator (Phase 1)",
    description="Generates comprehensive markdown reports with rankings, presentations, and analysis",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.REPORT_GEN],
    business_unit="insights_team",
    contact="insights@company.com",
    version="1.0.0",
    required_inputs=["aggregated_ranking", "expert_presentations"],
    output_keys=["executive_report", "report_markdown", "report_metadata"],
    tags=["report", "markdown", "executive", "phase1"]
)
def report_generator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Report generator agent wrapper."""
    return generate_executive_report(state)
