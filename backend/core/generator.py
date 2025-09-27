"""
Enhanced sequence generator for orthogonal oligo sets
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

    def get_compatible_sets(self, required_lengths: List[int]) -> Dict[str, Dict]:
        """Find orthogonal sets that contain all required lengths"""
        try:
            # Get all orthogonal set keys
            set_keys = self.redis.keys("orthogonal_set:*")
            compatible_sets = {}

            logger.info(f"Checking {len(set_keys)} orthogonal sets for lengths: {required_lengths}")

            for set_key in set_keys:
                try:
                    # Get set metadata
                    set_data = self.redis.get(set_key)
                    if not set_data:
                        continue

                    oligo_set = json.loads(set_data)

                    # Check if this set contains all required lengths
                    available_lengths = set(oligo_set.get('lengths', []))
                    required_lengths_set = set(required_lengths)

                    if required_lengths_set.issubset(available_lengths):
                        set_id = set_key.split(':')[1]  # Extract set ID
                        compatible_sets[set_id] = oligo_set
                        logger.debug(f"Set {set_id} is compatible: has lengths {sorted(available_lengths)}")
                    else:
                        missing = required_lengths_set - available_lengths
                        logger.debug(f"Set {set_key} missing lengths: {missing}")

                except Exception as e:
                    logger.error(f"Error processing set {set_key}: {e}")

            logger.info(f"Found {len(compatible_sets)} compatible orthogonal sets")
            return compatible_sets

        except Exception as e:
            logger.error(f"Error finding compatible sets: {e}")
            return {}

    def select_optimal_set(self, compatible_sets: Dict[str, Dict], required_lengths: List[int]) -> Optional[Dict]:
        """Select the best orthogonal set (currently random, scoring later)"""
        if not compatible_sets:
            logger.warning("No compatible orthogonal sets found")
            return None

        # For now: random selection
        # TODO: Implement scoring based on:
        # - Set quality/orthogonality score
        # - GC content distribution
        # - Thermodynamic properties
        # - Set completeness (extra lengths available)

        set_id = random.choice(list(compatible_sets.keys()))
        selected_set = compatible_sets[set_id]

        logger.info(f"Selected orthogonal set: {set_id} (random selection)")
        logger.debug(f"Set contains lengths: {sorted(selected_set.get('lengths', []))}")

        return selected_set

    def get_sequences_from_set(self, oligo_set: Dict, length: int, count: int = 1) -> List[str]:
        """Get sequences of specific length from an orthogonal set"""
        try:
            sequences_by_length = oligo_set.get('sequences', {})
            available_sequences = sequences_by_length.get(str(length), [])

            if not available_sequences:
                logger.warning(f"No sequences of length {length} in selected set")
                return []

            # Filter out already used sequences
            unused_sequences = [seq for seq in available_sequences if seq not in self.used_sequences]

            if not unused_sequences:
                logger.warning(f"All sequences of length {length} already used, reusing...")
                unused_sequences = available_sequences

            # Select requested number of sequences
            selected = random.sample(unused_sequences, min(count, len(unused_sequences)))

            # Mark as used
            self.used_sequences.update(selected)

            logger.debug(f"Selected {len(selected)} sequences of length {length}")
            return selected

        except Exception as e:
            logger.error(f"Error getting sequences from set: {e}")
            return []

    def design_domain_sequences(self, domains: List) -> bool:
        """Design sequences for domains using orthogonal sets"""
        try:
            # Get all required lengths
            required_lengths = []
            forward_domains = [d for d in domains if not d.isComplement]

            for domain in forward_domains:
                if domain.length not in required_lengths:
                    required_lengths.append(domain.length)

            logger.info(f"Required lengths for design: {required_lengths}")

            # Find compatible orthogonal sets
            compatible_sets = self.get_compatible_sets(required_lengths)

            if not compatible_sets:
                logger.error("No compatible orthogonal sets found")
                return False

            # Select optimal set
            selected_set = self.select_optimal_set(compatible_sets, required_lengths)

            if not selected_set:
                logger.error("Failed to select orthogonal set")
                return False

            # Assign sequences from the selected set
            for domain in forward_domains:
                sequences = self.get_sequences_from_set(selected_set, domain.length, 1)

                if sequences:
                    domain.sequence = sequences[0]
                    logger.info(f"Assigned sequence to domain {domain.name}: {domain.sequence}")

                    # Update complement domain
                    complement = next((d for d in domains if d.complementOf == domain.id), None)
                    if complement:
                        complement.sequence = self._reverse_complement(domain.sequence)
                        logger.debug(f"Generated complement for {domain.name}*: {complement.sequence}")
                else:
                    logger.error(f"Failed to get sequence for domain {domain.name} (length {domain.length})")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error in domain sequence design: {e}")
            return False

    def get_set_info(self, set_id: str) -> Optional[Dict]:
        """Get information about a specific orthogonal set"""
        try:
            set_key = f"orthogonal_set:{set_id}"
            set_data = self.redis.get(set_key)

            if set_data:
                return json.loads(set_data)
            return None

        except Exception as e:
            logger.error(f"Error getting set info: {e}")
            return None

    def list_available_sets(self) -> Dict[str, Dict]:
        """List all available orthogonal sets with their metadata"""
        try:
            set_keys = self.redis.keys("orthogonal_set:*")
            available_sets = {}

            for set_key in set_keys:
                set_id = set_key.split(':')[1]
                set_info = self.get_set_info(set_id)

                if set_info:
                    # Extract summary info
                    available_sets[set_id] = {
                        'lengths': sorted(set_info.get('lengths', [])),
                        'total_sequences': sum(len(seqs) for seqs in set_info.get('sequences', {}).values()),
                        'quality_score': set_info.get('quality_score', 0.0),
                        'created_at': set_info.get('created_at', 'unknown')
                    }

            return available_sets

        except Exception as e:
            logger.error(f"Error listing available sets: {e}")
            return {}

    def _reverse_complement(self, sequence: str) -> str:
        """Generate reverse complement"""
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
        return ''.join(complement.get(base.upper(), base) for base in sequence[::-1])

    # Legacy methods for backward compatibility
    def get_sequences_for_domain(self, length: int) -> List[str]:
        """Legacy method - get sequences for a specific length"""
        # Try to find any set with this length
        compatible_sets = self.get_compatible_sets([length])

        if compatible_sets:
            set_id = random.choice(list(compatible_sets.keys()))
            selected_set = compatible_sets[set_id]
            return self.get_sequences_from_set(selected_set, length, count=10)

        logger.warning(f"No orthogonal sets found for length {length}")
        return []

    def select_unused_sequence(self, sequences: List[str]) -> str:
        """Legacy method - select unused sequence"""
        if not sequences:
            return self._generate_fallback_sequence(20)

        unused = [seq for seq in sequences if seq not in self.used_sequences]

        if unused:
            selected = random.choice(unused)
        else:
            selected = random.choice(sequences)
            logger.warning("Reusing sequence")

        self.used_sequences.add(selected)
        return selected

    def _generate_fallback_sequence(self, length: int) -> str:
        """Generate simple fallback sequence"""
        bases = ['A', 'T', 'G', 'C']
        return ''.join(random.choice(bases) for _ in range(length))