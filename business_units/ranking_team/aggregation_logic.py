"""
Ranking Team - Aggregation Logic (Phase 1)

Combines multiple peer rankings into a single consensus ranking.

Methods:
1. Borda Count: Converts ranks to points
2. Average Scoring: Mean of peer scores
3. Rank-based: Median of rank positions

Also calculates:
- Score variance (agreement level)
- Peer consensus metrics
- Tie-breaking logic

Author: Kanauija
Date: 2024-12-08
Updated: 2024-12-08 - Flattened agreement_level fields for easier access
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from statistics import mean, median, stdev
from collections import defaultdict

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import (
    AgentFramework,
    AgentCapability
)

logger = logging.getLogger("AggregationLogic")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Aggregation Methods
# ============================================================================

def calculate_borda_count(
        peer_rankings: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Calculate Borda count scores for each country.

    Borda count: If there are N countries, rank 1 gets N points,
    rank 2 gets N-1 points, etc.

    Args:
        peer_rankings: List of rankings from each peer

    Returns:
        Dict mapping country_code to total Borda points
    """
    borda_scores = defaultdict(float)

    # Get number of countries
    if not peer_rankings:
        return {}

    num_countries = len(peer_rankings[0]['rankings'])

    for peer_ranking in peer_rankings:
        for country_rank in peer_ranking['rankings']:
            country_code = country_rank['country_code']
            rank = country_rank['rank']

            # Borda points: N - rank + 1
            points = num_countries - rank + 1
            borda_scores[country_code] += points

    return dict(borda_scores)


