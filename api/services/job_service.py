"""
Job Service - Background Job Processing

Handles background execution of ranking jobs using LangGraph workflow.
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from api.storage.job_store import job_store
from api.services.research_service import generate_research_data
from api.models.schemas import JobStatus

# Import LangGraph workflow
from src.workflows.phase1_workflow_langgraph import run_phase1_langgraph

logger = logging.getLogger("JobService")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Job Processing
# ============================================================================

async def process_ranking_job(job_id: str):
    """
    Process a ranking job in the background using LangGraph workflow.

    Args:
        job_id: Unique job identifier
    """

    logger.info("=" * 70)
    logger.info(f"PROCESSING JOB: {job_id}")
    logger.info("=" * 70)

    start_time = datetime.now()  # Track start time locally

    try:
        # Get job details
        job = job_store.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Update status to RUNNING
        job_store.update_job(job_id, {
            "status": JobStatus.RUNNING,
            "started_at": start_time.isoformat()
        })

        logger.info(f"Job {job_id} started")
        logger.info(f"Countries: {job['countries']}")
        logger.info(f"Peer rankers: {job['num_peer_rankers']}")

        # Update progress: Research
        job_store.update_progress(job_id, "research", "in_progress")

        # Generate research data
        logger.info("Generating research data...")
        research_data = generate_research_data(job["countries"])

        job_store.update_progress(job_id, "research", "complete")
        logger.info(f"Research generated for {len(research_data)} countries")

        # Update progress: Presentations
        job_store.update_progress(job_id, "presentations", "in_progress")

        # Run LangGraph workflow
        logger.info("Starting LangGraph workflow...")
        workflow_result = await run_phase1_langgraph(
            countries=job["countries"],
            research_json_data=research_data,
            num_peer_rankers=job["num_peer_rankers"]
        )

        # Check for workflow errors
        if workflow_result.get("errors"):
            logger.warning(f"Workflow completed with {len(workflow_result['errors'])} errors")
            for error in workflow_result["errors"]:
                logger.warning(f"  - {error}")

        # Update progress stages
        if workflow_result.get("expert_presentations"):
            job_store.update_progress(job_id, "presentations", "complete")
            logger.info(f"Generated {len(workflow_result['expert_presentations'])} presentations")

        if workflow_result.get("peer_rankings"):
            job_store.update_progress(job_id, "rankings", "in_progress")
            logger.info(f"Collected {len(workflow_result['peer_rankings'])} peer rankings")

        job_store.update_progress(job_id, "rankings", "complete")

        if workflow_result.get("aggregated_ranking"):
            job_store.update_progress(job_id, "aggregation", "in_progress")
            job_store.update_progress(job_id, "aggregation", "complete")
            logger.info("Rankings aggregated successfully")

        if workflow_result.get("report_markdown"):
            job_store.update_progress(job_id, "report_generation", "in_progress")
            job_store.update_progress(job_id, "report_generation", "complete")
            logger.info(f"Report generated: {len(workflow_result['report_markdown'])} chars")

        # Extract rankings
        rankings = _extract_rankings(workflow_result)

        # Get report path
        report_path = workflow_result.get("report_metadata", {}).get("filepath", "")

        # Calculate duration using local start_time
        completed_at = datetime.now()
        duration = (completed_at - start_time).total_seconds()

        # Update job with success
        job_store.update_job(job_id, {
            "status": JobStatus.COMPLETED,
            "completed_at": completed_at.isoformat(),
            "duration_seconds": round(duration, 2),
            "result": {
                "rankings": rankings,
                "report_path": report_path,
                "execution_metadata": workflow_result.get("execution_metadata", {})
            }
        })

        logger.info("=" * 70)
        logger.info(f"JOB {job_id} COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Rankings: {len(rankings)}")
        logger.info(f"Report: {report_path}")

        # Log final rankings
        if rankings:
            logger.info("\nFinal Rankings:")
            for r in rankings:
                logger.info(
                    f"  {r['rank']}. {r['country_code']} - "
                    f"Score: {r['consensus_score']}/10"
                )

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)

        # Update job with error
        job_store.update_job(job_id, {
            "status": JobStatus.FAILED,
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })

        logger.error("=" * 70)
        logger.error(f"JOB {job_id} FAILED")
        logger.error("=" * 70)


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_rankings(workflow_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract and format rankings from LangGraph workflow result.

    Args:
        workflow_result: Complete state from LangGraph workflow

    Returns:
        List of formatted ranking dictionaries for API response
    """

    aggregated = workflow_result.get("aggregated_ranking", {})
    final_rankings = aggregated.get("final_rankings", [])

    if not final_rankings:
        logger.warning("No final rankings found in workflow result")
        return []

    # Get expert presentations for recommendations
    expert_presentations = workflow_result.get("expert_presentations", {})

    # Format rankings for API
    formatted_rankings = []

    for ranking in final_rankings:
        country_code = ranking["country_code"]

        # Get expert recommendation if available
        expert_rec = "N/A"
        if country_code in expert_presentations:
            expert_rec = expert_presentations[country_code].get("recommendation", "N/A")

        # Get peer agreement level
        agreement = ranking.get("peer_agreement", {})
        agreement_level = agreement.get("agreement_level", "unknown")

        formatted_rankings.append({
            "rank": ranking["rank"],
            "country_code": country_code,
            "consensus_score": ranking["consensus_score"],
            "average_peer_score": ranking["average_peer_score"],
            "agreement_level": agreement_level,
            "peer_scores": ranking.get("peer_scores", []),
            "expert_recommendation": expert_rec,
            "score_details": {
                "borda_points": ranking.get("borda_points", 0),
                "score_stddev": ranking.get("score_stddev", 0),
                "median_rank": ranking.get("median_rank", 0),
                "rank_variance": agreement.get("rank_variance", 0),
                "score_variance": agreement.get("score_variance", 0)
            }
        })

    return formatted_rankings


