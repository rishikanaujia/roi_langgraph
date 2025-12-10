"""
Job Manager for Async Task Processing

Manages background jobs for long-running workflows.

Author: Kanauija
Date: 2024-12-08
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger("JobManager")


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    """Job container for tracking workflow execution."""

    def __init__(
            self,
            job_id: str,
            workflow_type: str,
            params: Dict[str, Any]
    ):
        self.job_id = job_id
        self.workflow_type = workflow_type
        self.params = params

        self.status = JobStatus.PENDING
        self.progress = 0
        self.current_stage = None

        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

        self.result = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "workflow_type": self.workflow_type,
            "params": self.params,
            "status": self.status.value,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


class JobManager:
    """
    Manages background jobs for async workflow execution.

    This is a simple in-memory job manager. For production, consider:
    - Redis for distributed job queuing
    - Celery for robust task management
    - Database for persistent job storage
    """

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.max_jobs = 1000  # Maximum jobs to keep in memory
        logger.info("Job Manager initialized")

    def create_job(
            self,
            workflow_type: str,
            params: Dict[str, Any]
    ) -> str:
        """Create a new job."""
        # Generate unique job ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        job_id = f"{workflow_type}_{timestamp}_{unique_id}"

        # Create job
        job = Job(job_id, workflow_type, params)
        self.jobs[job_id] = job

        logger.info(f"Created job: {job_id}")

        # Cleanup old jobs if needed
        self._cleanup_old_jobs()

        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def update_job_status(
            self,
            job_id: str,
            status: JobStatus,
            progress: Optional[int] = None,
            current_stage: Optional[str] = None,
            error: Optional[str] = None
    ):
        """Update job status."""
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Job not found: {job_id}")
            return

        job.status = status

        if progress is not None:
            job.progress = progress

        if current_stage is not None:
            job.current_stage = current_stage

        if error is not None:
            job.error = error

        # Update timestamps
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.now()

        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.now()

    def set_job_result(self, job_id: str, result: Any):
        """Set job result."""
        job = self.jobs.get(job_id)
        if job:
            job.result = result

    def get_job_result(self, job_id: str) -> Optional[Any]:
        """Get job result."""
        job = self.jobs.get(job_id)
        return job.result if job else None

    def list_jobs(
            self,
            workflow_type: Optional[str] = None,
            status: Optional[JobStatus] = None,
            limit: int = 50
    ) -> list[Job]:
        """List jobs with optional filters."""
        jobs = list(self.jobs.values())

        # Filter by workflow type
        if workflow_type:
            jobs = [j for j in jobs if j.workflow_type == workflow_type]

        # Filter by status
        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        # Limit results
        return jobs[:limit]

    def _cleanup_old_jobs(self):
        """Cleanup old completed jobs to prevent memory bloat."""
        if len(self.jobs) <= self.max_jobs:
            return

        # Get completed jobs sorted by completion time
        completed_jobs = [
            (job_id, job)
            for job_id, job in self.jobs.items()
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
        ]

        completed_jobs.sort(key=lambda x: x[1].completed_at or datetime.now())

        # Remove oldest completed jobs
        num_to_remove = len(self.jobs) - self.max_jobs
        for i in range(num_to_remove):
            job_id = completed_jobs[i][0]
            del self.jobs[job_id]
            logger.info(f"Cleaned up old job: {job_id}")


# Global job manager instance
job_manager = JobManager()