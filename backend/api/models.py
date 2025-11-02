from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union, Literal
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


# Analysis-related models

class StrandModel(BaseModel):
    """Model for a DNA/RNA strand with name and sequence"""
    name: str
    sequence: str

    @validator('sequence')
    def validate_sequence(cls, v, values):
        """Validate that the sequence contains valid nucleotides"""
        if not v:
            raise ValueError("Sequence cannot be empty")

        # Check for valid nucleotides (allowing both DNA and RNA)
        if not re.match(r'^[ATGCUatgcu]+$', v):
            raise ValueError("Sequence must contain only valid nucleotides (A, T, G, C, U)")

        return v.upper()


class AnalysisRequest(BaseModel):
    """Request model for nucleic acid structure analysis"""
    strands: List[StrandModel]
    temperature: float = Field(37.0, description="Temperature in degrees Celsius", ge=0, le=100)
    sodium: float = Field(1.0, description="Sodium concentration in molar", ge=0)
    magnesium: float = Field(0.0, description="Magnesium concentration in molar", ge=0)
    material: Literal["dna", "rna"] = Field("dna", description="Material type: 'dna' or 'rna'")
    strand_concentrations: Dict[str, float] = Field(
        default_factory=dict,
        description="Strand concentrations in molar, keyed by strand name"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strands": [
                    {"name": "strand1", "sequence": "ATGCATGCATGC"},
                    {"name": "strand2", "sequence": "GCATGCATGCAT"}
                ],
                "temperature": 37.0,
                "sodium": 1.0,
                "magnesium": 0.0,
                "material": "dna",
                "strand_concentrations": {
                    "strand1": 1e-6,
                    "strand2": 1e-6
                }
            }
        }


class MFEResult(BaseModel):
    """Model for Minimum Free Energy structure results"""
    structure: str
    energy: float
    pairs: List[List[int]]
    probabilities: Optional[List[float]] = None


class PairProbability(BaseModel):
    """Model for base pair probability"""
    i: int
    probability: float


class EnsembleResult(BaseModel):
    """Model for ensemble properties"""
    free_energy: float
    partition_function: float
    pair_probabilities: Optional[List[PairProbability]] = None


class SuboptimalStructure(BaseModel):
    """Model for a suboptimal structure"""
    structure: str
    energy: float


class ConcentrationResult(BaseModel):
    """Model for concentration results"""
    name: str
    concentration: float


class RateModel(BaseModel):
    """Model for kinetic rate information"""
    from_state: str = Field(..., alias="from")
    to_state: str = Field(..., alias="to")
    rate: float

    class Config:
        allow_population_by_field_name = True


class KineticsResult(BaseModel):
    """Model for kinetics results"""
    rates: List[RateModel]


class AnalysisResult(BaseModel):
    """Complete model for analysis results"""
    mfe: MFEResult
    ensemble: Optional[EnsembleResult] = None
    suboptimal: Optional[List[SuboptimalStructure]] = None
    concentrations: Optional[Dict[str, List[ConcentrationResult]]] = None
    melting: Optional[Dict[str, List[float]]] = None
    kinetics: Optional[KineticsResult] = None
    execution_time: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "mfe": {
                    "structure": "(((...)))",
                    "energy": -8.5,
                    "pairs": [[1, 9], [2, 8], [3, 7]]
                },
                "ensemble": {
                    "free_energy": -9.2,
                    "partition_function": 345600.0
                },
                "execution_time": 1.23
            }
        }


class AnalysisJobResult(BaseModel):
    """Model for analysis job results in the job system"""
    job_id: str
    status: JobStatus
    name: str
    job_type: str = "analysis"
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    analysis_results: Optional[AnalysisResult] = None
    raw_output: Optional[str] = None
    strands: List[StrandModel]
    temperature: float
    sodium: float
    magnesium: float
    material: str
    strand_concentrations: Dict[str, float] = {}