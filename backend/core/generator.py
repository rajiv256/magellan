"""
Overhauled sequence generator - simplified for length-based Redis storage only
No orthogonal sets, just individual sequences by length
"""

import json
import random
import logging
from typing import List, Dict, Set, Optional

logger = logging.getLogger(__name__)


class SequenceGenerator:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.used_sequences = set()

    def has_complement_domains(self, domains: List) -> bool:
        """Check if any domains have complement relationships"""
        for domain in domains:
            if hasattr(domain, 'isComplement') and domain.isComplement:
                return True
            if hasattr(domain, 'complementOf') and domain.complementOf is not None:
                return True
        return False

    def get_sequences_from_redis(self, length: int, count: int = 1, exclude: Set[str] = None) -> List[str]:
        """Sample sequences from Redis for a given length"""
        try:
            redis_key = f"sequences:length:{length}"
            available_sequences = list(self.redis.smembers(redis_key))

            if not available_sequences:
                logger.warning(f"No sequences found in Redis for length {length}")
                return []

            # Filter out excluded sequences
            if exclude:
                available_sequences = [seq for seq in available_sequences if seq not in exclude]

            if not available_sequences:
                logger.warning(f"All sequences for length {length} are excluded")
                return []

            # Sample randomly
            sample_count = min(count, len(available_sequences))
            selected = random.sample(available_sequences, sample_count)

            logger.debug(
                f"Sampled {len(selected)} sequences from {len(available_sequences)} available for length {length}")
            return selected

        except Exception as e:
            logger.error(f"Error sampling sequences from Redis for length {length}: {e}")
            return []

    def get_all_sequences_for_length(self, length: int) -> List[str]:
        """Get all available sequences for a specific length from Redis"""
        try:
            redis_key = f"sequences:length:{length}"
            sequences = list(self.redis.smembers(redis_key))

            if not sequences:
                logger.warning(f"No sequences found in Redis for length {length}")
                return []

            logger.debug(f"Found {len(sequences)} sequences for length {length}")
            return sequences

        except Exception as e:
            logger.error(f"Error getting sequences for length {length}: {e}")
            return []

    def check_cross_dimer_interactions(self, new_sequence: str, existing_sequences: List[str]) -> tuple[bool, str]:
        """Check cross-dimer interactions using ΔG values"""
        try:
            from thermodynamics import ThermodynamicCalculator
            from models import ValidationSettings

            settings = ValidationSettings()
            calculator = ThermodynamicCalculator(settings)

            for existing_seq in existing_sequences:
                # Full sequence cross-dimer ΔG check (≥ -5.0 kcal/mol)
                cross_dimer_dg = calculator.calculate_cross_dimer_delta_g(new_sequence, existing_seq)
                if cross_dimer_dg < settings.crossDimerDgMin:
                    return False, f"Cross-dimer ΔG {cross_dimer_dg:.2f} kcal/mol too negative with {existing_seq[:10]}..."

                # 3' end cross-dimer ΔG check (≥ -2.0 kcal/mol)
                three_prime_cross_dg = calculator.calculate_three_prime_cross_dimer_delta_g(
                    new_sequence, existing_seq, settings.threePrimeLength
                )
                if three_prime_cross_dg < settings.threePrimeCrossDimerDgMin:
                    return False, f"3' cross-dimer ΔG {three_prime_cross_dg:.2f} kcal/mol too negative"

            return True, "No problematic cross-interactions"

        except Exception as e:
            logger.error(f"Error in cross-dimer validation: {e}")
            return False, f"Cross-dimer validation error: {e}"

    def design_domain_sequences(self, domains: List) -> bool:
        """Design sequences for domains using individual sequence selection from Redis"""
        try:
            # Check if we have complement domains
            has_complements = self.has_complement_domains(domains)

            if has_complements:
                logger.info("Complement domains detected - skipping cross-dimer checks")
                return self._design_with_complements(domains)
            else:
                logger.info("No complement domains - performing full cross-dimer validation")
                return self._design_with_cross_validation(domains)

        except Exception as e:
            logger.error(f"Error in domain sequence design: {e}")
            return False

    def _design_with_complements(self, domains: List) -> bool:
        """Design sequences when complement domains are present (no cross-dimer checks)"""
        try:
            # Get forward domains only
            forward_domains = [d for d in domains if not getattr(d, 'isComplement', False)]

            for domain in forward_domains:
                # Sample sequence from Redis
                sequences = self.get_sequences_from_redis(
                    domain.length,
                    count=1,
                    exclude=self.used_sequences
                )

                if sequences:
                    domain.sequence = sequences[0]
                    self.used_sequences.add(sequences[0])
                    logger.info(f"Assigned sequence to domain {domain.name}: {domain.sequence}")

                    # Update complement domain
                    complement = next((d for d in domains if getattr(d, 'complementOf', None) == domain.id), None)
                    if complement:
                        complement.sequence = self._reverse_complement(domain.sequence)
                        logger.debug(f"Generated complement for {domain.name}*: {complement.sequence}")
                else:
                    logger.error(f"Failed to get sequence for domain {domain.name} (length {domain.length})")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error in complement-based design: {e}")
            return False

    def _design_with_cross_validation(self, domains: List) -> bool:
        """Design sequences with full cross-dimer validation"""
        try:
            assigned_sequences = []

            for domain in domains:
                max_attempts = 50  # Increased attempts since we're not using orthogonal sets
                sequence_found = False

                for attempt in range(max_attempts):
                    # Sample a sequence from Redis
                    sequences = self.get_sequences_from_redis(
                        domain.length,
                        count=1,
                        exclude=self.used_sequences
                    )

                    if not sequences:
                        logger.error(f"No available sequences for domain {domain.name} (length {domain.length})")
                        break

                    candidate_sequence = sequences[0]

                    # Check cross-interactions with previously assigned sequences
                    if assigned_sequences:
                        is_valid, reason = self.check_cross_dimer_interactions(candidate_sequence, assigned_sequences)
                        if not is_valid:
                            logger.debug(f"Sequence rejected for {domain.name}: {reason}")
                            self.used_sequences.add(candidate_sequence)  # Mark as used to avoid retrying
                            continue

                    # Sequence is valid
                    domain.sequence = candidate_sequence
                    assigned_sequences.append(candidate_sequence)
                    self.used_sequences.add(candidate_sequence)
                    sequence_found = True

                    logger.info(f"Assigned sequence to domain {domain.name}: {domain.sequence}")
                    break

                if not sequence_found:
                    logger.error(
                        f"Failed to find valid sequence for domain {domain.name} after {max_attempts} attempts")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error in cross-validation design: {e}")
            return False

    def _reverse_complement(self, sequence: str) -> str:
        """Generate reverse complement"""
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
        return ''.join(complement.get(base.upper(), base) for base in sequence[::-1])

    def get_length_info(self, length: int) -> Optional[Dict]:
        """Get information about sequences for a specific length"""
        try:
            redis_key = f"sequences:length:{length}"
            metadata_key = f"sequences:length:{length}:metadata"

            count = self.redis.scard(redis_key)
            metadata_raw = self.redis.get(metadata_key)

            if count == 0:
                return None

            return {
                'type': 'length_set',
                'length': length,
                'total_sequences': count,
                'metadata': json.loads(metadata_raw) if metadata_raw else {},
                'sample_sequences': list(self.redis.srandmember(redis_key, 5)),  # 5 random samples
                'redis_key': redis_key
            }

        except Exception as e:
            logger.error(f"Error getting info for length {length}: {e}")
            return None

    def list_available_lengths(self) -> Dict[str, Dict]:
        """List all available lengths with their sequence counts"""
        try:
            available_lengths = {}

            # Check lengths 7-25
            for length in range(7, 26):
                length_info = self.get_length_info(length)
                if length_info:
                    available_lengths[str(length)] = length_info

            return available_lengths

        except Exception as e:
            logger.error(f"Error listing available lengths: {e}")
            return {}

    def get_database_stats(self) -> Dict[str, any]:
        """Get comprehensive database statistics"""
        try:
            stats = {
                'individual_lengths': {},
                'total_sequences': 0,
                'available_lengths': []
            }

            # Count sequences by length
            for length in range(7, 26):
                redis_key = f"sequences:length:{length}"
                count = self.redis.scard(redis_key)
                if count > 0:
                    stats['individual_lengths'][length] = count
                    stats['total_sequences'] += count
                    stats['available_lengths'].append(length)

            # Redis memory info
            try:
                redis_info = self.redis.info()
                stats['redis_memory'] = redis_info.get('used_memory_human', 'unknown')
                stats['redis_keys'] = redis_info.get('db0', {}).get('keys', 0)
            except:
                stats['redis_memory'] = 'unknown'
                stats['redis_keys'] = 0

            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    def check_sequences_available(self, required_lengths: List[int]) -> Dict[int, Dict]:
        """Check if sequences are available for all required lengths"""
        try:
            availability = {}

            for length in required_lengths:
                redis_key = f"sequences:length:{length}"
                count = self.redis.scard(redis_key)

                availability[length] = {
                    'available': count > 0,
                    'count': count,
                    'redis_key': redis_key
                }

            return availability

        except Exception as e:
            logger.error(f"Error checking sequence availability: {e}")
            return {}

    def reload_sequences(self) -> bool:
        """Check Redis connection and available sequences"""
        try:
            if not self.redis:
                return False

            # Test Redis connection
            self.redis.ping()

            # Count total sequences
            total_sequences = 0
            available_lengths = 0

            for length in range(7, 26):
                count = self.redis.scard(f"sequences:length:{length}")
                if count > 0:
                    total_sequences += count
                    available_lengths += 1

            logger.info(f"Redis connection OK - {total_sequences} sequences across {available_lengths} lengths")
            return total_sequences > 0

        except Exception as e:
            logger.error(f"Error checking Redis: {e}")
            return False

    def clear_used_sequences(self):
        """Clear the set of used sequences for a new design session"""
        self.used_sequences.clear()
        logger.info("Cleared used sequences")

    def get_sequence_statistics(self, length: int) -> Dict[str, any]:
        """Get detailed statistics for sequences of a specific length"""
        try:
            sequences = self.get_all_sequences_for_length(length)

            if not sequences:
                return {'length': length, 'count': 0, 'statistics': None}

            # Calculate basic statistics
            total_sequences = len(sequences)
            avg_gc_content = sum(self._calculate_gc_content(seq) for seq in sequences) / total_sequences

            # GC content distribution
            gc_contents = [self._calculate_gc_content(seq) for seq in sequences]
            gc_min = min(gc_contents)
            gc_max = max(gc_contents)

            return {
                'length': length,
                'count': total_sequences,
                'statistics': {
                    'avg_gc_content': round(avg_gc_content, 2),
                    'gc_content_range': [round(gc_min, 2), round(gc_max, 2)],
                    'sample_sequences': sequences[:3]  # First 3 as examples
                }
            }

        except Exception as e:
            logger.error(f"Error getting statistics for length {length}: {e}")
            return {'length': length, 'count': 0, 'statistics': None, 'error': str(e)}

    def _calculate_gc_content(self, sequence: str) -> float:
        """Calculate GC content percentage"""
        if not sequence:
            return 0.0
        gc_count = sequence.upper().count('G') + sequence.upper().count('C')
        return (gc_count / len(sequence)) * 100