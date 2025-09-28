"""
Data models for OligoDesigner with updated validation settings
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
    # Core thermodynamic settings
    reactionTemp: float = 37.0
    saltConc: float = 50.0
    mgConc: float = 2.0

    # Secondary structure limits
    hairpinTm: float = 32.0  # Max hairpin Tm (°C)
    selfDimerTm: float = 32.0  # Max self-dimer Tm (°C)

    # Cross-dimer thermodynamics
    crossDimerDgMin: float = -5.0  # Min cross-dimer ΔG (kcal/mol)

    # Hybridization temperature range
    hybridizationTmMin: float = 42.0  # Min hybridization Tm (°C)
    hybridizationTmMax: float = 60.0  # Max hybridization Tm (°C)

    # GC content range
    gcContentMin: float = 30.0  # Min GC content (%)
    gcContentMax: float = 70.0  # Max GC content (%)

    # 3' end stringent checks
    threePrimeSelfDimerTm: float = 27.0  # Max 3' self-dimer Tm (°C)
    threePrimeHairpinTm: float = 27.0  # Max 3' hairpin Tm (°C)
    threePrimeCrossDimerDgMin: float = -2.0  # Min 3' cross-dimer ΔG (kcal/mol)
    threePrimeLength: int = 6  # Length of 3' region to check

    # System settings (maintained for compatibility)
    redisHost: str = 'localhost'
    redisPort: int = 6379
    cacheTimeout: int = 3600
    maxSequencesPerDomain: int = 10
    orthogonalityThreshold: float = 0.8

    def __post_init__(self):
        """Validate settings after initialization"""
        if self.hybridizationTmMin >= self.hybridizationTmMax:
            raise ValueError("hybridizationTmMin must be less than hybridizationTmMax")
        if self.gcContentMin >= self.gcContentMax:
            raise ValueError("gcContentMin must be less than gcContentMax")
        if self.crossDimerDgMin > 0:
            raise ValueError("crossDimerDgMin should be negative (ΔG in kcal/mol)")
        if self.threePrimeCrossDimerDgMin > 0:
            raise ValueError("threePrimeCrossDimerDgMin should be negative (ΔG in kcal/mol)")


@dataclass
class ValidationResult:
    passed: bool
    value: Any
    threshold: Any
    details: str = ""
    check_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'passed': self.passed,
            'value': str(self.value),
            'threshold': str(self.threshold),
            'details': self.details,
            'check_type': self.check_type
        }


# Utility functions
def reverse_complement(sequence: str) -> str:
    """Generate reverse complement of DNA sequence"""
    complement_map = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
    return ''.join(complement_map.get(base.upper(), base) for base in sequence[::-1])


def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content percentage"""
    if not sequence:
        return 0.0
    gc_count = sequence.upper().count('G') + sequence.upper().count('C')
    return (gc_count / len(sequence)) * 100


def validate_dna_sequence(sequence: str) -> bool:
    """Validate that sequence contains only valid DNA bases"""
    if not sequence:
        return False
    return all(base.upper() in 'ATGCN' for base in sequence)


def format_sequence(sequence: str, line_length: int = 50) -> str:
    """Format sequence with line breaks for display"""
    if not sequence:
        return ""
    return '\n'.join(sequence[i:i + line_length] for i in range(0, len(sequence), line_length))


def calculate_sequence_stats(sequence: str) -> Dict[str, Any]:
    """Calculate basic sequence statistics"""
    if not sequence:
        return {}

    length = len(sequence)
    gc_content = calculate_gc_content(sequence)

    # Count bases
    base_counts = {
        'A': sequence.upper().count('A'),
        'T': sequence.upper().count('T'),
        'G': sequence.upper().count('G'),
        'C': sequence.upper().count('C'),
        'N': sequence.upper().count('N')
    }

    return {
        'length': length,
        'gc_content': gc_content,
        'base_counts': base_counts,
        'is_valid_dna': validate_dna_sequence(sequence)
    }