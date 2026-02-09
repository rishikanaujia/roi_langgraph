"""
Phase 2 Workflow API Endpoints

FastAPI endpoints for Phase 2 workflow execution with async job processing.

Author: Kanauija
Date: 2024-12-08
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from api.models.phase2_models import (
    Phase2WorkflowRequest,
    Phase2WorkflowResponse,
    JobStatus as JobStatusModel,
    Phase2Results,
    Phase2JobsList
)
from api.services.job_manager import job_manager, JobStatus
from api.services.research_service import generate_research_data
from src.workflows.phase2_workflow_langgraph import run_phase2_langgraph

logger = logging.getLogger("Phase2Endpoints")

# Create router
router = APIRouter(
    prefix="/api/phase2",
    tags=["Phase 2 - Debate Workflow"],
    responses={404: {"description": "Not found"}}
)


# Background Task Function
# ============================================================================

async def execute_phase2_workflow(
        job_id: str,
        request: Phase2WorkflowRequest
):
    """
    Background task to execute Phase 2 workflow.

    This runs in the background and updates job status as it progresses.
    """
    try:
        logger.info(f"Starting Phase 2 workflow for job: {job_id}")

        # Update status to running
        job_manager.update_job_status(
            job_id,
            JobStatus.RUNNING,
            progress=10,
            current_stage="research"
        )

        # Generate research data if needed
        if request.use_existing_research:
            research_data = None  # Will load from storage
        else:
            research_data = generate_research_data(request.countries)

        # Update progress
        job_manager.update_job_status(
            job_id,
            JobStatus.RUNNING,
            progress=20,
            current_stage="presentations"
        )

        # Execute Phase 2 workflow
        result = await run_phase2_langgraph(
            countries=request.countries,
            research_json_data=research_data,
            num_peer_rankers=request.num_peer_rankers,
            debate_enabled=request.debate_enabled,
            debate_threshold=request.debate_threshold,
            num_challengers=request.num_challengers
        )

        # Update progress based on stages
        job_manager.update_job_status(
            job_id,
            JobStatus.RUNNING,
            progress=90,
            current_stage="finalizing"
        )

        # Store result
        job_manager.set_job_result(job_id, result)

        # Mark as completed
        job_manager.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            progress=100,
            current_stage="completed"
        )

        logger.info(f"✅ Phase 2 workflow completed for job: {job_id}")

    except Exception as e:
        logger.error(f"❌ Phase 2 workflow failed for job {job_id}: {str(e)}")

        job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )


# Endpoints
# ============================================================================

@router.post(
    "/execute",
    response_model=Phase2WorkflowResponse,
    summary="Execute Phase 2 Workflow",
    description="Submit a Phase 2 workflow job for async execution"
)
async def execute_phase2(
        request: Phase2WorkflowRequest,
        background_tasks: BackgroundTasks
):
    """
    Execute Phase 2 workflow with hot seat debate.

    This endpoint submits a job for async execution and returns immediately
    with a job ID. Use the status and results endpoints to track progress
    and retrieve results.

    **Workflow Steps:**
    1. Research loading
    2. Expert presentations (parallel)
    3. Peer rankings (parallel)
    4. Ranking aggregation
    5. Hot seat debate (conditional)
    6. Report generation

    **Returns:**
    - job_id: Unique identifier for tracking the job
    - status_url: Endpoint to check job status
    - results_url: Endpoint to retrieve results when ready
    """
    try:
        # Validate countries count
        if len(request.countries) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 countries required for comparison"
            )

        # Create job
        job_id = job_manager.create_job(
            workflow_type="phase2",
            params=request.dict()
        )

        # Add background task
        background_tasks.add_task(
            execute_phase2_workflow,
            job_id,
            request
        )

        # Return response
        return Phase2WorkflowResponse(
            job_id=job_id,
            status="pending",
            message="Phase 2 workflow job submitted successfully",
            status_url=f"/api/phase2/jobs/{job_id}/status",
            results_url=f"/api/phase2/jobs/{job_id}/results"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting Phase 2 workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit workflow: {str(e)}"
        )


@router.get(
    "/jobs/{job_id}/status",
    response_model=JobStatusModel,
    summary="Get Job Status",
    description="Get the current status of a Phase 2 workflow job"
)
async def get_job_status(job_id: str):
    """
    Get the current status of a workflow job.

    **Status Values:**
    - pending: Job is queued and waiting to start
    - running: Job is currently executing
    - completed: Job finished successfully
    - failed: Job encountered an error

    **Progress:**
    - 0-100: Percentage of workflow completion

    **Current Stage:**
    - research: Loading research data
    - presentations: Generating expert presentations
    - rankings: Collecting peer rankings
    - aggregation: Aggregating rankings
    - debate: Executing hot seat debate
    - report: Generating final report
    - completed: All stages finished
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )

    return JobStatusModel(
        job_id=job.job_id,
        status=job.status.value,
        progress=job.progress,
        current_stage=job.current_stage,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error
    )


