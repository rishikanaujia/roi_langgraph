"""
Job Processing Service

Handles background job execution for ranking workflows.
"""

import asyncio
from datetime import datetime
import logging

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.workflows.phase1_workflow import Phase1Workflow
from api.storage.job_store import get_job_store
from api.services.research_service import generate_research_data
from api.models.schemas import JobStatus

logger = logging.getLogger(__name__)


async def process_ranking_job(job_id: str):
    """Process ranking job in background."""

    job_store = get_job_store()
    job = job_store.get_job(job_id)

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        logger.info(f"Starting job {job_id}")

        # Update status to running
        job_store.update_job(job_id, {
            "status": JobStatus.RUNNING,
            "started_at": datetime.now().isoformat()
        })

        # Create workflow
        workflow = Phase1Workflow(num_peer_rankers=job["num_peer_rankers"])

        # Generate research data
        research_data = generate_research_data(job["countries"])

        # Run workflow
        result = await workflow.run_async(
            countries=job["countries"],
            research_json_data=research_data
        )

        # Update progress from workflow state
        if "execution_metadata" in result:
            stage_timings = result["execution_metadata"].get("stage_timings", {})
            for stage in stage_timings:
                job_store.update_progress(job_id, stage, "complete")

        # Extract rankings
        rankings = _extract_rankings(result)

        # Get report path
        report_path = result.get("report_metadata", {}).get("filepath")

        # Calculate duration
        start_time = datetime.fromisoformat(job["started_at"])
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Update job with results
        job_store.update_job(job_id, {
            "status": JobStatus.COMPLETED,
            "completed_at": end_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "result": {
                "rankings": rankings,
                "report_path": report_path,
                "execution_metadata": result.get("execution_metadata", {})
            }
        })

        logger.info(f"Job {job_id} completed successfully in {duration:.2f}s")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)

        # Update job with error
        job_store.update_job(job_id, {
            "status": JobStatus.FAILED,
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


def _extract_rankings(result: dict) -> list:
    """Extract rankings from workflow result."""
    rankings = []

    if result.get("aggregated_ranking"):
        for r in result["aggregated_ranking"].get("final_rankings", []):
            # Get expert recommendation
            expert_rec = None
            if r["country_code"] in result.get("expert_presentations", {}):
                expert_rec = result["expert_presentations"][r["country_code"]].get("recommendation")

            rankings.append({
                "rank": r["rank"],
                "country_code": r["country_code"],
                "consensus_score": round(r["consensus_score"], 2),
                "average_peer_score": round(r["average_peer_score"], 2),
                "agreement_level": r["peer_agreement"]["agreement_level"],
                "peer_scores": [round(s, 1) for s in r["peer_scores"]],
                "expert_recommendation": expert_rec
            })

    return rankings