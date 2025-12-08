"""
Expert Team - Country Investment Expert Agents (Phase 1)

Each country gets a dedicated expert agent that:
1. Reads country research data
2. Analyzes investment potential
3. Builds compelling presentation
4. Provides structured recommendations

UPDATED: Refactored to use AzureChatOpenAI instead of ChatOpenAI
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.registry.agent_registry import get_registry
from src.registry.agent_metadata import (
    AgentFramework,
    AgentCapability,
    create_expert_metadata
)

logger = logging.getLogger("ExpertAgents")
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

# Azure OpenAI Configuration
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "https://sparkapi.spglobal.com/v1/sparkassist")
AZURE_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT", "gpt-4o-mini")
AZURE_API_VERSION = os.environ.get("AZURE_API_VERSION", "2024-02-01")

llm = AzureChatOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    azure_deployment=AZURE_DEPLOYMENT,
    openai_api_version=AZURE_API_VERSION,
    api_key=AZURE_OPENAI_KEY,
    temperature=0.7,  # Higher for creative presentation
    max_retries=3,
    request_timeout=120
)


# ============================================================================
# Output Structure
# ============================================================================

class CountryPresentation(BaseModel):
    """Structured output from expert agent."""

    country_code: str = Field(description="3-letter country code (e.g., USA)")

    executive_summary: str = Field(
        description="2-3 sentence compelling summary of investment opportunity"
    )

    strengths: list[str] = Field(
        description="3-5 key investment strengths",
        min_items=3,
        max_items=5
    )

    opportunities: list[str] = Field(
        description="2-3 specific opportunities or growth areas",
        min_items=2,
        max_items=3
    )

    risks: list[str] = Field(
        description="2-3 key risks or challenges",
        min_items=2,
        max_items=3
    )

    investment_case: str = Field(
        description="Detailed 3-4 paragraph narrative making the investment case"
    )

    recommendation: str = Field(
        description="Investment recommendation: STRONG_BUY, BUY, HOLD, or AVOID"
    )

    confidence: str = Field(
        description="Confidence level: high, medium, or low"
    )

    key_metrics_summary: str = Field(
        description="Summary of most important metrics and data points"
    )


# ============================================================================
# Prompt Template
# ============================================================================

EXPERT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert renewable energy investment analyst specializing in {country_code}.

Your role is to build the STRONGEST POSSIBLE investment case for {country_code} based on the research provided.

You will compete with other country experts, so make your presentation:
- Compelling and data-driven
- Focused on unique advantages
- Honest about risks but emphasizing opportunities
- Professionally written
- Backed by specific examples from the research

{format_instructions}
"""),
    ("user", """Country: {country_code}

Research Data:
{research_text}

Build a compelling investment presentation for {country_code} that:
1. Highlights unique strengths and competitive advantages
2. Identifies specific opportunities
3. Acknowledges risks honestly but constructively
4. Makes a clear investment recommendation
5. Uses specific examples and data from the research

Make this the BEST case possible for investing in {country_code}'s renewable energy sector.""")
])


# ============================================================================
# Expert Agent Factory
# ============================================================================

