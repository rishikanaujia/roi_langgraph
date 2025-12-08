"""
Executive Report Generator

Generates comprehensive markdown reports from workflow results.

Author: Kanauija
Date: 2024-12-08
Updated: 2024-12-08 - Added Phase 2 support with debate section and fixed statistics extraction
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("ReportGenerator")


def generate_executive_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate executive markdown report from workflow results.

    Supports both Phase 1 (no debate) and Phase 2 (with debate) workflows.

    Parameters:
    -----------
    state : Dict[str, Any]
        Complete workflow state including:
        - countries: List of country codes
        - expert_presentations: Expert analysis results
        - peer_rankings: Peer ranking results
        - aggregated_ranking: Consensus ranking
        - final_ranking: Final ranking (after debate if applicable)
        - debate_triggered: Whether debate was executed
        - debate_result: Debate results (if triggered)
        - stage_timings: Execution timings

    Returns:
    --------
    Dict[str, Any]
        - report_markdown: Generated markdown report
        - report_metadata: Report metadata (filepath, etc.)
    """
    logger.info("=" * 70)
    logger.info("REPORT GENERATOR - Starting")
    logger.info("=" * 70)

    start_time = datetime.now()

    # Detect workflow type
    debate_triggered = state.get("debate_triggered", False)
    workflow_type = "Phase 2 - Hot Seat Debate" if debate_triggered else "Phase 1 - Initial Rankings"

    # Generate report sections
    sections = []

    # Header
    sections.append(_generate_header(state, workflow_type))

    # Executive Summary
    sections.append(_generate_executive_summary(state, workflow_type))

    # Final Rankings Table
    sections.append(_generate_rankings_table(state))

    # Phase 2: Debate Section (if triggered)
    if debate_triggered:
        sections.append(_generate_debate_section(state))

    # Detailed Country Analyses
    sections.append(_generate_country_analyses(state))

    # Methodology
    sections.append(_generate_methodology(state, workflow_type))

    # Execution Summary
    sections.append(_generate_execution_summary(state))

    # Footer
    sections.append(_generate_footer(workflow_type))

    # Combine all sections
    report_markdown = "\n\n".join(sections)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"phase{'2' if debate_triggered else '1'}_report_{timestamp}.md"
    filepath = Path("reports") / filename

    # Ensure reports directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_markdown)

    duration = (datetime.now() - start_time).total_seconds()

    logger.info(f"📄 Report saved to: {filepath}")
    logger.info("=" * 70)
    logger.info("✅ REPORT GENERATED")
    logger.info("=" * 70)
    logger.info(f"Report size: {len(report_markdown):,} characters")
    logger.info(f"Time: {duration:.2f}s")
    logger.info(f"Saved to: {filepath}")

    return {
        "report_markdown": report_markdown,
        "report_metadata": {
            "filepath": str(filepath),
            "filename": filename,
            "size_chars": len(report_markdown),
            "generation_time_seconds": duration,
            "generated_at": datetime.now().isoformat(),
            "workflow_type": workflow_type
        }
    }


def _generate_header(state: Dict[str, Any], workflow_type: str) -> str:
    """Generate report header."""
    countries = state.get("countries", [])
    timestamp = datetime.now().isoformat()

    return f"""# Renewable Energy Investment Analysis - {workflow_type}

**Generated:** {timestamp}  
**Countries Analyzed:** {len(countries)}

---"""


