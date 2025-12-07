"""
Rankings Router

Handles all ranking-related endpoints.
"""

import os
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse

from api.models.schemas import (
    RankingRequest,
    RankingJobResponse,
    RankingStatusResponse,
    RankingResultResponse,
    JobStatus
)
from api.storage.job_store import get_job_store
from api.services.job_service import process_ranking_job
from api.config import get_settings

router = APIRouter(prefix="/rankings", tags=["rankings"])
settings = get_settings()
job_store = get_job_store()


@router.post("", response_model=RankingJobResponse)
async def create_ranking_job(
        request: RankingRequest,
        background_tasks: BackgroundTasks
):
    """
    Create a new ranking job.

    The job will be processed asynchronously. Use the returned job_id
    to check status and retrieve results.

    **Parameters:**
    - **countries**: List of 2-15 country names or codes
    - **num_peer_rankers**: Number of independent peer rankers (2-5)

    **Returns:**
    - job_id: Unique identifier for tracking the job
    - status: Current job status (pending)
    - estimated_duration_seconds: Estimated completion time
    """

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create job
    job_store.create_job(
        job_id=job_id,
        countries=request.countries,
        num_peer_rankers=request.num_peer_rankers
    )

    # Add background task
    background_tasks.add_task(process_ranking_job, job_id)

    # Estimate duration (based on testing: ~20s for 3 countries)
    base_duration = 20
    country_factor = len(request.countries) / 3
    estimated_duration = int(base_duration * country_factor)

    return RankingJobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Ranking job created successfully. Processing will begin shortly.",
        created_at=job_store.get_job(job_id)["created_at"],
        estimated_duration_seconds=estimated_duration
    )


@router.get("/{job_id}/status", response_model=RankingStatusResponse)
async def get_job_status(job_id: str):
    """
    Get job status and progress.

    Returns current status, progress through stages, and timing information.

    **Progress Stages:**
    - research: Loading country research data
    - presentations: Expert agents building cases
    - rankings: Peer agents ranking countries
    - aggregation: Combining peer rankings
    - report_generation: Creating final report
    """

    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return RankingStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        duration_seconds=job.get("duration_seconds"),
        progress=job["progress"],
        countries=job["countries"],
        num_peer_rankers=job["num_peer_rankers"],
        error=job.get("error")
    )


@router.get("/{job_id}", response_model=RankingResultResponse)
async def get_ranking_results(job_id: str):
    """
    Get ranking results for a completed job.

    Returns the final rankings with scores and agreement levels.

    **Returns:**
    - rankings: List of countries with ranks, scores, and agreement levels
    - report_available: Whether a downloadable report is available
    """

    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["status"] == JobStatus.PENDING:
        raise HTTPException(
            status_code=202,
            detail="Job is still pending. Please check status endpoint."
        )

    if job["status"] == JobStatus.RUNNING:
        raise HTTPException(
            status_code=202,
            detail="Job is still running. Please check status endpoint."
        )

    if job["status"] == JobStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {job.get('error', 'Unknown error')}"
        )

    # Job is completed
    result = job.get("result", {})

    return RankingResultResponse(
        job_id=job["job_id"],
        status=job["status"],
        created_at=job["created_at"],
        completed_at=job["completed_at"],
        duration_seconds=job["duration_seconds"],
        countries_analyzed=len(job["countries"]),
        rankings=result.get("rankings", []),
        report_available=bool(result.get("report_path")),
        error=job.get("error")
    )


@router.get("/{job_id}/report")
async def download_report(job_id: str):
    """
    Download the markdown report for a completed job.

    Returns the report as a downloadable markdown file.
    """

    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Report not available. Job status: {job['status']}"
        )

    result = job.get("result", {})
    report_path = result.get("report_path")

    if not report_path or not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail="Report file not found"
        )

    # Return file for download
    filename = f"renewable_energy_rankings_{job_id[:8]}.md"

    return FileResponse(
        path=report_path,
        media_type="text/markdown",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{job_id}/report/preview")
async def preview_report(job_id: str):
    """
    Preview the report content (first 2000 characters).

    Returns a preview of the markdown report without downloading.
    """

    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Report not available. Job status: {job['status']}"
        )

    result = job.get("result", {})
    report_path = result.get("report_path")

    if not report_path or not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail="Report file not found"
        )

    # Read report content
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Return preview
    preview = content[:2000]
    if len(content) > 2000:
        preview += "\n\n... (truncated, download full report)"

    return Response(
        content=preview,
        media_type="text/markdown"
    )