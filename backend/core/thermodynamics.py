"""
Direct thermodynamic calculations using primer3-py
"""

import logging
import primer3

logger = logging.getLogger(__name__)


class ThermodynamicCalculator:
    """Direct thermodynamic calculator using primer3-py"""

    def __init__(self, settings):
        self.settings = settings

        # Standard primer3 parameters
        self.primer3_params = {
            'mv_conc': 50.0,  # mM monovalent cations
            'dv_conc': 10.0,  # mM divalent cations
            'dntp_conc': 0.6,  # mM dNTP
            'dna_conc': 250.0  # nM primer concentration
        }

        logger.info(
            f"Initialized calculator: mv={self.primer3_params['mv_conc']}mM, dv={self.primer3_params['dv_conc']}mM")

    def calculate_melting_temperature(self, sequence: str) -> float:
        """Calculate melting temperature using primer3"""
        if not sequence or len(sequence) < 2:
            return 25.0

        tm = primer3.calc_tm(seq=sequence.upper(), **self.primer3_params)
        logger.debug(f"Tm for {sequence}: {tm:.1f}°C")
        return tm

    def calculate_hairpin_tm(self, sequence: str) -> float:
        """Calculate hairpin formation temperature"""
        if not sequence or len(sequence) < 6:
            return 15.0

        result = primer3.calc_hairpin(seq=sequence.upper(), **self.primer3_params)
        tm = result.tm if hasattr(result, 'tm') else 15.0
        logger.debug(f"Hairpin Tm for {sequence}: {tm:.1f}°C")
        return tm

    def calculate_self_dimer_tm(self, sequence: str) -> float:
        """Calculate self-dimer formation temperature"""
        if not sequence or len(sequence) < 4:
            return 15.0

        result = primer3.calc_homodimer(seq=sequence.upper(), **self.primer3_params)
        tm = result.tm if hasattr(result, 'tm') else 15.0
        logger.debug(f"Self-dimer Tm for {sequence}: {tm:.1f}°C")
        return tm

    def calculate_cross_dimer_tm(self, seq1: str, seq2: str) -> float:
        """Calculate cross-dimer formation temperature"""
        if not seq1 or not seq2 or len(seq1) < 3 or len(seq2) < 3:
            return 15.0

        result = primer3.calc_heterodimer(
            seq1=seq1.upper(),
            seq2=seq2.upper(),
            **self.primer3_params
        )
        tm = result.tm if hasattr(result, 'tm') else 15.0
        logger.debug(f"Cross-dimer Tm: {tm:.1f}°C")
        return tm

    def calculate_cross_dimer_delta_g(self, seq1: str, seq2: str) -> float:
        """Calculate cross-dimer formation ΔG (kcal/mol)"""
        if not seq1 or not seq2 or len(seq1) < 3 or len(seq2) < 3:
            return 0.0

        result = primer3.calc_heterodimer(
            seq1=seq1.upper(),
            seq2=seq2.upper(),
            **self.primer3_params
        )

        # primer3 heterodimer returns dg, dh, ds
        delta_g = result.dg  # ΔG in kcal/mol
        delta_h = result.dh  # ΔH in kcal/mol
        delta_s = result.ds  # ΔS in cal/(mol·K)

        logger.debug(f"Cross-dimer: ΔG={delta_g:.2f}, ΔH={delta_h:.2f}, ΔS={delta_s:.2f}")
        return delta_g

    def calculate_three_prime_cross_dimer_delta_g(self, seq1: str, seq2: str, length: int) -> float:
        """Calculate 3' end cross-dimer ΔG"""
        three_prime_seq1 = seq1[-length:] if len(seq1) >= length else seq1
        three_prime_seq2 = seq2[-length:] if len(seq2) >= length else seq2
        return self.calculate_cross_dimer_delta_g(three_prime_seq1, three_prime_seq2)

    def calculate_three_prime_hairpin_tm(self, sequence: str, length: int) -> float:
        """Calculate 3' end hairpin (more stringent)"""
        three_prime_seq = sequence[-length:] if len(sequence) >= length else sequence
        return self.calculate_hairpin_tm(three_prime_seq) * 1.2

    def calculate_three_prime_self_dimer_tm(self, sequence: str, length: int) -> float:
        """Calculate 3' end self-dimer (more stringent)"""
        three_prime_seq = sequence[-length:] if len(sequence) >= length else sequence
        return self.calculate_self_dimer_tm(three_prime_seq) * 1.3

    def calculate_three_prime_cross_dimer_tm(self, seq1: str, seq2: str, length: int) -> float:
        """Calculate 3' end cross-dimer (more stringent)"""
        three_prime_seq1 = seq1[-length:] if len(seq1) >= length else seq1
        three_prime_seq2 = seq2[-length:] if len(seq2) >= length else seq2
        return self.calculate_cross_dimer_tm(three_prime_seq1, three_prime_seq2) * 1.25

    def calculate_gc_content(self, sequence: str) -> float:
        """Calculate GC content percentage"""
        if not sequence:
            return 0.0
        gc_count = sequence.upper().count('G') + sequence.upper().count('C')
        return (gc_count / len(sequence)) * 100

    def _reverse_complement(self, sequence: str) -> str:
        """Generate reverse complement"""
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
        return ''.join(complement.get(base.upper(), base) for base in sequence[::-1])