def _generate_executive_summary(state: Dict[str, Any], workflow_type: str) -> str:
    """Generate executive summary."""
    final_ranking = state.get("final_ranking", [])
    peer_rankings = state.get("peer_rankings", [])
    debate_triggered = state.get("debate_triggered", False)
    debate_result = state.get("debate_result")

    if not final_ranking:
        return "## Executive Summary\n\nNo ranking data available."

    # Get winner
    winner = final_ranking[0]
    runner_up = final_ranking[1] if len(final_ranking) > 1 else None
    third_place = final_ranking[2] if len(final_ranking) > 2 else None

    # Build summary
    lines = ["## Executive Summary", ""]

    # Debate verdict (if applicable)
    if debate_triggered and debate_result:
        verdict = debate_result.get("verdict", "UNKNOWN")
        if verdict == "OVERTURNED":
            lines.append(f"**🔄 DEBATE VERDICT: OVERTURNED** - After rigorous debate, the ranking was revised.")
        else:
            lines.append(f"**✅ DEBATE VERDICT: UPHELD** - The original ranking withstood challenger scrutiny.")
        lines.append("")

    lines.append(
        f"Based on comprehensive multi-agent analysis, **{winner['country_code']}** emerges as the top investment destination with a consensus score of **{winner['consensus_score']:.2f}/10**.")
    lines.append("")

    lines.append("**Key Findings:**")
    lines.append("")
    lines.append(
        f"- **Winner**: {winner['country_code']} ranked #1 with {winner.get('agreement_level', 'unknown')} peer agreement")

    if debate_triggered and debate_result:
        # Extract statistics properly (handle nested structure)
        statistics = debate_result.get("statistics", {})
        rounds = debate_result.get("rounds", [])
        num_rounds = statistics.get("total_rounds", len(rounds))
        recommendation = debate_result.get("recommendation", "")

        lines.append(f"- **Debate Executed**: Hot seat debate with {num_rounds} rounds")
        lines.append(
            f"- **Verdict**: {debate_result.get('verdict', 'UNKNOWN')} - {recommendation}")

    lines.append(f"- **Peer Consensus**: {len(peer_rankings)} independent peer agents evaluated all presentations")
    lines.append(f"- **Analysis Method**: Expert presentations followed by comparative peer ranking and aggregation")
    lines.append("")

    if runner_up:
        lines.append(f"- **Runner-up**: {runner_up['country_code']} (Score: {runner_up['consensus_score']:.2f}/10)")
    if third_place:
        lines.append(
            f"- **Third Place**: {third_place['country_code']} (Score: {third_place['consensus_score']:.2f}/10)")
    lines.append("")

    # Agreement indicator
    if winner.get('agreement_level') in ['very_high', 'high']:
        lines.append("**High Confidence**: All rankings show strong peer agreement, indicating robust consensus.")
    elif winner.get('agreement_level') == 'medium':
        lines.append("**Moderate Confidence**: Rankings show reasonable agreement with some divergence.")
    else:
        lines.append("**Low Confidence**: Significant divergence in peer rankings - further analysis recommended.")

    lines.append("")
    lines.append("---")

    return "\n".join(lines)


def _generate_rankings_table(state: Dict[str, Any]) -> str:
    """Generate final rankings table."""
    final_ranking = state.get("final_ranking", [])

    if not final_ranking:
        return "## Final Rankings\n\nNo ranking data available."

    lines = ["## Final Rankings", ""]
    lines.append("| Rank | Country | Consensus Score | Avg Peer Score | Agreement | Peer Scores |")
    lines.append("|------|---------|-----------------|----------------|-----------|-------------|")

    for country in final_ranking:
        rank = country.get("rank", 0)
        code = country.get("country_code", "???")
        consensus = country.get("consensus_score", 0)
        avg_peer = country.get("average_peer_score", 0)
        agreement = country.get("agreement_level", "unknown")
        peer_scores = country.get("peer_scores", [])

        # Format peer scores
        peer_scores_str = ", ".join([f"{s:.1f}" for s in peer_scores]) if peer_scores else "N/A"

        # Add debate markers
        marker = ""
        if country.get("debate_winner"):
            marker = " 🏆"
        elif country.get("debate_loser"):
            marker = " 📉"

        # Format rank
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "")
        rank_str = f"**#{rank}**" if rank == 1 else f"**#{rank}**"

        lines.append(
            f"| {rank_emoji} {rank_str} | **{code}**{marker} | **{consensus:.2f}/10** | {avg_peer:.1f}/10 | {agreement} | {peer_scores_str} |"
        )

    lines.append("")
    lines.append("---")

    return "\n".join(lines)


