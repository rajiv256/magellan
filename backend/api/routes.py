from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union, Literal
import primer3
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


class DimerAnalysisRequest(BaseModel):
    seq1: str
    seq2: Optional[str] = None  # Optional for homodimer analysis
    mv_conc: float = Field(50.0, description="Monovalent cation concentration in mM")
    dv_conc: float = Field(1.5, description="Divalent cation concentration in mM")
    dntp_conc: float = Field(0.6, description="dNTP concentration in mM")
    dna_conc: float = Field(50.0, description="DNA concentration in nM")
    temp_c: float = Field(37.0, description="Temperature in Celsius")
    max_loop: int = Field(30, description="Maximum size of loops in structures")
    output_structure: bool = Field(True, description="Whether to output ASCII structure")
    material: Literal["dna", "rna"] = Field("dna", description="Material type (DNA or RNA)")


class AnalysisResponse(BaseModel):
    tm: float
    dg: float
    dh: float
    ds: float
    structure_found: bool
    ascii_structure_lines: Optional[List[str]] = None


@router.post("/analyze/heterodimer", response_model=AnalysisResponse)
async def analyze_heterodimer(request: DimerAnalysisRequest):
    """
    Analyze heterodimer formation between two DNA/RNA sequences using Primer3.
    """
    try:
        # Validate input
        if len(request.seq1) == 0 or len(request.seq2) == 0:
            raise HTTPException(status_code=400, detail="Empty sequence provided")

        # Check if sequences are valid DNA/RNA
        validate_sequence(request.seq1, request.material)
        validate_sequence(request.seq2, request.material)

        # Enforce Primer3 length limitation (<60 bp for at least one strand)
        if len(request.seq1) >= 60 and len(request.seq2) >= 60:
            # Truncate the longer sequence to 60bp with warning
            if len(request.seq1) > len(request.seq2):
                print(
                    f"Warning: Truncating seq1 from {len(request.seq1)}bp to 60bp to comply with Primer3 requirements")
                request.seq1 = request.seq1[:60]
            else:
                print(
                    f"Warning: Truncating seq2 from {len(request.seq2)}bp to 60bp to comply with Primer3 requirements")
                request.seq2 = request.seq2[:60]

        # RNA -> DNA conversion if needed
        if request.material == "rna":
            seq1_dna = rna_to_dna(request.seq1)
            seq2_dna = rna_to_dna(request.seq2)
        else:
            seq1_dna = request.seq1
            seq2_dna = request.seq2

        # Call Primer3 for heterodimer analysis
        try:
            result = primer3.bindings.calc_end_stability(
                seq1=seq1_dna,
                seq2=seq2_dna,
                mv_conc=request.mv_conc,
                dv_conc=request.dv_conc,
                dntp_conc=request.dntp_conc,
                dna_conc=request.dna_conc,
                temp_c=request.temp_c,
                max_loop=request.max_loop,
                output_structure=request.output_structure
            )

            # Convert ThermoResult to dictionary
            result_dict = result.todict()

            # Prepare the response
            response = {
                "tm": result_dict.get("tm", 0.0),
                "dg": result_dict.get("dg", 0.0),
                "dh": result_dict.get("dh", 0.0),
                "ds": result_dict.get("ds", 0.0),
                "structure_found": result_dict.get("structure_found", False),
                "ascii_structure_lines": result_dict.get("ascii_structure_lines", None)
            }

            return response

        except RuntimeError as e:
            # Handle Primer3 specific errors
            raise HTTPException(status_code=400, detail=f"Primer3 error: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error in heterodimer analysis: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/homodimer", response_model=AnalysisResponse)
