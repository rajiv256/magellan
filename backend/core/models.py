"""
Updated data models for OligoDesigner with new validation settings
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class Domain:
    id: int
    name: str
    length: int
    sequence: str = ""
    role: str = "binding"
    isComplement: bool = False
    complementOf: Optional[int] = None


@dataclass
class Strand:
    id: int
    name: str
    domainIds: List[int]
    sequence: str = ""
    validated: bool = False


@dataclass
class ValidationSettings:
    # Core settings with updated defaults
    reactionTemp: float = 37.0
    saltConc: float = 50.0
    mgConc: float = 10.0
    hairpinTm: float = 32.0  # Updated: max 32°C
    selfDimerTm: float = 32.0  # Updated: max 32°C
    crossDimerDgMin: float = -5.0  # New: min -5 kcal/mol
    hybridizationTmMin: float = 42.0  # New: min 42°C
    hybridizationTmMax: float = 60.0  # New: max 60°C
    gcContentMin: float = 30.0  # Updated: min 30%
    gcContentMax: float = 70.0  # Updated: max 70%
    threePrimeSelfDimerTm: float = 27.0  # Updated: max 27°C
    threePrimeHairpinTm: float = 27.0  # Updated: max 27°C
    threePrimeCrossDimerDgMin: float = -2.0  # New: min -2 kcal/mol
    threePrimeLength: int = 6

    # Additional settings (ignored but accepted for compatibility)
    redisHost: str = 'localhost'
    redisPort: int = 6379
    cacheTimeout: int = 3600
    maxSequencesPerDomain: int = 10
    orthogonalityThreshold: float = 0.8

    def __post_init__(self):
        """Accept any additional keyword arguments"""
        pass


@dataclass
class ValidationResult:
    passed: bool
    value: Any
    threshold: Any
    details: str = ""
    check_type: str = ""


# Utility functions
def reverse_complement(sequence: str) -> str:
    """Generate reverse complement of DNA sequence"""
    complement_map = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
    return ''.join(complement_map.get(base.upper(), base) for base in sequence[::-1])


def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content percentage"""
    if not sequence:
        return 0.0
    gc_count = sequence.count('G') + sequence.count('C')
    return (gc_count / len(sequence)) * 100


def validate_dna_sequence(sequence: str) -> bool:
    """Validate that sequence contains only valid DNA bases"""
    return all(base.upper() in 'ATGCN' for base in sequence)