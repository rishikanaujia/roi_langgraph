"""
Agent Metadata - Defines agent types and metadata structure.

PHASE 1 EXTENSIONS:
- Added EXPERT_PRESENTATION capability
- Added PEER_RANKING capability
- Added AGGREGATION capability

This allows business units to describe their agents in a standardized way.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AgentFramework(str, Enum):
    """Supported agent frameworks."""
    LANGCHAIN = "langchain"
    LANGGRAPH = "langgraph"
    CUSTOM = "custom"


class AgentCapability(str, Enum):
    """
    Agent capabilities (what the agent can do).

    PHASE 1 CAPABILITIES:
    - RESEARCH: Load/compile country research data
    - EXPERT_PRESENTATION: Build compelling case for ONE country
    - PEER_RANKING: Rank ALL country presentations
    - AGGREGATION: Combine multiple peer rankings

    PHASE 2 CAPABILITIES (future):
    - CHALLENGE: Question weak presentations
    - HOT_SEAT_DEFENSE: Defend country under scrutiny
    - VERIFICATION: Validate rankings
    """
    # Data collection
    RESEARCH = "research"
    DATA_FETCH = "data_fetch"

    # Phase 1 - Initial Rankings
    EXPERT_PRESENTATION = "expert_presentation"  # NEW
    PEER_RANKING = "peer_ranking"  # NEW
    AGGREGATION = "aggregation"  # NEW

    # Analysis
    ANALYSIS = "analysis"
    RANKING = "ranking"
    VERIFICATION = "verification"

    # Output
    REPORT_GEN = "report_generation"

    # Phase 2 - Hot Seat (future)
    CHALLENGE = "challenge"  # Future
    HOT_SEAT_DEFENSE = "hot_seat_defense"  # Future
    DECISION_MAKING = "decision_making"


class AgentMetadata(BaseModel):
    """
    Metadata describing an agent.

    Business units fill this out when registering their agents.
    """

    # Identity
    agent_id: str = Field(description="Unique identifier for the agent")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="What this agent does")

    # Technical details
    framework: AgentFramework = Field(description="Framework used to build agent")
    capabilities: List[AgentCapability] = Field(description="What the agent can do")

    # Ownership
    business_unit: str = Field(description="Which team owns this agent")
    contact: str = Field(description="Contact person/email")
    version: str = Field(default="1.0.0", description="Agent version")

    # Input/Output specification
    required_inputs: List[str] = Field(
        description="State keys this agent needs",
        default_factory=list
    )
    output_keys: List[str] = Field(
        description="State keys this agent produces",
        default_factory=list
    )

    # Configuration
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific configuration"
    )

    # Execution
    dependencies: List[str] = Field(
        default_factory=list,
        description="Other agents this depends on (agent_ids)"
    )
    timeout_seconds: int = Field(default=300, description="Max execution time")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Search tags")
    enabled: bool = Field(default=True, description="Is agent active?")


class AgentExecutionResult(BaseModel):
    """Result from agent execution."""

    agent_id: str
    success: bool
    outputs: Dict[str, Any]
    error: Optional[str] = None
    execution_time_seconds: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Example Metadata Instances for Phase 1
# ============================================================================

RESEARCH_LOADER_METADATA = AgentMetadata(
    agent_id="research_loader_v1",
    name="Research Data Loader",
    description="Loads pre-researched country information from JSON",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.RESEARCH],
    business_unit="data_team",
    contact="data@company.com",
    required_inputs=[],  # Optional: countries, research_json_path
    output_keys=["country_research", "research_metadata"],
    tags=["research", "json", "loader", "phase1"]
)

EXPERT_AGENT_METADATA = AgentMetadata(
    agent_id="expert_agent_template",
    name="Country Expert Agent",
    description="Builds compelling investment case for assigned country",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.EXPERT_PRESENTATION],
    business_unit="expert_team",
    contact="experts@company.com",
    required_inputs=["country_research", "country_code"],
    output_keys=["expert_presentations"],
    tags=["expert", "presentation", "gpt4", "phase1"]
)

PEER_RANKER_METADATA = AgentMetadata(
    agent_id="peer_ranker_template",
    name="Peer Ranking Agent",
    description="Ranks all country presentations independently",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.PEER_RANKING],
    business_unit="ranking_team",
    contact="ranking@company.com",
    required_inputs=["expert_presentations"],
    output_keys=["peer_rankings"],
    tags=["ranking", "peer", "gpt4", "phase1"]
)

AGGREGATOR_METADATA = AgentMetadata(
    agent_id="ranking_aggregator_v1",
    name="Ranking Aggregator",
    description="Combines multiple peer rankings into consensus ranking",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.AGGREGATION],
    business_unit="ranking_team",
    contact="ranking@company.com",
    required_inputs=["peer_rankings", "expert_presentations"],
    output_keys=["aggregated_ranking", "consensus_scores"],
    tags=["aggregation", "consensus", "phase1"]
)


# ============================================================================
# Helper Functions
# ============================================================================

def create_expert_metadata(
        country_code: str,
        expert_id: int = 1
) -> AgentMetadata:
    """
    Factory function to create expert agent metadata for a country.

    Usage:
        usa_expert = create_expert_metadata("USA", expert_id=1)
    """
    return AgentMetadata(
        agent_id=f"expert_{country_code.lower()}_{expert_id}",
        name=f"{country_code} Investment Expert #{expert_id}",
        description=f"Builds investment case for {country_code}",
        framework=AgentFramework.LANGCHAIN,
        capabilities=[AgentCapability.EXPERT_PRESENTATION],
        business_unit="expert_team",
        contact="experts@company.com",
        version="1.0.0",
        required_inputs=["country_research", "country_reports"],
        output_keys=["expert_presentations"],
        config={"assigned_country": country_code},
        tags=["expert", "presentation", country_code.lower(), "phase1"]
    )


def create_peer_ranker_metadata(
        ranker_id: int
) -> AgentMetadata:
    """
    Factory function to create peer ranker metadata.

    Usage:
        peer_1 = create_peer_ranker_metadata(ranker_id=1)
    """
    return AgentMetadata(
        agent_id=f"peer_ranker_{ranker_id}",
        name=f"Peer Ranker #{ranker_id}",
        description=f"Independent ranking agent (Peer {ranker_id})",
        framework=AgentFramework.LANGCHAIN,
        capabilities=[AgentCapability.PEER_RANKING],
        business_unit="ranking_team",
        contact="ranking@company.com",
        version="1.0.0",
        required_inputs=["expert_presentations", "countries"],
        output_keys=["peer_rankings"],
        config={"ranker_id": ranker_id},
        tags=["peer", "ranking", f"peer_{ranker_id}", "phase1"]
    )


# ============================================================================
# Validation
# ============================================================================

def validate_phase1_agent(metadata: AgentMetadata) -> bool:
    """
    Validate that agent metadata is properly configured for Phase 1.

    Checks:
    - Has required Phase 1 capabilities
    - Has required inputs/outputs
    - Has proper tags
    """
    phase1_capabilities = {
        AgentCapability.RESEARCH,
        AgentCapability.EXPERT_PRESENTATION,
        AgentCapability.PEER_RANKING,
        AgentCapability.AGGREGATION
    }

    # Check if agent has Phase 1 capabilities
    has_phase1_capability = any(
        cap in phase1_capabilities
        for cap in metadata.capabilities
    )

    if not has_phase1_capability:
        return False

    # Validate required fields
    if not metadata.agent_id or not metadata.name:
        return False

    # Validate inputs/outputs are specified
    if not metadata.required_inputs and not metadata.output_keys:
        # At least one should be specified
        return False

    return True