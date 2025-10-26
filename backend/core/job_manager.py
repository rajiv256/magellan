import json
import redis
from typing import Optional, List
from datetime import datetime
from backend.api.models import DesignJobResult, JobStatus


class JobManager:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )

    def create_job(self, job_id: str, job_data: dict) -> str:
        """Create a new job entry"""
        job_data['job_id'] = job_id
        job_data['status'] = JobStatus.PENDING
        job_data['created_at'] = datetime.utcnow().isoformat()

        self.redis_client.hset('jobs', job_id, json.dumps(job_data))
        self.redis_client.lpush('job_queue', job_id)

        return job_id

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job by ID"""
        job_data = self.redis_client.hget('jobs', job_id)
        if job_data:
            return json.loads(job_data)
        return None

    def update_job_status(self, job_id: str, status: JobStatus,
                          error: Optional[str] = None,
                          result_domains: List[dict] = None,
                          result_strands: List[dict] = None,
                          raw_output: Optional[str] = None):
        """Update job status and results"""
        job_data = self.get_job(job_id)
        if not job_data:
            raise ValueError(f"Job {job_id} not found")

        job_data['status'] = status
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job_data['completed_at'] = datetime.utcnow().isoformat()

        if error:
            job_data['error'] = error
        if result_domains:
            job_data['result_domains'] = result_domains
        if result_strands:
            job_data['result_strands'] = result_strands
        if raw_output:
            job_data['raw_output'] = raw_output

        self.redis_client.hset('jobs', job_id, json.dumps(job_data))

    def get_all_jobs(self, window=100) -> List[dict]:
        """Get all jobs"""
        jobs = []
        for job_id in self.redis_client.hkeys('jobs'):
            job_data = self.get_job(job_id)
            if job_data:
                jobs.append(job_data)

        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jobs[:window]