"""
API Data Models

Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, validator


# ============================================================================
# Enums
# ============================================================================

class JobStatus(str, Enum):
    """Job status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Request Models
# ============================================================================

class RankingRequest(BaseModel):
    """Request to create a ranking job."""

    countries: List[str] = Field(
        ...,
        min_length=2,
        max_length=15,
        description="List of country names or codes (2-15 countries)",
        examples=[["USA", "India", "China"]]
    )

    num_peer_rankers: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Number of independent peer rankers (2-5)",
        examples=[3]
    )

    @validator("countries")
    def validate_countries(cls, v):
        """Validate and normalize country names."""
        from api.services.research_service import normalize_country_code

        # Remove duplicates while preserving order
        seen = set()
        unique_countries = []
        for country in v:
            country_code = normalize_country_code(country)
            if country_code not in seen:
                seen.add(country_code)
                unique_countries.append(country_code)

        if len(unique_countries) < 2:
            raise ValueError("At least 2 unique countries required")

        return unique_countries


# ============================================================================
# Response Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str


class CountryRanking(BaseModel):
    """Individual country ranking."""
    rank: int
    country_code: str
    consensus_score: float
    average_peer_score: float
    agreement_level: str
    peer_scores: List[float]
    expert_recommendation: Optional[str] = None


class RankingJobResponse(BaseModel):
    """Response after creating a ranking job."""
    job_id: str
    status: JobStatus
    message: str
    created_at: str
    estimated_duration_seconds: int


class RankingStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str
    status: JobStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    progress: Dict[str, str]
    countries: List[str]
    num_peer_rankers: int
    error: Optional[str] = None


class RankingResultResponse(BaseModel):
    """Response with ranking results."""
    job_id: str
    status: JobStatus
    created_at: str
    completed_at: str
    duration_seconds: float
    countries_analyzed: int
    rankings: List[CountryRanking]
    report_available: bool
    error: Optional[str] = None