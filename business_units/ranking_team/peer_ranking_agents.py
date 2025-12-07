"""
Ranking Team - Peer Ranking Agents (Phase 1)

Independent peer agents that evaluate and rank all country presentations.

Each peer:
1. Reviews all expert presentations
2. Ranks countries based on investment potential
3. Provides scores (0-10) and reasoning
4. Acts independently (different perspectives)

Multiple peers create diversity in rankings that gets aggregated later.
"""

import os
import logging
from typing import Dict, Any, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.registry.agent_registry import get_registry
from src.registry.agent_metadata import (
    AgentFramework,
    AgentCapability,
    create_peer_ranker_metadata
)

logger = logging.getLogger("PeerRankingAgents")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ============================================================================
# Configuration
# ============================================================================

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,  # Lower for consistent ranking
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_retries=3,
    request_timeout=120
)


# ============================================================================
# Output Structure
# ============================================================================

class CountryRanking(BaseModel):
    """Ranking for a single country."""

    country_code: str = Field(description="3-letter country code")
    rank: int = Field(description="Rank position (1 = best)", ge=1)
    score: float = Field(description="Score out of 10", ge=0, le=10)

    reasoning: str = Field(
        description="2-3 sentences explaining the ranking and score"
    )

    strengths_noted: List[str] = Field(
        description="Key strengths that influenced the ranking",
        max_items=3
    )

    concerns_noted: List[str] = Field(
        description="Key concerns that influenced the ranking",
        max_items=2
    )


class PeerRankingResult(BaseModel):
    """Complete ranking from one peer agent."""

    peer_id: str = Field(description="ID of peer ranker")

    rankings: List[CountryRanking] = Field(
        description="Ranked list of countries (sorted by rank)"
    )

    methodology: str = Field(
        description="Brief explanation of ranking approach"
    )

    top_choice_justification: str = Field(
        description="Why the #1 choice stands out"
    )


# ============================================================================
# Prompt Template
# ============================================================================