def _extract_rankings_legacy(workflow_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Legacy extraction for old workflow format (if needed for backwards compatibility).

    This is kept for reference but should not be needed with LangGraph.
    """

    final_rankings = workflow_result.get("final_rankings", [])
    expert_presentations = workflow_result.get("expert_presentations", {})
    peer_rankings = workflow_result.get("peer_rankings", [])

    formatted_rankings = []

    for ranking in final_rankings:
        country_code = ranking["country_code"]

        # Get expert recommendation
        expert_rec = "N/A"
        if country_code in expert_presentations:
            expert_rec = expert_presentations[country_code].get("recommendation", "N/A")

        # Get peer scores
        peer_scores = []
        for peer_ranking in peer_rankings:
            for country_rank in peer_ranking.get("rankings", []):
                if country_rank["country_code"] == country_code:
                    peer_scores.append(country_rank["score"])

        formatted_rankings.append({
            "rank": ranking["rank"],
            "country_code": country_code,
            "consensus_score": ranking["consensus_score"],
            "average_peer_score": ranking.get("average_peer_score", 0),
            "agreement_level": ranking["agreement_level"],
            "peer_scores": peer_scores,
            "expert_recommendation": expert_rec
        })

    return formatted_rankings


# ============================================================================
# Job Management Utilities
# ============================================================================

def get_job_summary(job_id: str) -> Dict[str, Any]:
    """
    Get a summary of job status and results.

    Args:
        job_id: Job identifier

    Returns:
        Dict with job summary
    """
    job = job_store.get_job(job_id)

    if not job:
        return {
            "found": False,
            "error": "Job not found"
        }

    summary = {
        "found": True,
        "job_id": job_id,
        "status": job["status"],
        "created_at": job["created_at"],
        "countries": job["countries"],
        "num_peer_rankers": job["num_peer_rankers"]
    }

    if job.get("started_at"):
        summary["started_at"] = job["started_at"]

    if job.get("completed_at"):
        summary["completed_at"] = job["completed_at"]
        summary["duration_seconds"] = job.get("duration_seconds", 0)

    if job["status"] == JobStatus.COMPLETED:
        result = job.get("result", {})
        rankings = result.get("rankings", [])

        summary["results"] = {
            "num_rankings": len(rankings),
            "top_choice": rankings[0]["country_code"] if rankings else None,
            "report_available": bool(result.get("report_path"))
        }

    if job["status"] == JobStatus.FAILED:
        summary["error"] = job.get("error", "Unknown error")

    if job.get("progress"):
        summary["progress"] = job["progress"]

    return summary


def cancel_job(job_id: str) -> bool:
    """
    Cancel a running job (if possible).

    Note: Current implementation doesn't support cancellation,
    but this provides the interface for future implementation.

    Args:
        job_id: Job identifier

    Returns:
        True if cancelled, False otherwise
    """
    job = job_store.get_job(job_id)

    if not job:
        return False

    if job["status"] not in [JobStatus.PENDING, JobStatus.RUNNING]:
        return False

    # TODO: Implement actual cancellation logic
    # For now, just mark as failed
    job_store.update_job(job_id, {
        "status": JobStatus.FAILED,
        "completed_at": datetime.now().isoformat(),
        "error": "Job cancelled by user"
    })

    return True


async def retry_job(job_id: str) -> str:
    """
    Retry a failed job.

    Args:
        job_id: Original job identifier

    Returns:
        New job ID
    """
    old_job = job_store.get_job(job_id)

    if not old_job:
        raise ValueError(f"Job {job_id} not found")

    # Create new job with same parameters
    from api.storage.job_store import generate_job_id

    new_job_id = generate_job_id()
    new_job = job_store.create_job(
        job_id=new_job_id,
        countries=old_job["countries"],
        num_peer_rankers=old_job["num_peer_rankers"]
    )

    # Process in background
    await process_ranking_job(new_job_id)

    return new_job_id


# ============================================================================
# Batch Processing
# ============================================================================

async def process_batch_jobs(job_ids: List[str], max_concurrent: int = 3):
    """
    Process multiple jobs with concurrency limit.

    Args:
        job_ids: List of job IDs to process
        max_concurrent: Maximum number of concurrent jobs
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(job_id: str):
        async with semaphore:
            await process_ranking_job(job_id)

    tasks = [process_with_semaphore(job_id) for job_id in job_ids]
    await asyncio.gather(*tasks)

    logger.info(f"Completed batch processing of {len(job_ids)} jobs")


# ============================================================================
# Health Check
# ============================================================================

def get_service_health() -> Dict[str, Any]:
    """
    Get health status of job service.

    Returns:
        Dict with health metrics
    """
    all_jobs = job_store.list_jobs(limit=100)

    status_counts = {
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0
    }

    for job in all_jobs:
        status = job["status"].lower()
        if status in status_counts:
            status_counts[status] += 1

    return {
        "status": "healthy",
        "total_jobs": len(all_jobs),
        "jobs_by_status": status_counts,
        "timestamp": datetime.now().isoformat()
    }