async def analyze_homodimer(request: DimerAnalysisRequest):
    """
    Analyze homodimer (self-complementarity) of a DNA/RNA sequence using Primer3.
    """
    try:
        # Validate input
        if len(request.seq1) == 0:
            raise HTTPException(status_code=400, detail="Empty sequence provided")

        # Check if sequence is valid DNA/RNA
        validate_sequence(request.seq1, request.material)

        # RNA -> DNA conversion if needed
        if request.material == "rna":
            seq1_dna = rna_to_dna(request.seq1)
        else:
            seq1_dna = request.seq1

        # Call Primer3 for homodimer analysis
        try:
            result = primer3.bindings.calc_end_stability(
                seq1=seq1_dna,
                seq2=seq1_dna,
                mv_conc=request.mv_conc,
                dv_conc=request.dv_conc,
                dntp_conc=request.dntp_conc,
                dna_conc=request.dna_conc,
                temp_c=request.temp_c,
                max_loop=request.max_loop,
                output_structure=request.output_structure
            )

            # Convert ThermoResult to dictionary
            result_dict = result.todict()

            # Prepare the response
            response = {
                "tm": result_dict.get("tm", 0.0),
                "dg": result_dict.get("dg", 0.0),
                "dh": result_dict.get("dh", 0.0),
                "ds": result_dict.get("ds", 0.0),
                "structure_found": result_dict.get("structure_found", False),
                "ascii_structure_lines": result_dict.get("ascii_structure_lines", None)
            }

            return response

        except RuntimeError as e:
            # Handle Primer3 specific errors
            raise HTTPException(status_code=400, detail=f"Primer3 error: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error in homodimer analysis: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/hairpin", response_model=AnalysisResponse)
async def analyze_hairpin(request: DimerAnalysisRequest):
    """
    Analyze hairpin formation of a DNA/RNA sequence using Primer3.
    """
    try:
        # Validate input
        if len(request.seq1) == 0:
            raise HTTPException(status_code=400, detail="Empty sequence provided")

        # Check if sequence is valid DNA/RNA
        validate_sequence(request.seq1, request.material)

        # RNA -> DNA conversion if needed
        if request.material == "rna":
            seq1_dna = rna_to_dna(request.seq1)
        else:
            seq1_dna = request.seq1

        # Call Primer3 for hairpin analysis
        try:
            result = primer3.bindings.calc_hairpin(
                seq=seq1_dna,
                mv_conc=request.mv_conc,
                dv_conc=request.dv_conc,
                dntp_conc=request.dntp_conc,
                dna_conc=request.dna_conc,
                temp_c=request.temp_c,
                max_loop=request.max_loop,
                output_structure=request.output_structure
            )

            # Convert ThermoResult to dictionary
            result_dict = result.todict()

            # Prepare the response
            response = {
                "tm": result_dict.get("tm", 0.0),
                "dg": result_dict.get("dg", 0.0),
                "dh": result_dict.get("dh", 0.0),
                "ds": result_dict.get("ds", 0.0),
                "structure_found": result_dict.get("structure_found", False),
                "ascii_structure_lines": result_dict.get("ascii_structure_lines", None)
            }

            return response

        except RuntimeError as e:
            # Handle Primer3 specific errors
            raise HTTPException(status_code=400, detail=f"Primer3 error: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error in hairpin analysis: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=str(e))


def validate_sequence(sequence: str, material: str):
    """Validate that the sequence contains valid nucleotides"""
    if material == "dna":
        valid_chars = set("ATGC")
    else:  # RNA
        valid_chars = set("AUGC")

    # Check if all characters in the sequence are valid nucleotides
    if not all(c.upper() in valid_chars for c in sequence):
        invalid_chars = [c for c in sequence.upper() if c not in valid_chars]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {material.upper()} sequence. Contains invalid characters: {', '.join(set(invalid_chars))}"
        )


def rna_to_dna(sequence: str) -> str:
    """Convert RNA sequence to DNA for Primer3 processing"""
    return sequence.upper().replace("U", "T")


# Add these imports at the top of your file
try:
    import nupack

    NUPACK_AVAILABLE = True
except ImportError:
    NUPACK_AVAILABLE = False
    print("Warning: Nupack package not installed. Will use mock data for Nupack analysis.")


# Add these Pydantic models
class Strand(BaseModel):
    name: str
    sequence: str


class Complex(BaseModel):
    name: str
    strands: List[str]


class NupackParameters(BaseModel):
    celsius: float = 37.0
    material: Literal["dna", "rna"] = "dna"
    sodium: float = 0.05  # M
    magnesium: float = 0.0015  # M


class NupackEquilibriumRequest(BaseModel):
    strands: List[Strand]
    complexes: List[Complex]
    concentrations: List[float]
    parameters: NupackParameters = Field(default_factory=NupackParameters)


class NupackEquilibriumResponse(BaseModel):
    equilibrium_concentrations: Dict[str, float]
    free_energy: Optional[float] = None
    duplex_fraction: Optional[float] = None
    secondary_structure: Optional[str] = None
    error: Optional[str] = None
    mock_data: bool = False