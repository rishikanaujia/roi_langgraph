"""
API Models and Schemas

Pydantic models for request/response validation and OpenAPI documentation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# Enums
# ============================================================================

class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProgressStatus(str, Enum):
    """Progress status for individual stages."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class AgreementLevel(str, Enum):
    """Peer agreement level."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ExpertRecommendation(str, Enum):
    """Expert investment recommendation."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    AVOID = "AVOID"


# ============================================================================
# Country Name Mapping (for validation)
# ============================================================================

COUNTRY_NAME_TO_CODE = {
    # Full names
    "united states": "USA",
    "united states of america": "USA",
    "usa": "USA",
    "us": "USA",

    "india": "IND",
    "republic of india": "IND",
    "ind": "IND",

    "china": "CHN",
    "people's republic of china": "CHN",
    "prc": "CHN",
    "chn": "CHN",

    "brazil": "BRA",
    "brasil": "BRA",
    "bra": "BRA",

    "germany": "DEU",
    "deutschland": "DEU",
    "deu": "DEU",

    "japan": "JPN",
    "nippon": "JPN",
    "jpn": "JPN",

    "united kingdom": "GBR",
    "uk": "GBR",
    "great britain": "GBR",
    "britain": "GBR",
    "gbr": "GBR",

    "france": "FRA",
    "fra": "FRA",

    "canada": "CAN",
    "can": "CAN",

    "australia": "AUS",
    "aus": "AUS",

    "south africa": "ZAF",
    "zaf": "ZAF",

    "mexico": "MEX",
    "mex": "MEX",

    "spain": "ESP",
    "esp": "ESP",

    "italy": "ITA",
    "ita": "ITA",
}

VALID_COUNTRY_CODES = set(COUNTRY_NAME_TO_CODE.values())


def normalize_country_code(country: str) -> str:
    """
    Normalize country name to ISO 3166-1 alpha-3 code.

    Args:
        country: Country name or code

    Returns:
        Three-letter country code (e.g., "USA")

    Raises:
        ValueError: If country not recognized
    """
    if not country:
        raise ValueError("Country name cannot be empty")

    # Normalize: lowercase, strip whitespace
    normalized = country.lower().strip()

    # Check if already a valid code
    if country.upper() in VALID_COUNTRY_CODES:
        return country.upper()

    # Look up in mapping
    code = COUNTRY_NAME_TO_CODE.get(normalized)

    if not code:
        raise ValueError(
            f"Unrecognized country: '{country}'. "
            f"Valid countries: {sorted(set(COUNTRY_NAME_TO_CODE.keys()))}"
        )

    return code


# ============================================================================
# Request Models
# ============================================================================

class RankingRequest(BaseModel):
    """
    Request to create a new ranking job.

    Example:
        {
            "countries": ["USA", "India", "China"],
            "num_peer_rankers": 3
        }
    """

    countries: List[str] = Field(
        ...,
        min_length=2,
        max_length=15,
        description="List of countries to rank (2-15 countries)",
        examples=[["USA", "IND", "CHN"], ["United States", "India", "China"]]
    )

    num_peer_rankers: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Number of independent peer rankers (2-5)",
        examples=[3, 5]
    )

    @field_validator('countries')
    @classmethod
    def validate_and_normalize_countries(cls, v: List[str]) -> List[str]:
        """
        Validate and normalize country names to codes.

        Converts country names to ISO 3166-1 alpha-3 codes.
        Removes duplicates while preserving order.
        """
        if not v:
            raise ValueError("At least 2 countries are required")

        # Normalize all country names to codes
        normalized = []
        seen = set()

        for country in v:
            try:
                code = normalize_country_code(country)

                # Check for duplicates
                if code in seen:
                    continue  # Skip duplicate

                normalized.append(code)
                seen.add(code)

            except ValueError as e:
                raise ValueError(f"Invalid country '{country}': {str(e)}")

        # Check minimum after deduplication
        if len(normalized) < 2:
            raise ValueError(
                f"At least 2 unique countries required (got {len(normalized)} after deduplication)"
            )

        return normalized

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "countries": ["USA", "IND", "CHN"],
                    "num_peer_rankers": 3
                },
                {
                    "countries": ["United States", "India", "China", "Brazil", "Germany"],
                    "num_peer_rankers": 5
                }
            ]
        }
    )