def create_expert_agent(country_code: str, expert_id: int = 1):
    """
    Factory function to create an expert agent for a specific country.

    Args:
        country_code: 3-letter country code (e.g., "USA")
        expert_id: Expert ID number (default: 1)

    Returns:
        Callable expert agent function

    Example:
        >>> usa_expert = create_expert_agent("USA", expert_id=1)
        >>> result = usa_expert(state)
    """

    # Create output parser
    parser = PydanticOutputParser(pydantic_object=CountryPresentation)

    # Create prompt with format instructions
    prompt = EXPERT_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    )

    # Create chain
    chain = prompt | llm | parser

    def expert_agent(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expert agent that builds presentation for assigned country.

        Input (from state):
            - country_research: Dict[country_code, research_text]
            - countries: List[str] (to verify country is included)

        Output (to state):
            - expert_presentations: Dict[country_code, presentation]
            - presentation_metadata: Metadata about generation
        """

        start_time = datetime.now()

        logger.info("=" * 70)
        logger.info(f"EXPERT AGENT - {country_code} Expert #{expert_id}")
        logger.info("=" * 70)

        # Validate inputs
        countries = state.get("countries", [])
        if country_code not in countries:
            error = f"Country {country_code} not in analysis scope: {countries}"
            logger.error(error)
            return {
                "expert_presentations": {},
                "presentation_metadata": {
                    country_code: {
                        "error": error,
                        "success": False
                    }
                }
            }

        country_research = state.get("country_research", {})
        if country_code not in country_research:
            error = f"No research data available for {country_code}"
            logger.error(error)
            return {
                "expert_presentations": {},
                "presentation_metadata": {
                    country_code: {
                        "error": error,
                        "success": False
                    }
                }
            }

        research_text = country_research[country_code]

        logger.info(f"📊 Building presentation for {country_code}")
        logger.info(f"   Research length: {len(research_text)} chars")

        try:
            # Generate presentation
            presentation = chain.invoke({
                "country_code": country_code,
                "research_text": research_text
            })

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Convert to dict and add metadata
            presentation_dict = presentation.dict()
            presentation_dict["expert_id"] = f"expert_{country_code.lower()}_{expert_id}"
            presentation_dict["generated_at"] = end_time.isoformat()
            presentation_dict["generation_time_seconds"] = round(duration, 2)

            logger.info(f"✅ Presentation complete for {country_code}")
            logger.info(f"   Recommendation: {presentation.recommendation}")
            logger.info(f"   Confidence: {presentation.confidence}")
            logger.info(f"   Strengths: {len(presentation.strengths)}")
            logger.info(f"   Time: {duration:.2f}s")

            return {
                "expert_presentations": {
                    country_code: presentation_dict
                },
                "presentation_metadata": {
                    country_code: {
                        "success": True,
                        "expert_id": f"expert_{country_code.lower()}_{expert_id}",
                        "generation_time_seconds": round(duration, 2),
                        "timestamp": end_time.isoformat(),
                        "model": AZURE_DEPLOYMENT,
                        "azure_endpoint": AZURE_ENDPOINT,
                        "research_length": len(research_text)
                    }
                }
            }

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(f"❌ Failed to generate presentation for {country_code}: {str(e)}")

            return {
                "expert_presentations": {},
                "presentation_metadata": {
                    country_code: {
                        "success": False,
                        "error": str(e),
                        "expert_id": f"expert_{country_code.lower()}_{expert_id}",
                        "generation_time_seconds": round(duration, 2),
                        "timestamp": end_time.isoformat()
                    }
                }
            }

    return expert_agent


# ============================================================================
# Batch Expert Creation
# ============================================================================

def register_experts_for_countries(
    countries: list[str],
    registry=None
) -> Dict[str, callable]:
    """
    Register expert agents for multiple countries.

    Args:
        countries: List of country codes
        registry: Agent registry (uses global if None)

    Returns:
        Dict mapping country_code to expert agent function

    Example:
        >>> experts = register_experts_for_countries(["USA", "IND", "CHN"])
        >>> usa_result = experts["USA"](state)
    """

    if registry is None:
        registry = get_registry()

    experts = {}

    for country_code in countries:
        # Create metadata
        metadata = create_expert_metadata(country_code, expert_id=1)

        # Create agent
        expert = create_expert_agent(country_code, expert_id=1)

        # Register
        registry.register_agent(metadata, expert)

        experts[country_code] = expert

        logger.info(f"✅ Registered expert for {country_code}: {metadata.agent_id}")

    return experts


# ============================================================================
# Parallel Execution Helper
# ============================================================================

async def execute_experts_parallel(
    state: Dict[str, Any],
    countries: Optional[list[str]] = None
) -> Dict[str, Any]:
    """
    Execute all expert agents in parallel.

    Args:
        state: Phase 1 state
        countries: List of countries (uses state['countries'] if None)

    Returns:
        Combined results from all experts

    Example:
        >>> result = await execute_experts_parallel(state)
        >>> presentations = result["expert_presentations"]
    """
    import asyncio

    if countries is None:
        countries = state.get("countries", [])

    logger.info(f"🚀 Executing {len(countries)} expert agents in parallel...")

    # Create experts
    experts = {
        country: create_expert_agent(country, expert_id=1)
        for country in countries
    }

    # Execute in parallel
    async def run_expert(country: str, expert: callable):
        """Run expert in async context."""
        import concurrent.futures
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, expert, state)

    tasks = [
        run_expert(country, expert)
        for country, expert in experts.items()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combine results
    combined_presentations = {}
    combined_metadata = {}
    errors = []

    for idx, result in enumerate(results):
        country = countries[idx]

        if isinstance(result, Exception):
            logger.error(f"❌ Expert for {country} failed: {str(result)}")
            errors.append(f"{country}: {str(result)}")
            continue

        if "expert_presentations" in result:
            combined_presentations.update(result["expert_presentations"])

        if "presentation_metadata" in result:
            combined_metadata.update(result["presentation_metadata"])

    logger.info(f"✅ Completed {len(combined_presentations)}/{len(countries)} presentations")

    return {
        "expert_presentations": combined_presentations,
        "presentation_metadata": combined_metadata,
        "errors": errors
    }