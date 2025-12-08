"""
Hot Seat Debate Module - Phase 2

Enables peer rankers to challenge the initial aggregated ranking through structured debate.
When consensus is low or rankings are controversial, this module orchestrates a "hot seat"
where the top-ranked country's position is challenged and defended.

Key Features:
- Parallel debate execution with multiple challengers
- Structured challenge/defense format
- Scoring and verdict determination
- Integration with LangGraph workflow

Author: Kanauija
Date: 2024-12-08
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from openai import AsyncOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HotSeatDebate")

# Initialize OpenAI client
client = AsyncOpenAI()


class HotSeatDebate:
    """
    Orchestrates structured debates about country rankings.

    When consensus is low, this class enables peer rankers to challenge
    the top-ranked country's position through formal debate rounds.
    """

    def __init__(
            self,
            model: str = "gpt-4o",
            temperature: float = 0.7,
            max_retries: int = 3
    ):
        """
        Initialize the Hot Seat Debate system.

        Args:
            model: OpenAI model to use for debate agents
            temperature: Temperature for LLM responses (higher = more creative)
            max_retries: Maximum retry attempts for API calls
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries

        logger.info("Hot Seat Debate system initialized")
        logger.info(f"Model: {model}, Temperature: {temperature}")

    async def execute_debate(
            self,
            top_ranked_country: Dict[str, Any],
            runner_up_country: Dict[str, Any],
            expert_presentations: List[Dict[str, Any]],
            peer_rankings: List[Dict[str, Any]],
            num_challengers: int = 2
    ) -> Dict[str, Any]:
        """
        Execute a hot seat debate challenging the top-ranked country.

        Args:
            top_ranked_country: The #1 ranked country with metadata
            runner_up_country: The #2 ranked country with metadata
            expert_presentations: Original expert presentations
            peer_rankings: Original peer rankings
            num_challengers: Number of challenger agents (default 2)

        Returns:
            Dict containing:
                - debate_rounds: List of challenge/defense exchanges
                - verdict: "UPHELD" or "OVERTURNED"
                - final_recommendation: Updated ranking recommendation
                - challenger_scores: Scores from each challenger
                - execution_metadata: Timing and performance data
        """
        start_time = time.time()

        logger.info("=" * 70)
        logger.info("HOT SEAT DEBATE - STARTING")
        logger.info("=" * 70)
        logger.info(f"Defending: {top_ranked_country['country_code']}")
        logger.info(f"Challenging in favor of: {runner_up_country['country_code']}")
        logger.info(f"Number of challengers: {num_challengers}")

        # Execute debates in parallel
        debate_tasks = []
        for i in range(num_challengers):
            task = self._execute_single_debate(
                challenger_id=i + 1,
                top_ranked=top_ranked_country,
                runner_up=runner_up_country,
                expert_presentations=expert_presentations,
                peer_rankings=peer_rankings
            )
            debate_tasks.append(task)

        # Wait for all debates to complete
        logger.info(f"🚀 Executing {num_challengers} debate rounds in parallel...")
        debate_results = await asyncio.gather(*debate_tasks)

        # Analyze debate results and determine verdict
        verdict_result = self._determine_verdict(
            debate_results,
            top_ranked_country,
            runner_up_country
        )

        duration = time.time() - start_time

        result = {
            "debate_rounds": debate_results,
            "verdict": verdict_result["verdict"],
            "final_recommendation": verdict_result["recommendation"],
            "challenger_scores": verdict_result["scores"],
            "confidence_level": verdict_result["confidence"],
            "execution_metadata": {
                "num_challengers": num_challengers,
                "duration_seconds": round(duration, 2),
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }
        }

        logger.info("=" * 70)
        logger.info("HOT SEAT DEBATE - COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Verdict: {result['verdict']}")
        logger.info(f"Recommendation: {result['final_recommendation']}")
        logger.info(f"Duration: {duration:.2f}s")

        return result

    async def _execute_single_debate(
            self,
            challenger_id: int,
            top_ranked: Dict[str, Any],
            runner_up: Dict[str, Any],
            expert_presentations: List[Dict[str, Any]],
            peer_rankings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a single debate round with one challenger.

        Args:
            challenger_id: Unique ID for this challenger
            top_ranked: Top-ranked country data
            runner_up: Runner-up country data
            expert_presentations: Expert presentation data
            peer_rankings: Peer ranking data

        Returns:
            Dict containing challenge, defense, and scoring
        """
        start_time = time.time()

        logger.info("=" * 70)
        logger.info(f"DEBATE ROUND #{challenger_id}")
        logger.info("=" * 70)

        # Step 1: Generate challenge
        logger.info(f"🎯 Challenger #{challenger_id} building case...")
        challenge = await self._generate_challenge(
            challenger_id,
            top_ranked,
            runner_up,
            expert_presentations,
            peer_rankings
        )

        # Step 2: Generate defense
        logger.info(f"🛡️  Defender responding to Challenge #{challenger_id}...")
        defense = await self._generate_defense(
            challenger_id,
            top_ranked,
            challenge,
            expert_presentations,
            peer_rankings
        )

        # Step 3: Challenger scores the debate
        logger.info(f"⚖️  Challenger #{challenger_id} scoring the exchange...")
        score = await self._score_debate(
            challenger_id,
            challenge,
            defense,
            top_ranked,
            runner_up
        )

        duration = time.time() - start_time

        result = {
            "challenger_id": challenger_id,
            "challenge": challenge,
            "defense": defense,
            "score": score,
            "duration_seconds": round(duration, 2)
        }

        logger.info(f"✅ Debate Round #{challenger_id} complete")
        logger.info(f"   Score: {score['challenger_score']}/10 vs {score['defender_score']}/10")
        logger.info(f"   Winner: {score['winner']}")
        logger.info(f"   Duration: {duration:.2f}s")

        return result

    async def _generate_challenge(
            self,
            challenger_id: int,
            top_ranked: Dict[str, Any],
            runner_up: Dict[str, Any],
            expert_presentations: List[Dict[str, Any]],
            peer_rankings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a challenge arguing why runner-up should be ranked #1.

        Returns:
            Dict with main_argument, supporting_points, weaknesses_identified
        """
        # Find relevant presentations
        top_presentation = self._find_presentation(
            expert_presentations,
            top_ranked['country_code']
        )
        runner_up_presentation = self._find_presentation(
            expert_presentations,
            runner_up['country_code']
        )

        # Build prompt
        prompt = f"""You are Challenger #{challenger_id} in a formal debate about renewable energy investment rankings.

CURRENT RANKING (BEING CHALLENGED):
#1: {top_ranked['country_code']} - Score: {top_ranked.get('consensus_score', 'N/A')}/10
#2: {runner_up['country_code']} - Score: {runner_up.get('consensus_score', 'N/A')}/10

YOUR TASK:
Build a compelling argument for why {runner_up['country_code']} should be ranked #1 instead of {top_ranked['country_code']}.

EVIDENCE AVAILABLE:
Top Ranked ({top_ranked['country_code']}) Presentation:
{top_presentation.get('content', 'No presentation available')[:1000]}

Runner-Up ({runner_up['country_code']}) Presentation:
{runner_up_presentation.get('content', 'No presentation available')[:1000]}

Peer Rankings Summary:
- {top_ranked['country_code']} average score: {top_ranked.get('average_peer_score', 'N/A')}
- {runner_up['country_code']} average score: {runner_up.get('average_peer_score', 'N/A')}

INSTRUCTIONS:
1. Identify 3-5 key weaknesses in {top_ranked['country_code']}'s position
2. Highlight 3-5 superior strengths of {runner_up['country_code']}
3. Build a coherent argument with specific evidence
4. Be professional but assertive

Respond in JSON format:
{{
    "main_argument": "One paragraph summarizing your core argument",
    "supporting_points": [
        "Point 1 with specific evidence",
        "Point 2 with specific evidence",
        "Point 3 with specific evidence"
    ],
    "weaknesses_identified": [
        "Weakness 1 in top-ranked country",
        "Weakness 2 in top-ranked country"
    ],
    "strength_score": 8.5  // How strong is your case (0-10)
}}"""

        # Call OpenAI
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert debate challenger specializing in renewable energy investment analysis."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        # Parse response
        import json
        challenge_data = json.loads(response.choices[0].message.content)

        logger.info(f"   Challenge strength: {challenge_data.get('strength_score', 'N/A')}/10")

        return challenge_data

    async def _generate_defense(
            self,
            challenger_id: int,
            top_ranked: Dict[str, Any],
            challenge: Dict[str, Any],
            expert_presentations: List[Dict[str, Any]],
            peer_rankings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a defense of the top-ranked country's position.

        Returns:
            Dict with rebuttal, counter_arguments, reaffirmed_strengths
        """
        top_presentation = self._find_presentation(
            expert_presentations,
            top_ranked['country_code']
        )

        prompt = f"""You are the Defender in a formal debate about renewable energy investment rankings.

THE CHALLENGE AGAINST {top_ranked['country_code']} AS #1:
Main Argument: {challenge['main_argument']}

Supporting Points:
{chr(10).join(f"- {point}" for point in challenge['supporting_points'])}

Weaknesses Identified:
{chr(10).join(f"- {weakness}" for weakness in challenge['weaknesses_identified'])}

YOUR EVIDENCE:
{top_ranked['country_code']} Expert Presentation:
{top_presentation.get('content', 'No presentation available')[:1000]}

Ranking Data:
- Consensus Score: {top_ranked.get('consensus_score', 'N/A')}/10
- Average Peer Score: {top_ranked.get('average_peer_score', 'N/A')}/10
- Agreement Level: {top_ranked.get('agreement_level', 'N/A')}

YOUR TASK:
Defend {top_ranked['country_code']}'s #1 position by:
1. Directly rebutting each challenge point with evidence
2. Reaffirming the key strengths that earned #1 ranking
3. Addressing identified weaknesses with context/mitigation
4. Maintaining professional, evidence-based argumentation

Respond in JSON format:
{{
    "rebuttal": "One paragraph core rebuttal",
    "counter_arguments": [
        "Counter to point 1 with evidence",
        "Counter to point 2 with evidence",
        "Counter to point 3 with evidence"
    ],
    "reaffirmed_strengths": [
        "Key strength 1 with evidence",
        "Key strength 2 with evidence"
    ],
    "defense_strength": 8.0  // How strong is your defense (0-10)
}}"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert defender specializing in renewable energy investment analysis."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        import json
        defense_data = json.loads(response.choices[0].message.content)

        logger.info(f"   Defense strength: {defense_data.get('defense_strength', 'N/A')}/10")

        return defense_data

    async def _score_debate(
            self,
            challenger_id: int,
            challenge: Dict[str, Any],
            defense: Dict[str, Any],
            top_ranked: Dict[str, Any],
            runner_up: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score the debate round to determine winner.

        Returns:
            Dict with challenger_score, defender_score, winner, reasoning
        """
        prompt = f"""You are an impartial judge scoring a debate about renewable energy investment rankings.

DEBATE TOPIC: Should {runner_up['country_code']} be ranked #1 instead of {top_ranked['country_code']}?

CHALLENGER'S ARGUMENT (for {runner_up['country_code']}):
{challenge['main_argument']}

Key Points:
{chr(10).join(f"- {point}" for point in challenge['supporting_points'])}

DEFENDER'S ARGUMENT (for {top_ranked['country_code']}):
{defense['rebuttal']}

Counter Arguments:
{chr(10).join(f"- {arg}" for arg in defense['counter_arguments'])}

YOUR TASK:
Score both sides on:
1. Strength of evidence (40%)
2. Logic and coherence (30%)
3. Addressing opponent's points (30%)

Respond in JSON format:
{{
    "challenger_score": 7.5,  // Score 0-10
    "defender_score": 8.2,    // Score 0-10
    "winner": "DEFENDER",     // "CHALLENGER" or "DEFENDER"
    "reasoning": "Brief explanation of scoring",
    "confidence": "high"      // "high", "medium", or "low"
}}"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an impartial debate judge with expertise in investment analysis."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent scoring
            response_format={"type": "json_object"}
        )

        import json
        score_data = json.loads(response.choices[0].message.content)

        return score_data

    def _determine_verdict(
            self,
            debate_results: List[Dict[str, Any]],
            top_ranked: Dict[str, Any],
            runner_up: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze all debate rounds and determine final verdict.

        Returns:
            Dict with verdict, recommendation, scores, confidence
        """
        logger.info("=" * 70)
        logger.info("ANALYZING DEBATE RESULTS")
        logger.info("=" * 70)

        # Collect scores
        challenger_wins = 0
        defender_wins = 0
        total_challenger_score = 0
        total_defender_score = 0

        for result in debate_results:
            score = result['score']
            if score['winner'] == 'CHALLENGER':
                challenger_wins += 1
            else:
                defender_wins += 1

            total_challenger_score += score['challenger_score']
            total_defender_score += score['defender_score']

        num_debates = len(debate_results)
        avg_challenger_score = total_challenger_score / num_debates
        avg_defender_score = total_defender_score / num_debates

        logger.info(f"Challenger wins: {challenger_wins}/{num_debates}")
        logger.info(f"Defender wins: {defender_wins}/{num_debates}")
        logger.info(f"Avg challenger score: {avg_challenger_score:.2f}/10")
        logger.info(f"Avg defender score: {avg_defender_score:.2f}/10")

        # Determine verdict
        # Ranking is OVERTURNED if challengers win majority AND have higher avg score
        if challenger_wins > defender_wins and avg_challenger_score > avg_defender_score:
            verdict = "OVERTURNED"
            recommendation = f"Rank {runner_up['country_code']} as #1"
            confidence = "high" if challenger_wins >= num_debates * 0.7 else "medium"
        else:
            verdict = "UPHELD"
            recommendation = f"Maintain {top_ranked['country_code']} as #1"
            confidence = "high" if defender_wins >= num_debates * 0.7 else "medium"

        return {
            "verdict": verdict,
            "recommendation": recommendation,
            "scores": {
                "challenger_avg": round(avg_challenger_score, 2),
                "defender_avg": round(avg_defender_score, 2),
                "challenger_wins": challenger_wins,
                "defender_wins": defender_wins
            },
            "confidence": confidence
        }

    def _find_presentation(
            self,
            presentations: List[Dict[str, Any]],
            country_code: str
    ) -> Dict[str, Any]:
        """Helper to find presentation for a specific country."""
        for pres in presentations:
            if pres.get('country') == country_code:
                return pres
        return {}


# Convenience functions for use in LangGraph workflow

async def execute_hot_seat_debate(
        top_ranked_country: Dict[str, Any],
        runner_up_country: Dict[str, Any],
        expert_presentations: List[Dict[str, Any]],
        peer_rankings: List[Dict[str, Any]],
        num_challengers: int = 2,
        model: str = "gpt-4o"
) -> Dict[str, Any]:
    """
    Convenience function to execute a hot seat debate.

    Used by LangGraph workflow nodes.
    """
    debate_system = HotSeatDebate(model=model)

    result = await debate_system.execute_debate(
        top_ranked_country=top_ranked_country,
        runner_up_country=runner_up_country,
        expert_presentations=expert_presentations,
        peer_rankings=peer_rankings,
        num_challengers=num_challengers
    )

    return result


def should_trigger_debate(
        aggregated_ranking: Dict[str, Any],
        threshold: str = "medium"
) -> bool:
    """
    Determine if hot seat debate should be triggered based on consensus.

    Args:
        aggregated_ranking: Dict containing final_rankings and agreement levels
        threshold: Minimum agreement level to skip debate
                  ("very_high", "high", "medium", "low")

    Returns:
        True if debate should be triggered, False otherwise
    """
    # Extract final_rankings from dict
    if not aggregated_ranking or not isinstance(aggregated_ranking, dict):
        logger.info("Debate trigger check: No valid aggregated ranking")
        return False

    final_rankings = aggregated_ranking.get("final_rankings", [])

    if not final_rankings or len(final_rankings) < 2:
        logger.info("Debate trigger check: Need at least 2 countries")
        return False

    top_country = final_rankings[0]
    agreement = top_country.get('agreement_level', 'unknown')

    # Define thresholds
    thresholds = {
        "very_high": ["very_high"],
        "high": ["very_high", "high"],
        "medium": ["very_high", "high", "medium"],
        "low": ["very_high", "high", "medium", "low"]
    }

    skip_debate = agreement in thresholds.get(threshold, [])

    logger.info(f"Debate trigger check: agreement={agreement}, threshold={threshold}")
    logger.info(f"Trigger debate: {not skip_debate}")

    return not skip_debate