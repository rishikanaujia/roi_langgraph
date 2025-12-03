"""
Ranking Team Agents

Example: How the Ranking Team can integrate their custom agents.
"""

from typing import Dict, Any
from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability


# ============ EXAMPLE 1: Custom Python Function ============

@register_agent(
    agent_id="ranking_team_simple_ranker_v1",
    name="Simple Ranker",
    description="Ranks countries by IRR (no AI)",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.RANKING],
    business_unit="ranking_team",
    contact="ranking@company.com",
    required_inputs=["country_reports"],
    output_keys=["ranking"]
)
def simple_ranker(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple ranking by IRR.

    This is a custom Python function - no framework needed!
    Just takes state dict and returns state dict.
    """
    country_reports = state.get("country_reports", {})

    # Sort by IRR
    sorted_countries = sorted(
        country_reports.items(),
        key=lambda x: x[1].get("aggregate_metrics", {}).get("average_irr", 0),
        reverse=True
    )

    # Create ranking
    ranking = {
        "ranked_countries": [
            {
                "rank": i + 1,
                "country_code": code,
                "country_name": report.get("country_name", code),
                "overall_score": report.get("aggregate_metrics", {}).get("average_irr", 0) * 10,
                "justification": f"IRR: {report.get('aggregate_metrics', {}).get('average_irr', 0):.2f}%"
            }
            for i, (code, report) in enumerate(sorted_countries)
        ],
        "methodology": "Ranked by average IRR"
    }

    return {"ranking": ranking}


# ============ EXAMPLE 2: Custom Class-Based Agent ============

class WeightedRankingAgent:
    """
    More sophisticated ranking with weighted criteria.

    This shows you can use classes too!
    """

    def __init__(self, weights: Dict[str, float]):
        self.weights = weights

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Make it callable so it works with our system."""
        country_reports = state.get("country_reports", {})

        # Calculate weighted scores
        scored_countries = []
        for code, report in country_reports.items():
            metrics = report.get("aggregate_metrics", {})

            score = (
                    metrics.get("average_irr", 0) * self.weights.get("irr", 0.4) +
                    (100 - metrics.get("average_lcoe", 100)) * self.weights.get("lcoe", 0.3) +
                    (metrics.get("average_npv", 0) / 1000000) * self.weights.get("npv", 0.3)
            )

            scored_countries.append({
                "rank": 0,  # Will be filled
                "country_code": code,
                "country_name": report.get("country_name", code),
                "overall_score": score,
                "justification": f"Weighted score using IRR ({self.weights['irr'] * 100}%), "
                                 f"LCOE ({self.weights['lcoe'] * 100}%), "
                                 f"NPV ({self.weights['npv'] * 100}%)"
            })

        # Sort and assign ranks
        scored_countries.sort(key=lambda x: x["overall_score"], reverse=True)
        for i, country in enumerate(scored_countries):
            country["rank"] = i + 1

        return {
            "ranking": {
                "ranked_countries": scored_countries,
                "methodology": f"Weighted scoring: {self.weights}"
            }
        }


# Register the class-based agent
weighted_ranker = WeightedRankingAgent(weights={"irr": 0.4, "lcoe": 0.3, "npv": 0.3})

register_agent(
    agent_id="ranking_team_weighted_ranker_v1",
    name="Weighted Ranker",
    description="Ranks countries using weighted criteria (IRR, LCOE, NPV)",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.RANKING],
    business_unit="ranking_team",
    contact="ranking@company.com",
    required_inputs=["country_reports"],
    output_keys=["ranking"]
)(weighted_ranker)

print("✅ Ranking Team agents registered!")