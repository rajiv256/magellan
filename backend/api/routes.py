from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.api.models import DesignJobCreate, DesignJobResult, JobStatus
from backend.core.job_manager import JobManager
from backend.core.design_runner import DesignRunner
import uuid
import traceback

router = APIRouter()
job_manager = JobManager()
design_runner = DesignRunner()


def run_design_task(job_id: str):
    """Background task to run the design"""
    try:
        # Update status to running
        job_manager.update_job_status(job_id, JobStatus.RUNNING)

        # Get job data
        job_data = job_manager.get_job(job_id)

        # Run design
        result = design_runner.run_design(job_data)

        # Update with results
        if result['success']:
            job_manager.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                result_domains=result['result_domains'],
                result_strands=result['result_strands'],
                raw_output=result.get('raw_output')
            )
        else:
            job_manager.update_job_status(
                job_id,
                JobStatus.FAILED,
                error=result['error']
            )

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"Error in design task: {error_msg}")
        job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            error=error_msg
        )


@router.post("/design")
async def create_design_job(job: DesignJobCreate,
                            background_tasks: BackgroundTasks):
    """Create a new design job"""
    try:
        job_id = str(uuid.uuid4())
        print("This is the raw received data", job)
        # Convert to dict
        job_dict = job.model_dump()

        print(f"Received job data: {job_dict}")  # Debug logging

        # Create job
        job_manager.create_job(job_id, job_dict)

        # Add background task
        background_tasks.add_task(run_design_task, job_id)

        return {"job_id": job_id, "status": "submitted"}

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"Error creating job: {error_msg}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs")
async def get_all_jobs():
    """Get all jobs"""
    return job_manager.get_all_jobs()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get a specific job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job