# ============================================================================
# Response Models - Job Management
# ============================================================================

class RankingJobResponse(BaseModel):
    """
    Response after creating a ranking job.

    Example:
        {
            "job_id": "job_abc123def456",
            "status": "PENDING",
            "message": "Ranking job created...",
            "created_at": "2024-12-08T10:30:00",
            "estimated_duration_seconds": 24
        }
    """

    job_id: str = Field(
        ...,
        description="Unique job identifier",
        examples=["job_abc123def456"]
    )

    status: JobStatus = Field(
        ...,
        description="Current job status",
        examples=[JobStatus.PENDING]
    )

    message: str = Field(
        ...,
        description="Human-readable message about the job",
        examples=["Ranking job created. Processing 3 countries with 3 peer rankers."]
    )

    created_at: str = Field(
        ...,
        description="Job creation timestamp (ISO format)",
        examples=["2024-12-08T10:30:00.123456"]
    )

    estimated_duration_seconds: int = Field(
        ...,
        description="Estimated processing time in seconds",
        examples=[24]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_id": "job_abc123def456",
                    "status": "PENDING",
                    "message": "Ranking job created. Processing 3 countries with 3 peer rankers.",
                    "created_at": "2024-12-08T10:30:00.123456",
                    "estimated_duration_seconds": 24
                }
            ]
        }
    )


class JobProgress(BaseModel):
    """Progress tracking for job stages."""

    research: ProgressStatus = Field(
        default=ProgressStatus.PENDING,
        description="Research loading stage"
    )

    presentations: ProgressStatus = Field(
        default=ProgressStatus.PENDING,
        description="Expert presentations stage"
    )

    rankings: ProgressStatus = Field(
        default=ProgressStatus.PENDING,
        description="Peer rankings stage"
    )

    aggregation: ProgressStatus = Field(
        default=ProgressStatus.PENDING,
        description="Ranking aggregation stage"
    )

    report_generation: ProgressStatus = Field(
        default=ProgressStatus.PENDING,
        description="Report generation stage"
    )


class RankingStatusResponse(BaseModel):
    """
    Job status and progress information.

    Example:
        {
            "job_id": "job_abc123",
            "status": "RUNNING",
            "created_at": "2024-12-08T10:30:00",
            "started_at": "2024-12-08T10:30:01",
            "progress": {
                "research": "complete",
                "presentations": "in_progress",
                ...
            },
            "countries": ["USA", "IND", "CHN"],
            "num_peer_rankers": 3
        }
    """

    job_id: str = Field(
        ...,
        description="Unique job identifier"
    )

    status: JobStatus = Field(
        ...,
        description="Current job status"
    )

    created_at: str = Field(
        ...,
        description="Job creation timestamp"
    )

    started_at: Optional[str] = Field(
        default=None,
        description="Job start timestamp"
    )

    completed_at: Optional[str] = Field(
        default=None,
        description="Job completion timestamp"
    )

    duration_seconds: Optional[float] = Field(
        default=None,
        description="Total execution time in seconds"
    )

    progress: Dict[str, str] = Field(
        default_factory=dict,
        description="Progress for each stage"
    )

    countries: List[str] = Field(
        ...,
        description="Countries being analyzed"
    )

    num_peer_rankers: int = Field(
        ...,
        description="Number of peer rankers"
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if job failed"
    )


# ============================================================================
# Response Models - Rankings
# ============================================================================