def _generate_debate_section(state: Dict[str, Any]) -> str:
    """Generate debate section (Phase 2 only)."""
    debate_result = state.get("debate_result", {})
    final_ranking = state.get("final_ranking", [])

    # 🐛 DEBUG: Print the structure
    import json
    logger.info("=" * 70)
    logger.info("DEBUG: debate_result keys: %s", list(debate_result.keys()))
    logger.info("DEBUG: debate_result structure:")
    logger.info(json.dumps(debate_result, indent=2, default=str))
    logger.info("=" * 70)

    if not debate_result:
        logger.warning("No debate_result found in state")
        return ""

    lines = ["## 🔥 Hot Seat Debate Analysis", ""]

    # Get participants
    defender = final_ranking[0] if final_ranking else None
    challenger = final_ranking[1] if len(final_ranking) > 1 else None

    if defender and challenger:
        lines.append(f"**Defending Position:** {defender['country_code']} (Top Ranked)")
        lines.append(f"**Challenger:** {challenger['country_code']} (Runner-up)")
        lines.append("")

    # Verdict
    verdict = debate_result.get("verdict", "UNKNOWN")
    recommendation = debate_result.get("recommendation", "")

    lines.append("### Verdict")
    lines.append("")
    if verdict == "OVERTURNED":
        lines.append(f"**🔄 OVERTURNED** - {recommendation}")
        lines.append("")
        lines.append("The challenger successfully demonstrated superior investment merits, ")
        lines.append("resulting in a revised ranking order.")
    else:
        lines.append(f"**✅ UPHELD** - {recommendation}")
        lines.append("")
        lines.append("The defending position successfully countered all challenges, ")
        lines.append("confirming the original ranking.")
    lines.append("")

    # Extract statistics - handle both flat and nested structures
    statistics = debate_result.get("statistics", {})
    rounds = debate_result.get("rounds", [])

    # Try nested structure first, then fall back to flat structure
    total_rounds = statistics.get("total_rounds", len(rounds))
    challenger_wins = statistics.get("challenger_wins", debate_result.get("challenger_wins", 0))
    defender_wins = statistics.get("defender_wins", debate_result.get("defender_wins", 0))
    avg_challenger_score = statistics.get("avg_challenger_score", debate_result.get("avg_challenger_score", 0.0))
    avg_defender_score = statistics.get("avg_defender_score", debate_result.get("avg_defender_score", 0.0))

    logger.info(f"Extracted debate stats: rounds={total_rounds}, challenger_wins={challenger_wins}, "
                f"defender_wins={defender_wins}, avg_challenger={avg_challenger_score:.2f}, "
                f"avg_defender={avg_defender_score:.2f}")

    # Statistics
    lines.append("### Debate Statistics")
    lines.append("")
    lines.append(f"- **Total Rounds:** {total_rounds}")
    lines.append(f"- **Challenger Wins:** {challenger_wins}")
    lines.append(f"- **Defender Wins:** {defender_wins}")
    lines.append(f"- **Average Challenger Score:** {avg_challenger_score:.2f}/10")
    lines.append(f"- **Average Defender Score:** {avg_defender_score:.2f}/10")
    lines.append("")

    # Round-by-round
    if rounds:
        lines.append("### Round-by-Round Analysis")
        lines.append("")

        for i, round_data in enumerate(rounds, 1):
            # Handle different possible structures for round data
            judgment = round_data.get("judgment", {})
            challenge = round_data.get("challenge", {})
            defense = round_data.get("defense", {})

            lines.append(f"#### Round {i}")
            lines.append("")

            # Try to get scores from judgment first, then fall back to round_data
            challenger_score = judgment.get("challenger_score", round_data.get("challenger_score", 0))
            defender_score = judgment.get("defender_score", round_data.get("defender_score", 0))
            winner = judgment.get("winner", round_data.get("winner", "Unknown"))

            lines.append(f"**Challenge Score:** {challenger_score:.1f}/10")
            lines.append(f"**Defense Score:** {defender_score:.1f}/10")
            lines.append(f"**Winner:** {winner}")
            lines.append("")

            # Challenge argument (truncated)
            challenge_arg = challenge.get("argument", round_data.get("challenge_argument", ""))
            if challenge_arg and len(challenge_arg) > 300:
                challenge_arg = challenge_arg[:300] + "..."
            if challenge_arg:
                lines.append(f"*Challenge:* {challenge_arg}")
                lines.append("")

            # Defense response (truncated)
            defense_arg = defense.get("argument", round_data.get("defense_response", ""))
            if defense_arg and len(defense_arg) > 300:
                defense_arg = defense_arg[:300] + "..."
            if defense_arg:
                lines.append(f"*Defense:* {defense_arg}")
                lines.append("")

    lines.append("---")

    return "\n".join(lines)


