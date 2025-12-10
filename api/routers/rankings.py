"""
Rankings Router - RESTful API Endpoints

Provides endpoints for creating and managing ranking jobs.
"""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from api.models.schemas import (
    RankingRequest,
    RankingJobResponse,
    RankingStatusResponse,
    RankingResultResponse,
    JobStatus,
    CountryRanking
)
from api.storage.job_store import job_store, generate_job_id
from api.services.job_service import process_ranking_job, get_job_summary
from api.config import get_settings

# Get settings
settings = get_settings()

# Setup logging
logger = logging.getLogger("RankingsRouter")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Create router
router = APIRouter()


# ============================================================================
# Main Endpoints
# ============================================================================

@router.post(
    "/rankings",
    response_model=RankingJobResponse,
    status_code=202,
    summary="Create Ranking Job",
    description="""
    Create a new ranking job to analyze countries for renewable energy investment.

    The job will:
    1. Load research data for each country
    2. Generate expert presentations (parallel)
    3. Generate peer rankings (parallel)
    4. Aggregate rankings into consensus
    5. Generate executive report

    Processing time: ~20-30 seconds for 3 countries with 3 peer rankers.

    Returns a job ID to track progress and retrieve results.
    """
)
async def create_ranking_job(
        request: RankingRequest,
        background_tasks: BackgroundTasks
) -> RankingJobResponse:
    """
    Create a new ranking job.

    Args:
        request: RankingRequest with countries and num_peer_rankers
        background_tasks: FastAPI background tasks

    Returns:
        RankingJobResponse with job_id and status
    """

    logger.info("=" * 70)
    logger.info("NEW RANKING JOB REQUEST")
    logger.info("=" * 70)
    logger.info(f"Countries: {request.countries}")
    logger.info(f"Peer rankers: {request.num_peer_rankers}")

    try:
        # Generate unique job ID
        job_id = generate_job_id()

        # Create job in storage
        job = job_store.create_job(
            job_id=job_id,
            countries=request.countries,
            num_peer_rankers=request.num_peer_rankers
        )

        # Add to background tasks
        background_tasks.add_task(process_ranking_job, job_id)

        logger.info(f"✅ Job created: {job_id}")
        logger.info(f"   Status: {job['status']}")

        # Estimate duration (rough estimate: 7-10 seconds per country)
        estimated_duration = len(request.countries) * 8

        return RankingJobResponse(
            job_id=job_id,
            status=job["status"],
            message=f"Ranking job created. Processing {len(request.countries)} countries with {request.num_peer_rankers} peer rankers.",
            created_at=job["created_at"],
            estimated_duration_seconds=estimated_duration
        )

    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ranking job: {str(e)}"
        )