PEER_RANKER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an experienced renewable energy investment analyst (Peer Ranker #{ranker_id}).

Your task: Rank ALL countries based on their investment presentations.

Ranking Criteria (in priority order):
1. Financial viability (30%): Policy support, market conditions, returns
2. Resource quality (25%): Solar/wind resources, capacity factors
3. Risk profile (20%): Political stability, regulatory clarity, execution risk
4. Market opportunity (15%): Market size, growth potential, competition
5. Strategic positioning (10%): Technology access, supply chains, partnerships

Be objective and analytical. Consider:
- Strength of evidence in presentations
- Balance of opportunities vs. risks
- Realistic assessment of challenges
- Comparative advantages across countries

{format_instructions}
"""),
    ("user", """Review these country investment presentations and provide your independent ranking:

{presentations_text}

Rank ALL {num_countries} countries from best (#1) to worst (#{num_countries}).

Provide:
- Clear rank ordering (1 = best investment opportunity)
- Scores out of 10 for each country
- Reasoning for each ranking
- Top strengths and concerns for each country
- Justification for your #1 choice

Be decisive and justify your rankings with specific evidence from the presentations.""")
])


# ============================================================================
# Helper Functions
# ============================================================================

def format_presentations_for_ranking(
        presentations: Dict[str, Dict[str, Any]]
) -> str:
    """
    Format expert presentations into readable text for peer review.

    Args:
        presentations: Dict mapping country_code to presentation

    Returns:
        Formatted text with all presentations
    """
    formatted = ""

    for idx, (country_code, presentation) in enumerate(sorted(presentations.items()), 1):
        formatted += f"\n{'=' * 70}\n"
        formatted += f"COUNTRY {idx}: {country_code}\n"
        formatted += f"{'=' * 70}\n\n"

        # Executive Summary
        formatted += f"Executive Summary:\n{presentation.get('executive_summary', 'N/A')}\n\n"

        # Strengths
        strengths = presentation.get('strengths', [])
        if strengths:
            formatted += "Key Strengths:\n"
            for i, strength in enumerate(strengths, 1):
                formatted += f"  {i}. {strength}\n"
            formatted += "\n"

        # Opportunities
        opportunities = presentation.get('opportunities', [])
        if opportunities:
            formatted += "Opportunities:\n"
            for i, opp in enumerate(opportunities, 1):
                formatted += f"  {i}. {opp}\n"
            formatted += "\n"

        # Risks
        risks = presentation.get('risks', [])
        if risks:
            formatted += "Risks/Challenges:\n"
            for i, risk in enumerate(risks, 1):
                formatted += f"  {i}. {risk}\n"
            formatted += "\n"

        # Investment Case (abbreviated)
        investment_case = presentation.get('investment_case', '')
        if investment_case:
            # Truncate if too long
            case_preview = investment_case[:300] + "..." if len(investment_case) > 300 else investment_case
            formatted += f"Investment Case:\n{case_preview}\n\n"

        # Recommendation
        formatted += f"Expert Recommendation: {presentation.get('recommendation', 'N/A')}\n"
        formatted += f"Confidence: {presentation.get('confidence', 'N/A')}\n\n"

    return formatted


# ============================================================================
# Peer Ranker Agent Factory
# ============================================================================

def create_peer_ranker_agent(ranker_id: int):
    """
    Factory function to create a peer ranker agent.

    Args:
        ranker_id: Unique ID for this peer ranker (1, 2, 3, etc.)

    Returns:
        Callable peer ranker agent function

    Example:
        >>> peer_1 = create_peer_ranker_agent(ranker_id=1)
        >>> result = peer_1(state)
    """

    # Create output parser
    parser = PydanticOutputParser(pydantic_object=PeerRankingResult)

    # Create prompt with format instructions
    prompt = PEER_RANKER_PROMPT.partial(
        format_instructions=parser.get_format_instructions(),
        ranker_id=ranker_id
    )

    # Create chain
    chain = prompt | llm | parser

    def peer_ranker_agent(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Peer ranker agent that ranks all country presentations.

        Input (from state):
            - expert_presentations: Dict[country_code, presentation]
            - countries: List[str]

        Output (to state):
            - peer_rankings: List[ranking_result] (appends to list)
            - ranking_metadata: Metadata about ranking generation
        """

        start_time = datetime.now()

        logger.info("=" * 70)
        logger.info(f"PEER RANKER #{ranker_id} - Starting evaluation")
        logger.info("=" * 70)

        # Validate inputs
        presentations = state.get("expert_presentations", {})
        if not presentations:
            error = "No expert presentations available to rank"
            logger.error(error)
            return {
                "peer_rankings": [],
                "ranking_metadata": {
                    f"peer_{ranker_id}": {
                        "success": False,
                        "error": error
                    }
                }
            }

        countries = state.get("countries", [])
        num_countries = len(countries)

        # Check if all countries have presentations
        missing = [c for c in countries if c not in presentations]
        if missing:
            warning = f"Missing presentations for: {missing}"
            logger.warning(warning)

        logger.info(f"📊 Ranking {len(presentations)} countries")

        try:
            # Format presentations for review
            presentations_text = format_presentations_for_ranking(presentations)

            # Generate ranking
            logger.info(f"🤖 Peer #{ranker_id} analyzing presentations...")

            ranking_result = chain.invoke({
                "presentations_text": presentations_text,
                "num_countries": len(presentations)
            })

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Convert to dict
            ranking_dict = ranking_result.model_dump()
            ranking_dict["peer_id"] = f"peer_ranker_{ranker_id}"
            ranking_dict["timestamp"] = end_time.isoformat()
            ranking_dict["generation_time_seconds"] = round(duration, 2)

            # Sort rankings by rank to ensure order
            ranking_dict["rankings"] = sorted(
                ranking_dict["rankings"],
                key=lambda x: x["rank"]
            )

            logger.info(f"✅ Peer #{ranker_id} ranking complete")
            logger.info(f"   Top choice: {ranking_dict['rankings'][0]['country_code']}")
            logger.info(f"   Time: {duration:.2f}s")

            # Log full ranking
            logger.info(f"\n   Peer #{ranker_id} Rankings:")
            for r in ranking_dict["rankings"]:
                logger.info(f"      {r['rank']}. {r['country_code']} - Score: {r['score']}/10")

            return {
                "peer_rankings": [ranking_dict],  # List with single ranking
                "ranking_metadata": {
                    f"peer_{ranker_id}": {
                        "success": True,
                        "peer_id": f"peer_ranker_{ranker_id}",
                        "countries_ranked": len(ranking_dict["rankings"]),
                        "top_choice": ranking_dict["rankings"][0]["country_code"],
                        "generation_time_seconds": round(duration, 2),
                        "timestamp": end_time.isoformat(),
                        "model": "gpt-4o"
                    }
                }
            }

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(f"❌ Peer #{ranker_id} ranking failed: {str(e)}")

            return {
                "peer_rankings": [],
                "ranking_metadata": {
                    f"peer_{ranker_id}": {
                        "success": False,
                        "error": str(e),
                        "peer_id": f"peer_ranker_{ranker_id}",
                        "generation_time_seconds": round(duration, 2),
                        "timestamp": end_time.isoformat()
                    }
                }
            }

    return peer_ranker_agent


# ============================================================================
# Batch Peer Creation
# ============================================================================

def register_peer_rankers(
        num_peers: int = 3,
        registry=None
) -> Dict[int, callable]:
    """
    Register multiple peer ranker agents.

    Args:
        num_peers: Number of peer rankers to create
        registry: Agent registry (uses global if None)

    Returns:
        Dict mapping peer_id to peer agent function

    Example:
        >>> peers = register_peer_rankers(num_peers=5)
        >>> result_1 = peers[1](state)
    """

    if registry is None:
        registry = get_registry()

    peers = {}

    for peer_id in range(1, num_peers + 1):
        # Create metadata
        metadata = create_peer_ranker_metadata(ranker_id=peer_id)

        # Create agent
        peer = create_peer_ranker_agent(ranker_id=peer_id)

        # Register
        registry.register_agent(metadata, peer)

        peers[peer_id] = peer

        logger.info(f"✅ Registered peer ranker #{peer_id}: {metadata.agent_id}")

    return peers


# ============================================================================
# Parallel Execution Helper
# ============================================================================

async def execute_peer_rankers_parallel(
        state: Dict[str, Any],
        num_peers: int = 3
) -> Dict[str, Any]:
    """
    Execute multiple peer rankers in parallel.

    Args:
        state: Phase 1 state with expert presentations
        num_peers: Number of peer rankers to execute

    Returns:
        Combined results from all peer rankers

    Example:
        >>> result = await execute_peer_rankers_parallel(state, num_peers=5)
        >>> rankings = result["peer_rankings"]
    """
    import asyncio

    logger.info(f"🚀 Executing {num_peers} peer rankers in parallel...")

    # Create peer rankers
    peers = {
        peer_id: create_peer_ranker_agent(peer_id)
        for peer_id in range(1, num_peers + 1)
    }

    # Execute in parallel
    async def run_peer(peer_id: int, peer: callable):
        """Run peer ranker in async context."""
        import concurrent.futures
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, peer, state)

    tasks = [
        run_peer(peer_id, peer)
        for peer_id, peer in peers.items()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combine results
    all_rankings = []
    combined_metadata = {}
    errors = []

    for idx, result in enumerate(results):
        peer_id = idx + 1

        if isinstance(result, Exception):
            logger.error(f"❌ Peer #{peer_id} failed: {str(result)}")
            errors.append(f"peer_{peer_id}: {str(result)}")
            continue

        if "peer_rankings" in result and result["peer_rankings"]:
            all_rankings.extend(result["peer_rankings"])

        if "ranking_metadata" in result:
            combined_metadata.update(result["ranking_metadata"])

    logger.info(f"✅ Completed {len(all_rankings)}/{num_peers} peer rankings")

    return {
        "peer_rankings": all_rankings,
        "ranking_metadata": combined_metadata,
        "errors": errors
    }


# ============================================================================
# Module Setup
# ============================================================================

# Create business unit directory
os.makedirs("business_units/ranking_team", exist_ok=True)
with open("business_units/ranking_team/__init__.py", "w") as f:
    f.write("# Ranking Team - Peer Ranking Agents\n")

logger.info("✅ Peer Ranking Agent System Ready!")
logger.info("   👥 Multiple independent peer rankers")
logger.info("   🤖 GPT-4 powered comparative analysis")
logger.info("   ⚡ Parallel execution support")
logger.info("   📊 Structured ranking output")