def calculate_average_scores(
        peer_rankings: List[Dict[str, Any]]
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate average scores and standard deviation for each country.

    Args:
        peer_rankings: List of rankings from each peer

    Returns:
        Dict mapping country_code to (mean_score, stddev)
    """
    country_scores = defaultdict(list)

    for peer_ranking in peer_rankings:
        for country_rank in peer_ranking['rankings']:
            country_code = country_rank['country_code']
            score = country_rank['score']
            country_scores[country_code].append(score)

    # Calculate mean and stddev
    result = {}
    for country_code, scores in country_scores.items():
        avg_score = mean(scores)
        std = stdev(scores) if len(scores) > 1 else 0.0
        result[country_code] = (avg_score, std)

    return result


def calculate_median_ranks(
        peer_rankings: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Calculate median rank position for each country.

    Args:
        peer_rankings: List of rankings from each peer

    Returns:
        Dict mapping country_code to median rank
    """
    country_ranks = defaultdict(list)

    for peer_ranking in peer_rankings:
        for country_rank in peer_ranking['rankings']:
            country_code = country_rank['country_code']
            rank = country_rank['rank']
            country_ranks[country_code].append(rank)

    # Calculate median
    result = {}
    for country_code, ranks in country_ranks.items():
        result[country_code] = median(ranks)

    return result


def calculate_peer_agreement(
        peer_rankings: List[Dict[str, Any]],
        country_code: str
) -> Dict[str, Any]:
    """
    Calculate agreement metrics for a specific country.

    Args:
        peer_rankings: List of rankings from each peer
        country_code: Country to analyze

    Returns:
        Dict with agreement metrics
    """
    ranks = []
    scores = []

    for peer_ranking in peer_rankings:
        for country_rank in peer_ranking['rankings']:
            if country_rank['country_code'] == country_code:
                ranks.append(country_rank['rank'])
                scores.append(country_rank['score'])

    if not ranks:
        return {
            "agreement_level": "unknown",
            "rank_variance": 0,
            "score_variance": 0
        }

    # Calculate variance
    rank_var = stdev(ranks) if len(ranks) > 1 else 0.0
    score_var = stdev(scores) if len(scores) > 1 else 0.0

    # Classify agreement based on rank variance
    if rank_var <= 0.5:
        agreement = "very_high"
    elif rank_var <= 1.0:
        agreement = "high"
    elif rank_var <= 1.5:
        agreement = "medium"
    else:
        agreement = "low"

    return {
        "agreement_level": agreement,
        "rank_variance": round(rank_var, 2),
        "score_variance": round(score_var, 2),
        "rank_range": (min(ranks), max(ranks)),
        "score_range": (round(min(scores), 2), round(max(scores), 2))
    }


# ============================================================================
# Main Aggregation Function
# ============================================================================

def aggregate_peer_rankings(
        peer_rankings: List[Dict[str, Any]],
        method: str = "hybrid"
) -> Dict[str, Any]:
    """
    Aggregate multiple peer rankings into consensus ranking.

    Args:
        peer_rankings: List of rankings from each peer
        method: Aggregation method ("borda", "average", "median", "hybrid")

    Returns:
        Dict with aggregated ranking results
    """

    if not peer_rankings:
        logger.warning("No peer rankings to aggregate")
        return {
            "final_rankings": [],
            "method": method,
            "error": "No peer rankings provided"
        }

    logger.info(f"Aggregating {len(peer_rankings)} peer rankings using '{method}' method")

    # Get all countries
    countries = set()
    for peer_ranking in peer_rankings:
        for country_rank in peer_ranking['rankings']:
            countries.add(country_rank['country_code'])

    countries = sorted(list(countries))

    logger.info(f"Found {len(countries)} countries to rank")

    # Calculate different metrics
    borda_scores = calculate_borda_count(peer_rankings)
    average_scores = calculate_average_scores(peer_rankings)
    median_ranks = calculate_median_ranks(peer_rankings)

    # Build country results
    country_results = []

    for country_code in countries:
        # Get peer agreement
        agreement = calculate_peer_agreement(peer_rankings, country_code)

        # Get all peer scores and positions for this country
        peer_scores = []
        peer_positions = []

        for peer_ranking in peer_rankings:
            for country_rank in peer_ranking['rankings']:
                if country_rank['country_code'] == country_code:
                    peer_scores.append(country_rank['score'])
                    peer_positions.append(country_rank['rank'])

        result = {
            "country_code": country_code,
            "borda_points": borda_scores.get(country_code, 0),
            "average_score": average_scores[country_code][0],
            "score_stddev": average_scores[country_code][1],
            "median_rank": median_ranks.get(country_code, 0),
            "peer_scores": peer_scores,
            "peer_positions": peer_positions,
            "peer_agreement": agreement
        }

        # Calculate final score based on method
        if method == "borda":
            result["final_score"] = borda_scores.get(country_code, 0)
        elif method == "average":
            result["final_score"] = average_scores[country_code][0]
        elif method == "median":
            result["final_score"] = 10 - median_ranks.get(country_code, 0)  # Convert rank to score
        else:  # hybrid (default)
            # Combine Borda and average score
            borda_normalized = borda_scores.get(country_code, 0) / len(peer_rankings)
            avg_score = average_scores[country_code][0]
            result["final_score"] = (borda_normalized + avg_score) / 2

        country_results.append(result)

    # Sort by final score (descending)
    country_results.sort(key=lambda x: x["final_score"], reverse=True)

    # Assign final ranks
    final_rankings = []
    for idx, result in enumerate(country_results, 1):
        # Get peer agreement metrics
        peer_agreement = result["peer_agreement"]

        final_rankings.append({
            "rank": idx,
            "country_code": result["country_code"],
            "consensus_score": round(result["final_score"], 2),
            "average_peer_score": round(result["average_score"], 2),
            "score_stddev": round(result["score_stddev"], 2),
            "borda_points": result["borda_points"],
            "median_rank": result["median_rank"],
            "peer_scores": result["peer_scores"],
            "peer_positions": result["peer_positions"],
            # ✅ Flatten peer_agreement fields to top level for easier access
            "agreement_level": peer_agreement["agreement_level"],
            "rank_variance": peer_agreement["rank_variance"],
            "score_variance": peer_agreement["score_variance"],
            "rank_range": peer_agreement["rank_range"],
            "score_range": peer_agreement["score_range"],
            # Keep the full structure too for backward compatibility
            "peer_agreement": peer_agreement
        })

    logger.info(f"Aggregation complete - Final ranking:")
    for ranking in final_rankings:
        logger.info(
            f"  {ranking['rank']}. {ranking['country_code']} - "
            f"Score: {ranking['consensus_score']}/10 "
            f"(Agreement: {ranking['agreement_level']})"
        )

    return {
        "final_rankings": final_rankings,
        "method": method,
        "num_peers": len(peer_rankings),
        "num_countries": len(countries),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Registered Agent
# ============================================================================

@register_agent(
    agent_id="ranking_team_aggregator_phase1_v1",
    name="Ranking Aggregator (Phase 1)",
    description="Aggregates multiple peer rankings into consensus ranking using Borda count and scoring",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.AGGREGATION],
    business_unit="ranking_team",
    contact="ranking@company.com",
    version="1.0.0",
    required_inputs=["peer_rankings"],
    output_keys=["aggregated_ranking", "consensus_scores", "score_variance"],
    tags=["aggregation", "consensus", "borda", "phase1"]
)
def ranking_aggregator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate peer rankings into final consensus ranking.

    Input (from state):
        - peer_rankings: List[Dict] - Rankings from each peer
        - aggregation_method: str (optional) - Method to use

    Output (to state):
        - aggregated_ranking: Dict - Final consensus ranking
        - consensus_scores: Dict[country_code, score]
        - score_variance: Dict[country_code, variance]
        - aggregation_metadata: Dict - Aggregation statistics
    """

    start_time = datetime.now()

    logger.info("=" * 70)
    logger.info("RANKING AGGREGATOR - Starting")
    logger.info("=" * 70)

    # Get inputs
    peer_rankings = state.get("peer_rankings", [])
    method = state.get("aggregation_method", "hybrid")

    if not peer_rankings:
        error = "No peer rankings available to aggregate"
        logger.error(error)
        return {
            "aggregated_ranking": {},
            "consensus_scores": {},
            "score_variance": {},
            "aggregation_metadata": {
                "success": False,
                "error": error
            }
        }

    logger.info(f"Aggregating {len(peer_rankings)} peer rankings")

    try:
        # Perform aggregation
        result = aggregate_peer_rankings(peer_rankings, method=method)

        # Extract consensus scores and variances
        consensus_scores = {
            r["country_code"]: r["consensus_score"]
            for r in result["final_rankings"]
        }

        score_variance = {
            r["country_code"]: r["score_stddev"]
            for r in result["final_rankings"]
        }

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Create metadata
        metadata = {
            "success": True,
            "method": method,
            "num_peers": len(peer_rankings),
            "num_countries": len(consensus_scores),
            "aggregation_time_seconds": round(duration, 2),
            "timestamp": end_time.isoformat(),
            "top_choice": result["final_rankings"][0]["country_code"] if result["final_rankings"] else None,
            "average_agreement": round(
                mean([
                    r["rank_variance"]
                    for r in result["final_rankings"]
                ]), 2
            )
        }

        logger.info("=" * 70)
        logger.info("✅ AGGREGATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Top choice: {metadata['top_choice']}")
        logger.info(f"Average peer agreement: {metadata['average_agreement']} (lower = better)")
        logger.info(f"Time: {duration:.2f}s")

        return {
            "aggregated_ranking": result,
            "consensus_scores": consensus_scores,
            "score_variance": score_variance,
            "aggregation_metadata": metadata
        }

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.error(f"❌ Aggregation failed: {str(e)}")

        return {
            "aggregated_ranking": {},
            "consensus_scores": {},
            "score_variance": {},
            "aggregation_metadata": {
                "success": False,
                "error": str(e),
                "aggregation_time_seconds": round(duration, 2),
                "timestamp": end_time.isoformat()
            }
        }