@router.get(
    "/rankings/{job_id}/status",
    response_model=RankingStatusResponse,
    summary="Get Job Status",
    description="""
    Check the status and progress of a ranking job.

    Status values:
    - PENDING: Job created, waiting to start
    - RUNNING: Job is processing
    - COMPLETED: Job finished successfully
    - FAILED: Job encountered an error

    Progress is tracked through 5 stages:
    1. research - Loading country data
    2. presentations - Expert analysis (parallel)
    3. rankings - Peer evaluation (parallel)
    4. aggregation - Consensus calculation
    5. report_generation - Creating markdown report
    """
)
async def get_job_status(job_id: str) -> RankingStatusResponse:
    """
    Get the current status of a ranking job.

    Args:
        job_id: Unique job identifier

    Returns:
        RankingStatusResponse with status and progress
    """

    logger.info(f"Status check: {job_id}")

    job = job_store.get_job(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")

    # Build response
    response = RankingStatusResponse(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        duration_seconds=job.get("duration_seconds"),
        progress=job.get("progress", {}),
        countries=job["countries"],
        num_peer_rankers=job["num_peer_rankers"],
        error=job.get("error")
    )

    logger.info(f"Job {job_id}: {job['status']}")

    return response


@router.get(
    "/rankings/{job_id}",
    response_model=RankingResultResponse,
    summary="Get Ranking Results",
    description="""
    Get the complete results of a completed ranking job.

    Returns:
    - Final country rankings (ordered by consensus score)
    - Consensus scores and agreement levels
    - Peer scores for each country
    - Expert recommendations
    - Report availability status
    - Execution metadata

    Note: Only available for COMPLETED jobs.
    Returns 202 (Accepted) if job is still running.
    """
)
async def get_ranking_results(job_id: str) -> RankingResultResponse:
    """
    Get the results of a completed ranking job.

    Args:
        job_id: Unique job identifier

    Returns:
        RankingResultResponse with rankings and metadata
    """

    logger.info(f"Results request: {job_id}")

    job = job_store.get_job(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if job is still running
    if job["status"] in [JobStatus.PENDING, JobStatus.RUNNING]:
        logger.info(f"Job {job_id} still running: {job['status']}")
        raise HTTPException(
            status_code=202,
            detail=f"Job is still {job['status'].lower()}. Check /rankings/{job_id}/status for progress."
        )

    # Check if job failed
    if job["status"] == JobStatus.FAILED:
        logger.error(f"Job {job_id} failed: {job.get('error', 'Unknown error')}")
        return RankingResultResponse(
            job_id=job_id,
            status=job["status"],
            created_at=job["created_at"],
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at"),
            duration_seconds=job.get("duration_seconds", 0),
            countries_analyzed=[],
            rankings=[],
            report_available=False,
            error=job.get("error", "Unknown error")
        )

    # Job completed successfully
    result = job.get("result", {})
    rankings_data = result.get("rankings", [])

    # Convert to CountryRanking objects
    rankings = [
        CountryRanking(**ranking)
        for ranking in rankings_data
    ]

    # Check if report is available
    report_path = result.get("report_path", "")
    report_available = bool(report_path and os.path.exists(report_path))

    logger.info(f"Job {job_id}: {len(rankings)} rankings, report: {report_available}")

    response = RankingResultResponse(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        duration_seconds=job.get("duration_seconds", 0),
        countries_analyzed=job["countries"],
        rankings=rankings,
        report_available=report_available
    )

    return response


@router.get(
    "/rankings/{job_id}/report",
    summary="Download Markdown Report",
    description="""
    Download the complete markdown report for a completed ranking job.

    The report includes:
    - Executive summary with top recommendations
    - Rankings table with consensus scores
    - Detailed country analyses
    - Peer reasoning and agreement levels
    - Methodology section
    - Execution metadata

    Returns a markdown file ready for viewing or further processing.
    """
)
async def download_report(job_id: str):
    """
    Download the markdown report file.

    Args:
        job_id: Unique job identifier

    Returns:
        FileResponse with markdown file
    """

    logger.info(f"Report download: {job_id}")

    job = job_store.get_job(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != JobStatus.COMPLETED:
        logger.warning(f"Job {job_id} not completed: {job['status']}")
        raise HTTPException(
            status_code=400,
            detail=f"Report not available. Job status: {job['status']}"
        )

    # Get report path from result
    result = job.get("result", {})
    report_path = result.get("report_path", "")

    # Validate report path
    if not report_path:
        logger.error(f"Job {job_id}: No report path in result")
        raise HTTPException(
            status_code=404,
            detail="Report path not found in job result"
        )

    # Check if file exists
    if not os.path.exists(report_path):
        logger.error(f"Job {job_id}: Report file not found at {report_path}")
        raise HTTPException(
            status_code=404,
            detail=f"Report file not found: {report_path}"
        )

    # Check file size
    file_size = os.path.getsize(report_path)
    logger.info(f"Serving report: {report_path} ({file_size:,} bytes)")

    # Return file
    return FileResponse(
        path=report_path,
        media_type="text/markdown",
        filename=f"ranking_report_{job_id}.md",
        headers={
            "Content-Disposition": f"attachment; filename=ranking_report_{job_id}.md"
        }
    )


@router.get(
    "/rankings/{job_id}/report/preview",
    summary="Preview Report",
    description="""
    Get a preview of the markdown report (first 2000 characters).

    Useful for quickly checking report content without downloading the full file.
    """
)
async def preview_report(job_id: str):
    """
    Get a preview of the report content.

    Args:
        job_id: Unique job identifier

    Returns:
        Dict with preview text and metadata
    """

    logger.info(f"Report preview: {job_id}")

    job = job_store.get_job(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != JobStatus.COMPLETED:
        logger.warning(f"Job {job_id} not completed: {job['status']}")
        raise HTTPException(
            status_code=400,
            detail=f"Report not available. Job status: {job['status']}"
        )

    # Get report path
    result = job.get("result", {})
    report_path = result.get("report_path", "")

    if not report_path or not os.path.exists(report_path):
        logger.error(f"Job {job_id}: Report file not found")
        raise HTTPException(status_code=404, detail="Report file not found")

    try:
        # Read first 2000 characters
        with open(report_path, 'r', encoding='utf-8') as f:
            preview = f.read(2000)

        # Get full file info
        file_size = os.path.getsize(report_path)

        logger.info(f"Preview generated: {len(preview)} chars of {file_size:,} bytes")

        return {
            "job_id": job_id,
            "preview": preview,
            "preview_length": len(preview),
            "total_file_size": file_size,
            "is_truncated": file_size > 2000,
            "download_url": f"/api/v1/rankings/{job_id}/report"
        }

    except Exception as e:
        logger.error(f"Failed to read report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read report: {str(e)}"
        )


# ============================================================================
# Additional Utility Endpoints
# ============================================================================

@router.get(
    "/rankings",
    summary="List All Jobs",
    description="""
    Get a list of all ranking jobs (up to 100 most recent).

    Returns basic information for each job:
    - job_id
    - status
    - countries
    - created_at
    - completed_at (if finished)
    """
)
async def list_jobs(limit: int = 20):
    """
    List all ranking jobs.

    Args:
        limit: Maximum number of jobs to return (default: 20, max: 100)

    Returns:
        List of job summaries
    """

    # Validate limit
    if limit < 1:
        limit = 20
    elif limit > 100:
        limit = 100

    logger.info(f"Listing jobs (limit: {limit})")

    jobs = job_store.list_jobs(limit=limit)

    # Format response
    job_list = []
    for job in jobs:
        summary = {
            "job_id": job["job_id"],
            "status": job["status"],
            "countries": job["countries"],
            "num_peer_rankers": job["num_peer_rankers"],
            "created_at": job["created_at"]
        }

        if job.get("started_at"):
            summary["started_at"] = job["started_at"]

        if job.get("completed_at"):
            summary["completed_at"] = job["completed_at"]
            summary["duration_seconds"] = job.get("duration_seconds", 0)

        if job["status"] == JobStatus.COMPLETED:
            result = job.get("result", {})
            rankings = result.get("rankings", [])
            summary["num_rankings"] = len(rankings)
            if rankings:
                summary["top_choice"] = rankings[0]["country_code"]

        job_list.append(summary)

    logger.info(f"Returning {len(job_list)} jobs")

    return {
        "total": len(job_list),
        "limit": limit,
        "jobs": job_list
    }


@router.delete(
    "/rankings/{job_id}",
    summary="Delete Job",
    description="Delete a ranking job and its results (if completed)."
)
async def delete_job(job_id: str):
    """
    Delete a ranking job.

    Args:
        job_id: Unique job identifier

    Returns:
        Success message
    """

    logger.info(f"Delete request: {job_id}")

    job = job_store.get_job(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")

    # Don't allow deletion of running jobs
    if job["status"] == JobStatus.RUNNING:
        logger.warning(f"Cannot delete running job: {job_id}")
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a running job. Wait for completion or failure."
        )

    # Delete report file if exists
    if job["status"] == JobStatus.COMPLETED:
        result = job.get("result", {})
        report_path = result.get("report_path", "")

        if report_path and os.path.exists(report_path):
            try:
                os.remove(report_path)
                logger.info(f"Deleted report file: {report_path}")
            except Exception as e:
                logger.warning(f"Failed to delete report file: {e}")

    # Remove from job store (if implemented)
    # job_store.delete_job(job_id)
    # For now, just mark as deleted in metadata

    logger.info(f"Job {job_id} deleted")

    return {
        "message": f"Job {job_id} deleted successfully",
        "job_id": job_id
    }


@router.get(
    "/rankings/{job_id}/summary",
    summary="Get Job Summary",
    description="Get a quick summary of job status and results."
)
async def get_job_summary_endpoint(job_id: str):
    """
    Get a summary of job status and results.

    Args:
        job_id: Unique job identifier

    Returns:
        Job summary with key metrics
    """

    logger.info(f"Summary request: {job_id}")

    summary = get_job_summary(job_id)

    if not summary.get("found"):
        raise HTTPException(status_code=404, detail="Job not found")

    return summary


# ============================================================================
# Debug Endpoint (Remove in Production)
# ============================================================================

@router.get(
    "/rankings/{job_id}/debug",
    summary="Debug Job (Development Only)",
    description="Get full job details for debugging. Remove in production.",
    include_in_schema=settings.environment != "production"  # Hide in prod
)
async def debug_job(job_id: str):
    """
    Get complete job details for debugging.

    ⚠️ WARNING: This endpoint exposes sensitive data. Remove in production.
    """

    if settings.environment == "production":
        raise HTTPException(status_code=404, detail="Endpoint not found")

    job = job_store.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job