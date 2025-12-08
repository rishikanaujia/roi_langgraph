"""
Phase 2 Workflow API Models

Pydantic models for Phase 2 workflow requests and responses.

Author: Kanauija
Date: 2024-12-08
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Request Models
# ============================================================================

class Phase2WorkflowRequest(BaseModel):
    """Request model for Phase 2 workflow execution."""

    countries: List[str] = Field(
        ...,
        description="List of country codes to analyze (2-10 countries)",
        min_items=2,
        max_items=10,
        example=["USA", "CHN", "IND"]
    )

    num_peer_rankers: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Number of peer rankers to create"
    )

    debate_enabled: bool = Field(
        default=True,
        description="Whether to enable hot seat debate"
    )

    debate_threshold: str = Field(
        default="high",
        description="Threshold for triggering debate",
        pattern="^(very_high|high|medium|low)$"
    )

    num_challengers: int = Field(
        default=2,
        ge=1,
        le=3,
        description="Number of challengers in debate"
    )

    use_existing_research: bool = Field(
        default=False,
        description="Whether to use existing research data (if available)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "countries": ["USA", "CHN", "IND"],
                "num_peer_rankers": 3,
                "debate_enabled": True,
                "debate_threshold": "high",
                "num_challengers": 2,
                "use_existing_research": False
            }
        }


# Response Models
# ============================================================================

class JobStatus(BaseModel):
    """Job status information."""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, running, completed, failed")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    current_stage: Optional[str] = Field(None, description="Current stage being executed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


class Phase2WorkflowResponse(BaseModel):
    """Response model for Phase 2 workflow submission."""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Response message")
    status_url: str = Field(..., description="URL to check job status")
    results_url: str = Field(..., description="URL to retrieve results (when ready)")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "phase2_20241208_123456_abc123",
                "status": "pending",
                "message": "Phase 2 workflow job submitted successfully",
                "status_url": "/api/phase2/jobs/phase2_20241208_123456_abc123/status",
                "results_url": "/api/phase2/jobs/phase2_20241208_123456_abc123/results"
            }
        }


class RankingItem(BaseModel):
    """Individual country ranking."""

    rank: int
    country_code: str
    consensus_score: float
    agreement_level: str
    debate_winner: Optional[bool] = None
    debate_loser: Optional[bool] = None
    debate_challenger: Optional[bool] = None


class DebateResult(BaseModel):
    """Debate execution results."""

    verdict: str
    recommendation: str
    challenger_wins: int
    defender_wins: int
    avg_challenger_score: float
    avg_defender_score: float
    rounds: List[Dict[str, Any]]


class Phase2Results(BaseModel):
    """Complete Phase 2 workflow results."""

    job_id: str
    status: str

    # Workflow results
    expert_presentations: Dict[str, Any]
    peer_rankings: List[Dict[str, Any]]
    aggregated_ranking: Dict[str, Any]
    final_ranking: List[RankingItem]

    # Phase 2 specific
    debate_triggered: bool
    debate_result: Optional[DebateResult] = None

    # Report
    report_markdown: str
    report_metadata: Dict[str, Any]

    # Execution metadata
    execution_metadata: Dict[str, Any]
    errors: List[str]

    # Timestamps
    created_at: datetime
    started_at: datetime
    completed_at: datetime


class Phase2JobsList(BaseModel):
    """List of Phase 2 jobs."""

    jobs: List[JobStatus]
    total: int
    page: int
    page_size: int