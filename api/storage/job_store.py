"""
Job Store - In-Memory Job Storage with Redis Option

Manages ranking job storage and retrieval.

Features:
- In-memory storage (default)
- Redis backend (optional, for production)
- CRUD operations
- Progress tracking
- Job listing and filtering
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import OrderedDict
import uuid

from api.models.schemas import JobStatus

logger = logging.getLogger("JobStore")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Job ID Generator
# ============================================================================

def generate_job_id() -> str:
    """
    Generate a unique job ID.

    Returns:
        Unique job ID (e.g., "job_abc123def456")
    """
    return f"job_{uuid.uuid4().hex[:12]}"


# ============================================================================
# In-Memory Job Store
# ============================================================================

class InMemoryJobStore:
    """
    In-memory storage for ranking jobs.

    Uses OrderedDict to maintain insertion order.
    Thread-safe for single-process deployments.

    For multi-process/distributed deployments, use RedisJobStore instead.
    """

    def __init__(self, max_jobs: int = 1000):
        """
        Initialize in-memory job store.

        Args:
            max_jobs: Maximum number of jobs to keep (oldest deleted first)
        """
        self.jobs: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_jobs = max_jobs

        logger.info("=" * 70)
        logger.info("JOB STORE INITIALIZED - In-Memory")
        logger.info("=" * 70)
        logger.info(f"Max jobs: {max_jobs}")
        logger.info(f"Storage: In-Memory (single process)")
        logger.info("=" * 70)

    def create_job(
            self,
            job_id: str,
            countries: List[str],
            num_peer_rankers: int
    ) -> Dict[str, Any]:
        """
        Create a new ranking job.

        Args:
            job_id: Unique job identifier
            countries: List of country codes
            num_peer_rankers: Number of peer rankers

        Returns:
            Created job dictionary
        """

        # Check if job already exists
        if job_id in self.jobs:
            logger.warning(f"Job {job_id} already exists")
            raise ValueError(f"Job {job_id} already exists")

        # Create job
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

        # Add to store
        self.jobs[job_id] = job

        # Enforce max jobs limit
        if len(self.jobs) > self.max_jobs:
            # Remove oldest job
            oldest_job_id = next(iter(self.jobs))
            removed_job = self.jobs.pop(oldest_job_id)
            logger.info(f"Removed oldest job to maintain limit: {oldest_job_id}")

        logger.info(f"✅ Created job: {job_id}")
        logger.info(f"   Countries: {countries}")
        logger.info(f"   Peer rankers: {num_peer_rankers}")
        logger.info(f"   Total jobs: {len(self.jobs)}")

        return job.copy()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job dictionary or None if not found
        """
        job = self.jobs.get(job_id)

        if job:
            return job.copy()

        return None

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update job fields.

        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if job not found
        """

        if job_id not in self.jobs:
            logger.warning(f"Cannot update non-existent job: {job_id}")
            return False

        # Update fields
        self.jobs[job_id].update(updates)

        logger.debug(f"Updated job {job_id}: {list(updates.keys())}")

        return True

    def update_progress(
            self,
            job_id: str,
            stage: str,
            status: str
    ) -> bool:
        """
        Update progress for a specific stage.

        Args:
            job_id: Job identifier
            stage: Stage name (research, presentations, rankings, aggregation, report_generation)
            status: Status (pending, in_progress, complete)

        Returns:
            True if updated, False if job not found
        """

        if job_id not in self.jobs:
            logger.warning(f"Cannot update progress for non-existent job: {job_id}")
            return False

        # Valid stages
        valid_stages = [
            "research",
            "presentations",
            "rankings",
            "aggregation",
            "report_generation"
        ]

        if stage not in valid_stages:
            logger.warning(f"Invalid stage: {stage}")
            return False

        # Update progress
        self.jobs[job_id]["progress"][stage] = status

        logger.debug(f"Job {job_id}: {stage} -> {status}")

        return True

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """

        if job_id not in self.jobs:
            logger.warning(f"Cannot delete non-existent job: {job_id}")
            return False

        del self.jobs[job_id]

        logger.info(f"🗑️  Deleted job: {job_id}")
        logger.info(f"   Total jobs: {len(self.jobs)}")

        return True

    def list_jobs(
            self,
            limit: int = 100,
            status: Optional[JobStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by status.

        Args:
            limit: Maximum number of jobs to return
            status: Filter by status (optional)

        Returns:
            List of job dictionaries (most recent first)
        """

        # Get all jobs
        all_jobs = list(self.jobs.values())

        # Filter by status if specified
        if status:
            all_jobs = [job for job in all_jobs if job["status"] == status]

        # Sort by created_at (most recent first)
        all_jobs.sort(
            key=lambda x: x["created_at"],
            reverse=True
        )

        # Apply limit
        result = all_jobs[:limit]

        logger.debug(f"Listed {len(result)} jobs (total: {len(self.jobs)})")

        return [job.copy() for job in result]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats
        """

        # Count by status
        status_counts = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0
        }

        for job in self.jobs.values():
            status = job["status"].lower()
            if status in status_counts:
                status_counts[status] += 1

        return {
            "total_jobs": len(self.jobs),
            "max_jobs": self.max_jobs,
            "usage_percent": (len(self.jobs) / self.max_jobs) * 100,
            "status_counts": status_counts,
            "storage_type": "in_memory"
        }

    def clear_completed(self, older_than_hours: int = 24) -> int:
        """
        Clear completed jobs older than specified hours.

        Args:
            older_than_hours: Delete jobs completed more than this many hours ago

        Returns:
            Number of jobs deleted
        """

        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        jobs_to_delete = []

        for job_id, job in self.jobs.items():
            if job["status"] == JobStatus.COMPLETED and job.get("completed_at"):
                completed_at = datetime.fromisoformat(job["completed_at"])
                if completed_at < cutoff_time:
                    jobs_to_delete.append(job_id)

        # Delete jobs
        for job_id in jobs_to_delete:
            del self.jobs[job_id]

        if jobs_to_delete:
            logger.info(f"🗑️  Cleared {len(jobs_to_delete)} completed jobs older than {older_than_hours}h")

        return len(jobs_to_delete)


# ============================================================================
# Redis Job Store (Optional - for Production)
# ============================================================================

class RedisJobStore:
    """
    Redis-backed storage for ranking jobs.

    Features:
    - Persistent storage
    - Multi-process safe
    - Distributed deployment support
    - TTL (Time To Live) for automatic cleanup

    Requires: pip install redis
    """

    def __init__(
            self,
            redis_url: str = "redis://localhost:6379/0",
            key_prefix: str = "roi:job:",
            default_ttl: int = 86400  # 24 hours
    ):
        """
        Initialize Redis job store.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all job keys
            default_ttl: Default TTL in seconds (None = no expiration)
        """
        try:
            import redis

            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.key_prefix = key_prefix
            self.default_ttl = default_ttl

            # Test connection
            self.redis_client.ping()

            logger.info("=" * 70)
            logger.info("JOB STORE INITIALIZED - Redis")
            logger.info("=" * 70)
            logger.info(f"Redis URL: {redis_url}")
            logger.info(f"Key prefix: {key_prefix}")
            logger.info(f"Default TTL: {default_ttl}s ({default_ttl / 3600:.1f}h)")
            logger.info("=" * 70)

        except ImportError:
            logger.error("Redis not installed. Run: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _get_key(self, job_id: str) -> str:
        """Get Redis key for job ID."""
        return f"{self.key_prefix}{job_id}"

    def create_job(
            self,
            job_id: str,
            countries: List[str],
            num_peer_rankers: int
    ) -> Dict[str, Any]:
        """Create a new ranking job in Redis."""

        key = self._get_key(job_id)

        # Check if exists
        if self.redis_client.exists(key):
            logger.warning(f"Job {job_id} already exists")
            raise ValueError(f"Job {job_id} already exists")

        # Create job
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

        # Store in Redis with TTL
        self.redis_client.set(
            key,
            json.dumps(job),
            ex=self.default_ttl
        )

        # Add to index (sorted set by created_at)
        self.redis_client.zadd(
            f"{self.key_prefix}index",
            {job_id: datetime.now().timestamp()}
        )

        logger.info(f"✅ Created job in Redis: {job_id}")

        return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job from Redis."""

        key = self._get_key(job_id)
        job_json = self.redis_client.get(key)

        if not job_json:
            return None

        return json.loads(job_json)

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job fields in Redis."""

        key = self._get_key(job_id)
        job_json = self.redis_client.get(key)

        if not job_json:
            logger.warning(f"Cannot update non-existent job: {job_id}")
            return False

        # Load, update, save
        job = json.loads(job_json)
        job.update(updates)

        self.redis_client.set(
            key,
            json.dumps(job),
            ex=self.default_ttl
        )

        logger.debug(f"Updated job in Redis: {job_id}")

        return True

    def update_progress(
            self,
            job_id: str,
            stage: str,
            status: str
    ) -> bool:
        """Update progress for a specific stage in Redis."""

        job = self.get_job(job_id)

        if not job:
            logger.warning(f"Cannot update progress for non-existent job: {job_id}")
            return False

        job["progress"][stage] = status

        return self.update_job(job_id, {"progress": job["progress"]})

    def delete_job(self, job_id: str) -> bool:
        """Delete a job from Redis."""

        key = self._get_key(job_id)

        # Delete from main store
        deleted = self.redis_client.delete(key)

        # Delete from index
        self.redis_client.zrem(f"{self.key_prefix}index", job_id)

        if deleted:
            logger.info(f"🗑️  Deleted job from Redis: {job_id}")

        return bool(deleted)

    def list_jobs(
            self,
            limit: int = 100,
            status: Optional[JobStatus] = None
    ) -> List[Dict[str, Any]]:
        """List all jobs from Redis (most recent first)."""

        # Get job IDs from index (sorted by timestamp, newest first)
        job_ids = self.redis_client.zrevrange(
            f"{self.key_prefix}index",
            0,
            -1  # All jobs
        )

        # Get jobs
        jobs = []
        for job_id in job_ids:
            job = self.get_job(job_id)
            if job:
                # Filter by status if specified
                if status is None or job["status"] == status:
                    jobs.append(job)

                # Stop if we have enough
                if len(jobs) >= limit:
                    break

        logger.debug(f"Listed {len(jobs)} jobs from Redis")

        return jobs

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis storage statistics."""

        # Get total jobs
        total_jobs = self.redis_client.zcard(f"{self.key_prefix}index")

        # Count by status (requires scanning all jobs)
        job_ids = self.redis_client.zrange(f"{self.key_prefix}index", 0, -1)

        status_counts = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0
        }

        for job_id in job_ids:
            job = self.get_job(job_id)
            if job:
                status = job["status"].lower()
                if status in status_counts:
                    status_counts[status] += 1

        # Get Redis memory info
        memory_info = self.redis_client.info("memory")

        return {
            "total_jobs": total_jobs,
            "status_counts": status_counts,
            "storage_type": "redis",
            "redis_memory_used": memory_info.get("used_memory_human", "unknown"),
            "default_ttl_hours": self.default_ttl / 3600
        }

    def clear_completed(self, older_than_hours: int = 24) -> int:
        """Clear completed jobs older than specified hours from Redis."""

        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cutoff_timestamp = cutoff_time.timestamp()

        # Get old job IDs
        old_job_ids = self.redis_client.zrangebyscore(
            f"{self.key_prefix}index",
            0,
            cutoff_timestamp
        )

        # Delete completed jobs
        deleted_count = 0
        for job_id in old_job_ids:
            job = self.get_job(job_id)
            if job and job["status"] == JobStatus.COMPLETED:
                self.delete_job(job_id)
                deleted_count += 1

        if deleted_count:
            logger.info(
                f"🗑️  Cleared {deleted_count} completed jobs from Redis "
                f"older than {older_than_hours}h"
            )

        return deleted_count


# ============================================================================
# Job Store Factory
# ============================================================================

def create_job_store(storage_backend: str = "memory", **kwargs) -> InMemoryJobStore:
    """
    Factory function to create appropriate job store.

    Args:
        storage_backend: "memory" or "redis"
        **kwargs: Additional arguments for store initialization

    Returns:
        Job store instance
    """

    if storage_backend == "redis":
        return RedisJobStore(**kwargs)
    elif storage_backend == "memory":
        return InMemoryJobStore(**kwargs)
    else:
        raise ValueError(f"Unknown storage backend: {storage_backend}")


# ============================================================================
# Global Job Store Instance
# ============================================================================

# Default: In-Memory store
# For production with Redis, set in config and create with:
# job_store = create_job_store("redis", redis_url="redis://localhost:6379/0")

job_store = InMemoryJobStore(max_jobs=1000)