def _generate_country_analyses(state: Dict[str, Any]) -> str:
    """Generate detailed country analyses."""
    final_ranking = state.get("final_ranking", [])
    expert_presentations = state.get("expert_presentations", {})
    peer_rankings = state.get("peer_rankings", [])

    if not final_ranking:
        return "## Detailed Country Analyses\n\nNo data available."

    lines = ["## Detailed Country Analyses", ""]

    for country in final_ranking:
        country_code = country.get("country_code", "???")
        rank = country.get("rank", 0)

        # Get presentation
        presentation = expert_presentations.get(country_code, {})

        # Rank emoji
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "📊")

        lines.append(f"### {rank_emoji} #{rank} - {country_code}")
        lines.append("")
        lines.append(f"**Consensus Score:** {country['consensus_score']:.2f}/10 | "
                     f"**Agreement:** {country.get('agreement_level', 'unknown')} | "
                     f"**Expert Recommendation:** {presentation.get('recommendation', 'N/A')}")
        lines.append("")

        # Executive Summary
        if presentation.get("executive_summary"):
            lines.append("#### Executive Summary")
            lines.append("")
            lines.append(presentation["executive_summary"])
            lines.append("")

        # Key Strengths
        strengths = presentation.get("key_strengths", [])
        if strengths:
            lines.append("#### Key Strengths")
            lines.append("")
            for i, strength in enumerate(strengths, 1):
                lines.append(f"{i}. {strength}")
            lines.append("")

        # Investment Opportunities
        opportunities = presentation.get("investment_opportunities", [])
        if opportunities:
            lines.append("#### Investment Opportunities")
            lines.append("")
            for i, opp in enumerate(opportunities, 1):
                lines.append(f"{i}. {opp}")
            lines.append("")

        # Risks & Challenges
        risks = presentation.get("risks_and_challenges", [])
        if risks:
            lines.append("#### Risks & Challenges")
            lines.append("")
            for i, risk in enumerate(risks, 1):
                lines.append(f"{i}. {risk}")
            lines.append("")

        # Investment Case
        if presentation.get("investment_case"):
            lines.append("#### Investment Case")
            lines.append("")
            lines.append(presentation["investment_case"])
            lines.append("")

        # Peer Evaluation
        peer_scores = country.get("peer_scores", [])
        if peer_scores and peer_rankings:
            lines.append("#### Peer Evaluation")
            lines.append("")
            lines.append(f"**Peer Scores:** {', '.join([f'{s:.1f}/10' for s in peer_scores])}")
            lines.append("")
            lines.append("**Peer Reasonings:**")
            lines.append("")

            # Get peer reasonings for this country
            for i, peer_ranking in enumerate(peer_rankings, 1):
                rankings_list = peer_ranking.get("rankings", [])
                for rank_item in rankings_list:
                    if rank_item.get("country_code") == country_code:
                        reasoning = rank_item.get("reasoning", "No reasoning provided")
                        score = rank_item.get("score", 0)
                        lines.append(f"- **peer_ranker_{i}** ({score}/10): {reasoning}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _generate_methodology(state: Dict[str, Any], workflow_type: str) -> str:
    """Generate methodology section."""
    peer_rankings = state.get("peer_rankings", [])
    aggregated_ranking = state.get("aggregated_ranking", {})
    debate_triggered = state.get("debate_triggered", False)

    lines = ["## Methodology", ""]
    lines.append(f"**Workflow:** {workflow_type}")
    lines.append("")
    lines.append("**Analysis Stages:**")
    lines.append("")

    if debate_triggered:
        lines.append("- 1. Research Loading: Country-specific renewable energy research")
        lines.append("- 2. Expert Presentations: Dedicated expert agents build investment cases")
        lines.append("- 3. Peer Rankings: Independent peer agents rank all presentations")
        lines.append("- 4. Aggregation: Borda count + average scoring to generate consensus")
        lines.append("- 5. Hot Seat Debate: Challenger agents test top-ranked country")
        lines.append("- 6. Final Verdict: Ranking maintained or revised based on debate")
    else:
        lines.append("- 1. Research Loading: Country-specific renewable energy research")
        lines.append("- 2. Expert Presentations: Dedicated expert agents build investment cases")
        lines.append("- 3. Peer Rankings: Independent peer agents rank all presentations")
        lines.append("- 4. Aggregation: Borda count + average scoring to generate consensus")

    lines.append("")
    lines.append(f"**Aggregation Method:** {aggregated_ranking.get('method', 'hybrid')}")
    lines.append(f"**Number of Peer Rankers:** {len(peer_rankings)}")
    lines.append("**AI Model:** GPT-4o (via LangChain)")
    lines.append("**Execution Mode:** Parallel (Stages 2 & 3)")

    if debate_triggered:
        debate_result = state.get("debate_result", {})
        # Extract statistics properly
        statistics = debate_result.get("statistics", {})
        rounds = debate_result.get("rounds", [])
        num_rounds = statistics.get("total_rounds", len(rounds))

        lines.append(f"**Debate Rounds:** {num_rounds}")
        lines.append(f"**Debate Model:** GPT-4o with temperature 0.7")

    return "\n".join(lines)


def _generate_execution_summary(state: Dict[str, Any]) -> str:
    """Generate execution summary."""
    stage_timings = state.get("stage_timings", {})

    # Calculate total duration
    total_duration = sum(stage_timings.values())

    # Calculate parallel efficiency
    presentation_time = stage_timings.get("presentations", 0)
    ranking_time = stage_timings.get("rankings", 0)
    sequential_time = sum(stage_timings.values())
    parallel_time = max(presentation_time, ranking_time)

    efficiency = sequential_time / parallel_time if parallel_time > 0 else 0

    lines = ["## Execution Summary", ""]
    lines.append(f"**Total Duration:** {total_duration:.2f} seconds")
    lines.append(f"**Parallel Efficiency:** {efficiency:.2f}x")

    # Add stage breakdown
    if stage_timings:
        lines.append("")
        lines.append("**Stage Timings:**")
        lines.append("")
        for stage, duration in sorted(stage_timings.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total_duration * 100) if total_duration > 0 else 0
            lines.append(f"- {stage.capitalize()}: {duration:.2f}s ({percentage:.1f}%)")

    lines.append("")
    lines.append("---")

    return "\n".join(lines)


def _generate_footer(workflow_type: str) -> str:
    """Generate report footer."""
    timestamp = datetime.now().isoformat()

    return f"""*This report was generated by the {workflow_type} Multi-Agent System*  
*Generated at: {timestamp}*
*Framework: LangGraph + LangChain + Async Parallel Execution*"""