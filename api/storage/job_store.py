"""
Job Storage

In-memory job store with optional Redis backend support.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging

from api.models.schemas import JobStatus

logger = logging.getLogger(__name__)


class JobStore:
    """In-memory job store."""

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(
            self,
            job_id: str,
            countries: list[str],
            num_peer_rankers: int
    ) -> Dict[str, Any]:
        """Create a new job."""
        job = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "countries": countries,
            "num_peer_rankers": num_peer_rankers,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "duration_seconds": None,
            "progress": {
                "research": "pending",
                "presentations": "pending",
                "rankings": "pending",
                "aggregation": "pending",
                "report_generation": "pending"
            },
            "result": None,
            "error": None
        }
        self.jobs[job_id] = job
        logger.info(f"Created job {job_id} for {len(countries)} countries")
        return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def update_job(self, job_id: str, updates: Dict[str, Any]):
        """Update job."""
        if job_id in self.jobs:
            self.jobs[job_id].update(updates)
            logger.debug(f"Updated job {job_id}: {list(updates.keys())}")

    def update_progress(self, job_id: str, stage: str, status: str):
        """Update job progress."""
        if job_id in self.jobs:
            self.jobs[job_id]["progress"][stage] = status
            logger.debug(f"Job {job_id}: {stage} -> {status}")

    def list_jobs(self, limit: int = 100) -> list[Dict[str, Any]]:
        """List all jobs."""
        jobs = list(self.jobs.values())
        # Sort by created_at descending
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        return jobs[:limit]


# Global job store instance
job_store = JobStore()


def get_job_store() -> JobStore:
    """Get job store instance."""
    return job_store