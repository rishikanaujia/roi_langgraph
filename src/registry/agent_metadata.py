"""
Agent Metadata - Defines agent types and metadata structure.

This allows business units to describe their agents in a standardized way.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field


class AgentFramework(str, Enum):
    """Supported agent frameworks."""
    LANGCHAIN = "langchain"
    LANGGRAPH = "langgraph"
    CUSTOM = "custom"


class AgentCapability(str, Enum):
    """Agent capabilities (what the agent can do)."""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    RANKING = "ranking"
    VERIFICATION = "verification"
    DATA_FETCH = "data_fetch"
    REPORT_GEN = "report_generation"
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


# Example metadata instances
RESEARCH_AGENT_METADATA = AgentMetadata(
    agent_id="research_agent_v1",
    name="Research Agent",
    description="Fetches policy and resource data for renewable energy analysis",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.RESEARCH, AgentCapability.DATA_FETCH],
    business_unit="roi_team",
    contact="roi-team@company.com",
    required_inputs=["country_code", "technology", "latitude", "longitude"],
    output_keys=["policy_data", "resource_data"],
    tags=["renewable_energy", "data_collection"]
)

RANKING_AGENT_METADATA = AgentMetadata(
    agent_id="ranking_agent_v1",
    name="AI Ranking Agent",
    description="Ranks countries using GPT-4 with weighted criteria",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.RANKING, AgentCapability.DECISION_MAKING],
    business_unit="roi_team",
    contact="roi-team@company.com",
    required_inputs=["country_reports"],
    output_keys=["ranking", "justifications"],
    tags=["ai", "ranking", "decision_support"]
)