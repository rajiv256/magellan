"""
Updated sequence validator matching frontend settings structure
"""

import logging
from typing import Dict, List, Tuple
from .models import ValidationSettings, ValidationResult, Domain, Strand
from .thermodynamics import ThermodynamicCalculator

logger = logging.getLogger(__name__)


class SequenceValidator:
    """Comprehensive sequence validation with thermodynamic checks"""

    def __init__(self, settings: ValidationSettings):
        self.settings = settings
        self.calculator = ThermodynamicCalculator(settings)

    def validate_domain(self, domain: Domain) -> Dict[str, ValidationResult]:
        """Validate a single domain against all criteria"""
        if not domain.sequence or domain.sequence == "":
            return self._create_empty_validation_results()

        results = {}

        # 1. Length validation
        results['length'] = self._validate_length(domain.sequence, domain.length)

        # 2. GC content validation
        results['gcContent'] = self._validate_gc_content(domain.sequence)

        # 3. Melting temperature validation (range check)
        results['meltingTemp'] = self._validate_melting_temperature(domain.sequence)

        # 4. Hairpin formation validation
        results['hairpin'] = self._validate_hairpin_formation(domain.sequence)

        # 5. Self-dimer validation
        results['selfDimer'] = self._validate_self_dimer(domain.sequence)

        # 6. Problematic patterns validation
        results['patterns'] = self._validate_sequence_patterns(domain.sequence)

        # 7. 3' end specific validations (more stringent)
        three_prime_results = self._validate_three_prime_region(domain.sequence)
        results.update(three_prime_results)

        logger.info(
            f"Validated domain {domain.name}: {self._count_passed_checks(results)}/{len(results)} checks passed")
        return results

    def validate_strand(self, strand: Strand, domains: List[Domain] = None) -> Dict[str, ValidationResult]:
        """Validate a complete strand"""
        if not strand.sequence or strand.sequence == "":
            return self._create_empty_validation_results()

        results = {}

        # Basic strand validations
        results['length'] = self._validate_strand_length(strand, domains)
        results['gcContent'] = self._validate_gc_content(strand.sequence)
        results['meltingTemp'] = self._validate_melting_temperature(strand.sequence)
        results['hairpin'] = self._validate_hairpin_formation(strand.sequence)
        results['selfDimer'] = self._validate_self_dimer(strand.sequence)
        results['patterns'] = self._validate_sequence_patterns(strand.sequence)

        # 3' end validations (critical for primers)
        three_prime_results = self._validate_three_prime_region(strand.sequence)
        results.update(three_prime_results)

        # Domain composition validation (if domains provided)
        if domains:
            composition_results = self._validate_domain_composition(strand, domains)
            results.update(composition_results)

        logger.info(
            f"Validated strand {strand.name}: {self._count_passed_checks(results)}/{len(results)} checks passed")
        return results

    def validate_cross_interactions(self, strands: List[Strand]) -> Dict[Tuple[int, int], Dict[str, ValidationResult]]:
        """Validate cross-interactions between different strands"""
        cross_results = {}

        for i, strand1 in enumerate(strands):
            for j, strand2 in enumerate(strands[i + 1:], i + 1):
                if strand1.sequence and strand2.sequence:
                    pair_key = (strand1.id, strand2.id)
                    cross_results[pair_key] = self._validate_strand_pair(strand1, strand2)

        logger.info(f"Validated {len(cross_results)} strand pairs for cross-interactions")
        return cross_results

    def _validate_length(self, sequence: str, expected_length: int) -> ValidationResult:
        """Validate sequence length matches expected"""
        actual_length = len(sequence)
        passed = actual_length == expected_length

        return ValidationResult(
            passed=passed,
            value=f"{actual_length}nt",
            threshold=f"{expected_length}nt",
            details=f"Sequence length: {actual_length}, expected: {expected_length}",
            check_type="length"
        )

    def _validate_gc_content(self, sequence: str) -> ValidationResult:
        """Validate GC content within acceptable range"""
        gc_content = self.calculator.calculate_gc_content(sequence)
        passed = self.settings.gcContentMin <= gc_content <= self.settings.gcContentMax

        return ValidationResult(
            passed=passed,
            value=f"{gc_content:.1f}%",
            threshold=f"{self.settings.gcContentMin}-{self.settings.gcContentMax}%",
            details=f"GC content: {gc_content:.1f}%",
            check_type="gc_content"
        )

    def _validate_melting_temperature(self, sequence: str) -> ValidationResult:
        """Validate melting temperature is within hybridization range"""
        tm = self.calculator.calculate_melting_temperature(sequence)
        passed = self.settings.hybridizationTmMin <= tm <= self.settings.hybridizationTmMax

        return ValidationResult(
            passed=passed,
            value=f"{tm:.1f}°C",
            threshold=f"{self.settings.hybridizationTmMin}-{self.settings.hybridizationTmMax}°C",
            details=f"Melting temperature: {tm:.1f}°C (range: {self.settings.hybridizationTmMin}-{self.settings.hybridizationTmMax}°C)",
            check_type="melting_temp"
        )

    def _validate_hairpin_formation(self, sequence: str) -> ValidationResult:
        """Validate hairpin formation temperature is acceptable"""
        hairpin_tm = self.calculator.calculate_hairpin_tm(sequence)
        passed = hairpin_tm <= self.settings.hairpinTm

        return ValidationResult(
            passed=passed,
            value=f"{hairpin_tm:.1f}°C",
            threshold=f"<={self.settings.hairpinTm}°C",
            details=f"Hairpin Tm: {hairpin_tm:.1f}°C",
            check_type="hairpin"
        )

    def _validate_self_dimer(self, sequence: str) -> ValidationResult:
        """Validate self-dimer formation temperature"""
        self_dimer_tm = self.calculator.calculate_self_dimer_tm(sequence)
        passed = self_dimer_tm <= self.settings.selfDimerTm

        return ValidationResult(
            passed=passed,
            value=f"{self_dimer_tm:.1f}°C",
            threshold=f"<={self.settings.selfDimerTm}°C",
            details=f"Self-dimer Tm: {self_dimer_tm:.1f}°C",
            check_type="self_dimer"
        )

    def _validate_sequence_patterns(self, sequence: str) -> ValidationResult:
        """Validate sequence doesn't contain problematic patterns"""
        problematic_patterns = self._find_problematic_patterns(sequence)
        passed = len(problematic_patterns) == 0

        details = "No problematic patterns found" if passed else f"Found: {', '.join(problematic_patterns)}"

        return ValidationResult(
            passed=passed,
            value="Clean" if passed else f"{len(problematic_patterns)} issues",
            threshold="No problematic patterns",
            details=details,
            check_type="patterns"
        )

    def _validate_three_prime_region(self, sequence: str) -> Dict[str, ValidationResult]:
        """Validate 3' end region with more stringent criteria"""
        results = {}

        # 3' hairpin check
        three_prime_hairpin_tm = self.calculator.calculate_three_prime_hairpin_tm(
            sequence, self.settings.threePrimeLength
        )
        results['threePrimeHairpin'] = ValidationResult(
            passed=three_prime_hairpin_tm <= self.settings.threePrimeHairpinTm,
            value=f"{three_prime_hairpin_tm:.1f}°C",
            threshold=f"<={self.settings.threePrimeHairpinTm}°C",
            details=f"3' hairpin Tm: {three_prime_hairpin_tm:.1f}°C",
            check_type="three_prime_hairpin"
        )

        # 3' self-dimer check
        three_prime_self_dimer_tm = self.calculator.calculate_three_prime_self_dimer_tm(
            sequence, self.settings.threePrimeLength
        )
        results['threePrimeSelfDimer'] = ValidationResult(
            passed=three_prime_self_dimer_tm <= self.settings.threePrimeSelfDimerTm,
            value=f"{three_prime_self_dimer_tm:.1f}°C",
            threshold=f"<={self.settings.threePrimeSelfDimerTm}°C",
            details=f"3' self-dimer Tm: {three_prime_self_dimer_tm:.1f}°C",
            check_type="three_prime_self_dimer"
        )

        # 3' GC clamp check (last 5 bases shouldn't be all G/C)
        three_prime_end = sequence[-5:] if len(sequence) >= 5 else sequence
        gc_clamp_count = three_prime_end.count('G') + three_prime_end.count('C')
        gc_clamp_passed = gc_clamp_count <= 3  # Maximum 3 G/C in last 5 bases

        results['threePrimeGCClamp'] = ValidationResult(
            passed=gc_clamp_passed,
            value=f"{gc_clamp_count}/5 G/C",
            threshold="≤3 G/C in last 5 bases",
            details=f"3' end ({three_prime_end}): {gc_clamp_count} G/C bases",
            check_type="three_prime_gc_clamp"
        )

        return results

    def _validate_strand_length(self, strand: Strand, domains: List[Domain]) -> ValidationResult:
        """Validate strand length matches sum of constituent domains"""
        if not domains:
            return ValidationResult(
                passed=True,
                value=f"{len(strand.sequence)}nt",
                threshold="N/A",
                details="No domains provided for validation",
                check_type="strand_length"
            )

        expected_length = sum(d.length for d in domains if d.id in strand.domainIds)
        actual_length = len(strand.sequence)
        passed = actual_length == expected_length

        return ValidationResult(
            passed=passed,
            value=f"{actual_length}nt",
            threshold=f"{expected_length}nt",
            details=f"Strand length: {actual_length}, expected from domains: {expected_length}",
            check_type="strand_length"
        )

    def _validate_domain_composition(self, strand: Strand, domains: List[Domain]) -> Dict[str, ValidationResult]:
        """Validate strand sequence matches concatenated domain sequences"""
        results = {}

        # Get domain sequences in order
        domain_dict = {d.id: d for d in domains}
        expected_sequences = []

        for domain_id in strand.domainIds:
            if domain_id in domain_dict:
                domain = domain_dict[domain_id]
                if domain.sequence:
                    expected_sequences.append(domain.sequence)

        expected_full_sequence = "".join(expected_sequences)

        # Compare with actual strand sequence
        passed = strand.sequence == expected_full_sequence

        results['composition'] = ValidationResult(
            passed=passed,
            value="Matches" if passed else "Mismatch",
            threshold="Perfect match",
            details=f"Expected: {expected_full_sequence[:20]}..." if not passed else "Sequence matches domain composition",
            check_type="composition"
        )

        return results

    def _validate_strand_pair(self, strand1: Strand, strand2: Strand) -> Dict[str, ValidationResult]:
        """Validate interactions between two strands using updated settings"""
        results = {}

        # Cross-dimer ΔG check (using crossDimerDgMin)
        cross_dimer_dg = self.calculator.calculate_cross_dimer_delta_g(strand1.sequence, strand2.sequence)
        results['crossDimerDg'] = ValidationResult(
            passed=cross_dimer_dg >= self.settings.crossDimerDgMin,
            value=f"{cross_dimer_dg:.2f} kcal/mol",
            threshold=f">={self.settings.crossDimerDgMin} kcal/mol",
            details=f"Cross-dimer ΔG between {strand1.name} and {strand2.name}: {cross_dimer_dg:.2f} kcal/mol",
            check_type="cross_dimer_dg"
        )

        # 3' cross-dimer ΔG check (using threePrimeCrossDimerDgMin)
        three_prime_cross_dg = self.calculator.calculate_three_prime_cross_dimer_delta_g(
            strand1.sequence, strand2.sequence, self.settings.threePrimeLength
        )
        results['threePrimeCrossDimerDg'] = ValidationResult(
            passed=three_prime_cross_dg >= self.settings.threePrimeCrossDimerDgMin,
            value=f"{three_prime_cross_dg:.2f} kcal/mol",
            threshold=f">={self.settings.threePrimeCrossDimerDgMin} kcal/mol",
            details=f"3' cross-dimer ΔG: {three_prime_cross_dg:.2f} kcal/mol",
            check_type="three_prime_cross_dimer_dg"
        )

        return results

    def _find_problematic_patterns(self, sequence: str) -> List[str]:
        """Find problematic patterns in sequence"""
        patterns_found = []

        # Homopolymers (4+ consecutive same bases)
        for base in ['A', 'T', 'G', 'C']:
            if base * 4 in sequence:
                patterns_found.append(f"{base}4+")

        # Simple repeats
        simple_repeats = ['ATAT', 'TATA', 'CGCG', 'GCGC', 'AAGG', 'CCTT', 'GGCC', 'TTAA']
        for repeat in simple_repeats:
            if repeat in sequence:
                patterns_found.append(repeat)

        # Common restriction sites (might be problematic)
        restriction_sites = ['GAATTC', 'GGATCC', 'AAGCTT', 'CTGCAG', 'GTCGAC']
        for site in restriction_sites:
            if site in sequence:
                patterns_found.append(f"RestSite:{site}")

        # Runs of purines or pyrimidines
        if 'AAAAA' in sequence or 'GGGGG' in sequence:
            patterns_found.append("Purine-run")
        if 'TTTTT' in sequence or 'CCCCC' in sequence:
            patterns_found.append("Pyrimidine-run")

        return patterns_found

    def _create_empty_validation_results(self) -> Dict[str, ValidationResult]:
        """Create validation results for empty/invalid sequences"""
        return {
            'sequence': ValidationResult(
                passed=False,
                value="Empty",
                threshold="Valid DNA sequence",
                details="No sequence provided",
                check_type="sequence"
            )
        }

    def _count_passed_checks(self, results: Dict[str, ValidationResult]) -> int:
        """Count number of passed validation checks"""
        return sum(1 for result in results.values() if result.passed)

    def get_validation_summary(self, results: Dict[str, ValidationResult]) -> Dict[str, any]:
        """Get summary of validation results"""
        total_checks = len(results)
        passed_checks = self._count_passed_checks(results)
        failed_checks = total_checks - passed_checks

        critical_failures = []
        warnings = []

        for check_name, result in results.items():
            if not result.passed:
                if check_name in ['threePrimeHairpin', 'threePrimeSelfDimer', 'threePrimeCrossDimerDg']:
                    critical_failures.append(check_name)
                else:
                    warnings.append(check_name)

        return {
            'total_checks': total_checks,
            'passed': passed_checks,
            'failed': failed_checks,
            'pass_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0,
            'critical_failures': critical_failures,
            'warnings': warnings,
            'overall_status': 'PASS' if failed_checks == 0 else 'CRITICAL' if critical_failures else 'WARNING'
        }