class ScoreDetails(BaseModel):
    """Detailed scoring breakdown."""

    borda_points: float = Field(
        ...,
        description="Borda count points",
        examples=[6.0]
    )

    score_stddev: float = Field(
        ...,
        description="Standard deviation of peer scores",
        examples=[0.25]
    )

    median_rank: float = Field(
        ...,
        description="Median rank position across peers",
        examples=[1.0]
    )

    rank_variance: float = Field(
        ...,
        description="Variance in rank positions",
        examples=[0.47]
    )

    score_variance: float = Field(
        ...,
        description="Variance in peer scores",
        examples=[0.06]
    )


class CountryRanking(BaseModel):
    """
    Ranking for a single country.

    Example:
        {
            "rank": 1,
            "country_code": "USA",
            "consensus_score": 8.95,
            "average_peer_score": 9.1,
            "agreement_level": "high",
            "peer_scores": [9.2, 8.8, 9.2],
            "expert_recommendation": "STRONG_BUY",
            "score_details": {...}
        }
    """

    rank: int = Field(
        ...,
        ge=1,
        description="Rank position (1 = best investment opportunity)",
        examples=[1, 2, 3]
    )

    country_code: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 3166-1 alpha-3 country code",
        examples=["USA", "IND", "CHN"]
    )

    consensus_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Consensus score from all peer rankers (0-10)",
        examples=[8.95, 7.23, 6.45]
    )

    average_peer_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Average score from all peer rankers (0-10)",
        examples=[9.1, 7.5, 6.8]
    )

    agreement_level: str = Field(
        ...,
        description="Level of agreement among peer rankers",
        examples=["very_high", "high", "medium", "low"]
    )

    peer_scores: List[float] = Field(
        ...,
        description="Individual scores from each peer ranker",
        examples=[[9.2, 8.8, 9.2], [7.5, 7.6, 7.4]]
    )

    expert_recommendation: str = Field(
        ...,
        description="Expert's investment recommendation",
        examples=["STRONG_BUY", "BUY", "HOLD", "AVOID"]
    )

    score_details: Optional[ScoreDetails] = Field(
        default=None,
        description="Detailed scoring breakdown"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "rank": 1,
                    "country_code": "USA",
                    "consensus_score": 8.95,
                    "average_peer_score": 9.1,
                    "agreement_level": "high",
                    "peer_scores": [9.2, 8.8, 9.2],
                    "expert_recommendation": "STRONG_BUY",
                    "score_details": {
                        "borda_points": 6.0,
                        "score_stddev": 0.23,
                        "median_rank": 1.0,
                        "rank_variance": 0.47,
                        "score_variance": 0.05
                    }
                }
            ]
        }
    )


class RankingResultResponse(BaseModel):
    """
    Complete results of a ranking job.

    Example:
        {
            "job_id": "job_abc123",
            "status": "COMPLETED",
            "created_at": "2024-12-08T10:30:00",
            "completed_at": "2024-12-08T10:30:24",
            "duration_seconds": 24.5,
            "countries_analyzed": ["USA", "IND", "CHN"],
            "rankings": [...],
            "report_available": true
        }
    """

    job_id: str = Field(
        ...,
        description="Unique job identifier"
    )

    status: JobStatus = Field(
        ...,
        description="Job status (should be COMPLETED)"
    )

    created_at: str = Field(
        ...,
        description="Job creation timestamp"
    )

    started_at: Optional[str] = Field(
        default=None,
        description="Job start timestamp"
    )

    completed_at: Optional[str] = Field(
        default=None,
        description="Job completion timestamp"
    )

    duration_seconds: float = Field(
        ...,
        description="Total execution time in seconds",
        examples=[24.5, 18.3]
    )

    countries_analyzed: List[str] = Field(
        ...,
        description="Countries that were analyzed"
    )

    rankings: List[CountryRanking] = Field(
        ...,
        description="Ranked list of countries (ordered by consensus score)"
    )

    report_available: bool = Field(
        ...,
        description="Whether markdown report is available for download"
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if job failed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_id": "job_abc123def456",
                    "status": "COMPLETED",
                    "created_at": "2024-12-08T10:30:00.123456",
                    "started_at": "2024-12-08T10:30:01.234567",
                    "completed_at": "2024-12-08T10:30:25.678901",
                    "duration_seconds": 24.5,
                    "countries_analyzed": ["USA", "IND", "CHN"],
                    "rankings": [
                        {
                            "rank": 1,
                            "country_code": "USA",
                            "consensus_score": 8.95,
                            "average_peer_score": 9.1,
                            "agreement_level": "high",
                            "peer_scores": [9.2, 8.8, 9.2],
                            "expert_recommendation": "STRONG_BUY"
                        }
                    ],
                    "report_available": True
                }
            ]
        }
    )


