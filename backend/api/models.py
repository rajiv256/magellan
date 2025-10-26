from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
import re


class DomainCreate(BaseModel):
    name: str
    code: str

    @validator('code')
    def validate_code(cls, v):
        if not re.match(r'^([MRWSYKVHDBNATGCU][0-9]*)+$', v):
            raise ValueError('Invalid domain code format')
        return v


class Domain(DomainCreate):
    id: str


class StrandCreate(BaseModel):
    name: str
    domains: str  # comma-separated, e.g., "dx,~dy,dz"


class Strand(StrandCreate):
    id: str


class ComplexCreate(BaseModel):
    name: str
    strands: str  # comma-separated strand names
    structure: str  # DU+ notation

    @validator('structure')
    def validate_structure(cls, v):
        # Basic validation for DU+ notation
        # if not all(c in 'DU+()' for c in v.replace(' ', '')):
        #     raise ValueError('Structure must use DU+ notation')
        return v


class Complex(ComplexCreate):
    id: str


class ConstraintType(str, Enum):
    # Hard constraints
    MATCH = "Match"
    COMPLEMENTARITY = "Complementarity"
    SIMILARITY = "Similarity"
    LIBRARY = "Library"
    WINDOW = "Window"
    PATTERN = "Pattern"
    DIVERSITY = "Diversity"

    # Soft constraints
    SSM = "SSM"
    ENERGY_MATCH = "EnergyMatch"


class Constraint(BaseModel):
    type: ConstraintType
    is_hard: bool
    params: Dict[str, Any]


class OffTargets(BaseModel):
    max_size: int = Field(3, description="Maximum number of strands in off-target complexes")
    excludes: List[List[str]] = Field(default_factory=list,
                                      description="List of strand groups to exclude as off-targets")
class DesignJobCreate(BaseModel):
    name: str
    domains: List[Domain]
    strands: List[Strand]
    complexes: List[Complex]
    base_concentration: float = 1e-7
    custom_concentrations: Dict[str, float] = {}
    hard_constraints: List[Constraint] = []
    soft_constraints: List[Constraint] = []
    # Add this field - it was missing!
    off_targets: Optional[OffTargets] = Field(
        default_factory=lambda: {"max_size": 3, "excludes": []},
        description="Off-targets configuration"
    )
    trials: int = 3
    f_stop: float = 0.01
    seed: int = 93


class JobStatus(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class ResultDomain(BaseModel):
    name: str
    sequence: str


class ResultStrand(BaseModel):
    name: str
    sequence: str


class DesignJobResult(BaseModel):
    job_id: str
    status: JobStatus
    name: str
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result_domains: List[ResultDomain] = []
    result_strands: List[ResultStrand] = []
    raw_output: Optional[str] = None