@router.get(
    "/jobs/{job_id}/results",
    response_model=Phase2Results,
    summary="Get Job Results",
    description="Get the complete results of a completed Phase 2 workflow job"
)
async def get_job_results(job_id: str):
    """
    Get the complete results of a workflow job.

    **Returns:**
    - Expert presentations for each country
    - Peer rankings from all rankers
    - Aggregated consensus ranking
    - Final ranking (after debate if applicable)
    - Debate results (if debate was triggered)
    - Executive report (markdown)
    - Execution metadata and timings

    **Note:** This endpoint only returns data for completed jobs.
    Use the status endpoint to check if the job is finished.
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed yet. Current status: {job.status.value}"
        )

    result = job.result

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Job completed but results not found"
        )

    # Convert to response model
    return Phase2Results(
        job_id=job.job_id,
        status=job.status.value,
        expert_presentations=result.get("expert_presentations", {}),
        peer_rankings=result.get("peer_rankings", []),
        aggregated_ranking=result.get("aggregated_ranking", {}),
        final_ranking=result.get("final_ranking", []),
        debate_triggered=result.get("debate_triggered", False),
        debate_result=result.get("debate_result"),
        report_markdown=result.get("report_markdown", ""),
        report_metadata=result.get("report_metadata", {}),
        execution_metadata=result.get("execution_metadata", {}),
        errors=result.get("errors", []),
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.get(
    "/jobs",
    response_model=Phase2JobsList,
    summary="List All Jobs",
    description="Get a paginated list of Phase 2 workflow jobs"
)
async def list_jobs(
        status: Optional[str] = Query(
            None,
            description="Filter by status: pending, running, completed, failed"
        ),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get a paginated list of workflow jobs.

    **Filters:**
    - status: Filter by job status

    **Pagination:**
    - page: Page number (starts at 1)
    - page_size: Number of items per page (1-100)
    """
    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: pending, running, completed, failed"
            )

    # Get all jobs
    all_jobs = job_manager.list_jobs(
        workflow_type="phase2",
        status=status_filter
    )

    # Paginate
    total = len(all_jobs)
    start = (page - 1) * page_size
    end = start + page_size
    page_jobs = all_jobs[start:end]

    # Convert to response models
    job_models = [
        JobStatusModel(
            job_id=job.job_id,
            status=job.status.value,
            progress=job.progress,
            current_stage=job.current_stage,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error=job.error
        )
        for job in page_jobs
    ]

    return Phase2JobsList(
        jobs=job_models,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete(
    "/jobs/{job_id}",
    summary="Delete Job",
    description="Delete a Phase 2 workflow job and its results"
)
async def delete_job(job_id: str):
    """
    Delete a workflow job and its results.

    **Note:** Only completed or failed jobs can be deleted.
    Running jobs cannot be cancelled via this endpoint.
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )

    if job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete running job. Wait for completion or failure."
        )

    # Delete job
    del job_manager.jobs[job_id]

    return JSONResponse(
        content={
            "message": f"Job deleted successfully: {job_id}",
            "job_id": job_id
        }
    )


@router.get(
    "/health",
    summary="Health Check",
    description="Check if Phase 2 API is healthy"
)
async def health_check():
    """
    Health check endpoint for Phase 2 workflow API.

    **Returns:**
    - status: API health status
    - active_jobs: Number of currently running jobs
    - total_jobs: Total number of jobs in memory
    """
    running_jobs = len([
        j for j in job_manager.jobs.values()
        if j.status == JobStatus.RUNNING
    ])

    return {
        "status": "healthy",
        "service": "Phase 2 Workflow API",
        "active_jobs": running_jobs,
        "total_jobs": len(job_manager.jobs)
    }