# ============================================================================
# Response Models - Health & Misc
# ============================================================================

class HealthResponse(BaseModel):
    """
    API health check response.

    Example:
        {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2024-12-08T10:30:00",
            "details": {...}
        }
    """

    status: str = Field(
        ...,
        description="Health status",
        examples=["healthy", "unhealthy"]
    )

    version: str = Field(
        ...,
        description="API version",
        examples=["1.0.0"]
    )

    timestamp: str = Field(
        ...,
        description="Current server time (ISO format)",
        examples=["2024-12-08T10:30:00.123456"]
    )

    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional health details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "healthy",
                    "version": "1.0.0",
                    "timestamp": "2024-12-08T10:30:00.123456",
                    "details": {
                        "langgraph": "enabled",
                        "storage": "memory",
                        "openai": "configured"
                    }
                }
            ]
        }
    )


class ErrorResponse(BaseModel):
    """
    Standard error response.

    Example:
        {
            "error": "ValidationError",
            "message": "Invalid country name",
            "details": {...}
        }
    """

    error: str = Field(
        ...,
        description="Error type",
        examples=["ValidationError", "NotFoundError", "InternalError"]
    )

    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Invalid country name: 'XYZ'"]
    )

    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )

    timestamp: Optional[str] = Field(
        default=None,
        description="Error timestamp"
    )


class JobSummary(BaseModel):
    """Summary of a job for listing endpoints."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job status")
    countries: List[str] = Field(..., description="Countries analyzed")
    num_peer_rankers: int = Field(..., description="Number of peer rankers")
    created_at: str = Field(..., description="Creation timestamp")
    started_at: Optional[str] = Field(default=None, description="Start timestamp")
    completed_at: Optional[str] = Field(default=None, description="Completion timestamp")
    duration_seconds: Optional[float] = Field(default=None, description="Duration in seconds")
    num_rankings: Optional[int] = Field(default=None, description="Number of rankings produced")
    top_choice: Optional[str] = Field(default=None, description="Top-ranked country")


class JobListResponse(BaseModel):
    """Response for listing multiple jobs."""

    total: int = Field(..., description="Total number of jobs returned")
    limit: int = Field(..., description="Maximum jobs per page")
    jobs: List[JobSummary] = Field(..., description="List of job summaries")


# ============================================================================
# Export All Models
# ============================================================================

__all__ = [
    # Enums
    "JobStatus",
    "ProgressStatus",
    "AgreementLevel",
    "ExpertRecommendation",

    # Request Models
    "RankingRequest",

    # Response Models
    "RankingJobResponse",
    "RankingStatusResponse",
    "RankingResultResponse",
    "HealthResponse",
    "ErrorResponse",

    # Supporting Models
    "CountryRanking",
    "ScoreDetails",
    "JobProgress",
    "JobSummary",
    "JobListResponse",

    # Utilities
    "normalize_country_code",
    "VALID_COUNTRY_CODES",
    "COUNTRY_NAME_TO_CODE"
]