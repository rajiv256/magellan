#!/usr/bin/env python3
"""
Simplified Parallel Sequence Generator
Generates sequences for lengths 7-25 using multiprocessing
"""

import random
import redis
import logging
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count
from typing import List, Set
import primer3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Global settings
SETTINGS = {
    'gc_min': 30.0,
    'gc_max': 70.0,
    'tm_min': 42.0,
    'tm_max': 60.0,
    'hairpin_max': 32.0,
    'self_dimer_max': 32.0,
    'three_prime_hairpin_max': 27.0,
    'three_prime_self_dimer_max': 27.0,
    'three_prime_length': 6,
    'mv_conc': 50.0,
    'dv_conc': 10.0,
    'dntp_conc': 0.6,
    'dna_conc': 250.0
}


def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content percentage"""
    gc_count = sequence.count('G') + sequence.count('C')
    return (gc_count / len(sequence)) * 100


def has_repetitive_patterns(sequence: str) -> bool:
    """Check for repetitive patterns and design issues"""
    seq = sequence.upper()

    # 1. Homopolymer runs (4+ identical bases)
    for base in ['A', 'T', 'G', 'C']:
        if base * 4 in seq:
            return True

    # 2. Simple dinucleotide repeats (ATATAT...)
    dinucleotides = ['AT', 'TA', 'GC', 'CG', 'AG', 'GA', 'CT', 'TC']
    for dinuc in dinucleotides:
        if dinuc * 3 in seq:  # 6+ bp repeat
            return True

    # 3. Trinucleotide repeats
    if len(seq) >= 9:
        for i in range(len(seq) - 8):
            trinuc = seq[i:i + 3]
            if trinuc * 3 == seq[i:i + 9]:
                return True

    # 4. Palindromes (avoid strong hairpin potential)
    if len(seq) >= 8:
        for i in range(len(seq) - 7):
            segment = seq[i:i + 8]
            if segment == segment[::-1]:
                return True

    # 5. Low complexity (too many of same base)
    for base in ['A', 'T', 'G', 'C']:
        if seq.count(base) > len(seq) * 0.6:  # >60% of any single base
            return True

    # 6. Avoid runs of purines or pyrimidines
    purine_run = 0
    pyrimidine_run = 0
    for base in seq:
        if base in 'AG':
            purine_run += 1
            pyrimidine_run = 0
        elif base in 'CT':
            pyrimidine_run += 1
            purine_run = 0
        else:
            purine_run = 0
            pyrimidine_run = 0

        if purine_run >= 5 or pyrimidine_run >= 5:
            return True

    return False


def check_symmetry_constraints(sequence: str) -> bool:
    """Check for problematic symmetry patterns"""
    seq = sequence.upper()
    length = len(seq)

    # 1. Avoid perfect reverse complement of itself (palindromic)
    complement_map = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    reverse_comp = ''.join(complement_map.get(base, base) for base in seq[::-1])
    if seq == reverse_comp:
        return False

    # 2. Avoid sequences that are reverse of themselves
    if seq == seq[::-1]:
        return False

    # 3. Check for internal symmetry (avoid strong secondary structures)
    if length >= 12:
        # Check if first half is reverse complement of second half
        mid = length // 2
        first_half = seq[:mid]
        second_half = seq[mid:mid * 2]
        second_half_rc = ''.join(complement_map.get(base, base) for base in second_half[::-1])

        if first_half == second_half_rc:
            return False

    # 4. Avoid sequences with strong internal complementarity
    if length >= 8:
        for i in range(length - 3):
            for j in range(i + 4, length):
                if j - i >= 4:  # At least 4 bp apart
                    subseq1 = seq[i:i + 4]
                    subseq2 = seq[j:j + 4] if j + 4 <= length else seq[j:]
                    if len(subseq2) >= 4:
                        subseq2_rc = ''.join(complement_map.get(base, base) for base in subseq2[::-1])
                        if subseq1 == subseq2_rc:
                            return False

    return True


def has_problematic_motifs(sequence: str) -> bool:
    """Check for known problematic sequence motifs"""
    seq = sequence.upper()

    # 1. Common restriction enzyme sites (might interfere with cloning)
    restriction_sites = [
        'GAATTC',  # EcoRI
        'GGATCC',  # BamHI
        'AAGCTT',  # HindIII
        'CTGCAG',  # PstI
        'GTCGAC',  # SalI
        'CCATGG',  # NcoI
        'GCGGCCGC',  # NotI
        'TCTAGA',  # XbaI
    ]

    for site in restriction_sites:
        if site in seq:
            return True

    # 2. Polymerase problematic sequences
    problematic_motifs = [
        'GGGGGG',  # G-quadruplex forming
        'CCCCCC',  # Strong secondary structure
        'AAAAAA',  # Weak region
        'TTTTTT',  # Termination signal-like
    ]

    for motif in problematic_motifs:
        if motif in seq:
            return True

    # 3. Avoid sequences similar to common primers
    common_primers = [
        'GTAAAACGACGGCCAGT',  # M13 forward
        'CAGGAAACAGCTATGAC',  # M13 reverse
        'TGTAAAACGACGGCCAGT',  # M13(-20) forward
    ]

    for primer in common_primers:
        # Check for significant overlap (>80% similarity in 8+ bp window)
        if len(seq) >= 8:
            for i in range(len(seq) - 7):
                window = seq[i:i + 8]
                for p in common_primers:
                    if len(p) >= 8:
                        for j in range(len(p) - 7):
                            p_window = p[j:j + 8]
                            matches = sum(1 for a, b in zip(window, p_window) if a == b)
                            if matches >= 7:  # >85% similarity
                                return True

    return False


def validate_sequence(sequence: str) -> bool:
    """Enhanced validation with design constraints"""
    try:
        # Basic thermodynamic validation (existing)
        gc = calculate_gc_content(sequence)
        if not (SETTINGS['gc_min'] <= gc <= SETTINGS['gc_max']):
            return False

        tm = primer3.calc_tm(sequence,
                             mv_conc=SETTINGS['mv_conc'],
                             dv_conc=SETTINGS['dv_conc'],
                             dntp_conc=SETTINGS['dntp_conc'],
                             dna_conc=SETTINGS['dna_conc'])
        if not (SETTINGS['tm_min'] <= tm <= SETTINGS['tm_max']):
            return False

        hairpin = primer3.calc_hairpin(sequence,
                                       mv_conc=SETTINGS['mv_conc'],
                                       dv_conc=SETTINGS['dv_conc'],
                                       dntp_conc=SETTINGS['dntp_conc'],
                                       dna_conc=SETTINGS['dna_conc'])
        if hairpin.tm > SETTINGS['hairpin_max']:
            return False

        homodimer = primer3.calc_homodimer(sequence,
                                           mv_conc=SETTINGS['mv_conc'],
                                           dv_conc=SETTINGS['dv_conc'],
                                           dntp_conc=SETTINGS['dntp_conc'],
                                           dna_conc=SETTINGS['dna_conc'])
        if homodimer.tm > SETTINGS['self_dimer_max']:
            return False

        # 3' end checks (existing)
        if len(sequence) >= SETTINGS['three_prime_length']:
            three_prime = sequence[-SETTINGS['three_prime_length']:]

            three_prime_hairpin = primer3.calc_hairpin(three_prime,
                                                       mv_conc=SETTINGS['mv_conc'],
                                                       dv_conc=SETTINGS['dv_conc'],
                                                       dntp_conc=SETTINGS['dntp_conc'],
                                                       dna_conc=SETTINGS['dna_conc'])
            if three_prime_hairpin.tm > SETTINGS['three_prime_hairpin_max']:
                return False

            three_prime_homodimer = primer3.calc_homodimer(three_prime,
                                                           mv_conc=SETTINGS['mv_conc'],
                                                           dv_conc=SETTINGS['dv_conc'],
                                                           dntp_conc=SETTINGS['dntp_conc'],
                                                           dna_conc=SETTINGS['dna_conc'])
            if three_prime_homodimer.tm > SETTINGS['three_prime_self_dimer_max']:
                return False

        # NEW: Design constraint checks
        if has_repetitive_patterns(sequence):
            return False

        if not check_symmetry_constraints(sequence):
            return False

        if has_problematic_motifs(sequence):
            return False

        return True

    except Exception:
        return False


def generate_sequences_for_length(args) -> tuple:
    """Generate sequences for a specific length (worker function)"""
    length, target_count, existing_sequences = args

    bases = ['A', 'T', 'G', 'C']
    valid_sequences = []
    attempts = 0
    max_attempts = target_count * 1000  # Reasonable limit

    existing_set = set(existing_sequences)

    while len(valid_sequences) < target_count and attempts < max_attempts:
        attempts += 1

        # Generate random sequence
        sequence = ''.join(random.choice(bases) for _ in range(length))

        # Skip if exists
        if sequence in existing_set or sequence in valid_sequences:
            continue

        # Validate
        if validate_sequence(sequence):
            valid_sequences.append(sequence)

        # Progress log every 10000 attempts
        if attempts % 10000 == 0:
            print(f"Length {length}: {len(valid_sequences)}/{target_count} - {attempts} attempts")

    return length, valid_sequences, attempts


def get_existing_sequences(redis_client, length: int) -> List[str]:
    """Get existing sequences for a length"""
    try:
        key = f"sequences:length:{length}"
        return list(redis_client.smembers(key))
    except Exception:
        return []


def save_sequences(redis_client, length: int, sequences: List[str]):
    """Save sequences to Redis"""
    if not sequences:
        return

    key = f"sequences:length:{length}"
    redis_client.sadd(key, *sequences)

    # Save metadata
    metadata_key = f"sequences:length:{length}:metadata"
    metadata = {
        'length': length,
        'count': len(sequences),
        'updated': datetime.now().isoformat(),
        'settings': SETTINGS
    }
    redis_client.set(metadata_key, str(metadata))


def clear_redis_database(redis_client):
    """Clear all sequence data from Redis with confirmation"""
    try:
        # Get current counts
        total_sequences = 0
        length_counts = {}

        for length in range(7, 26):
            count = redis_client.scard(f"sequences:length:{length}")
            if count > 0:
                length_counts[length] = count
                total_sequences += count

        if total_sequences == 0:
            print("Redis database is already empty")
            return

        print(f"\nCurrent database contents:")
        for length, count in sorted(length_counts.items()):
            print(f"  Length {length}: {count} sequences")
        print(f"Total: {total_sequences} sequences")

        # Confirmation prompt
        print(f"\nWARNING: This will permanently delete all {total_sequences} sequences!")
        confirm = input("Type 'DELETE ALL' to confirm: ").strip()

        if confirm != "DELETE ALL":
            print("Database clear cancelled")
            return

        # Clear all sequence data
        keys_deleted = 0
        for length in range(7, 26):
            seq_key = f"sequences:length:{length}"
            meta_key = f"sequences:length:{length}:metadata"

            if redis_client.exists(seq_key):
                redis_client.delete(seq_key)
                keys_deleted += 1

            if redis_client.exists(meta_key):
                redis_client.delete(meta_key)
                keys_deleted += 1

        # Also clear any orthogonal sets if they exist
        orthogonal_keys = redis_client.keys("orthogonal_set:*")
        if orthogonal_keys:
            redis_client.delete(*orthogonal_keys)
            keys_deleted += len(orthogonal_keys)

        print(f"Database cleared successfully!")
        print(f"Deleted {keys_deleted} Redis keys")
        print(f"Removed {total_sequences} sequences")

    except Exception as e:
        print(f"Error clearing database: {e}")


def show_database_status(redis_client):
    """Show current database status"""
    try:
        print("Redis Database Status:")
        print("-" * 30)

        total_sequences = 0
        total_keys = 0

        for length in range(7, 26):
            seq_key = f"sequences:length:{length}"
            count = redis_client.scard(seq_key)

            if count > 0:
                print(f"Length {length:2d}: {count:4d} sequences")
                total_sequences += count
                total_keys += 1

        if total_sequences == 0:
            print("Database is empty")
        else:
            print("-" * 30)
            print(f"Total: {total_sequences} sequences across {total_keys} lengths")

        # Check for orthogonal sets
        orthogonal_keys = redis_client.keys("orthogonal_set:*")
        if orthogonal_keys:
            print(f"Orthogonal sets: {len(orthogonal_keys)}")

        # Redis info
        info = redis_client.info()
        memory = info.get('used_memory_human', 'unknown')
        print(f"Redis memory usage: {memory}")

    except Exception as e:
        print(f"Error checking database status: {e}")


def main():
    # Connect to Redis
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        print("Connected to Redis")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return

    # Command line argument handling
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "clear":
            clear_redis_database(redis_client)
            return
        elif command == "status":
            show_database_status(redis_client)
            return
        elif command == "help":
            print("Usage:")
            print("  python generate_sequences_parallel.py        # Generate sequences")
            print("  python generate_sequences_parallel.py clear  # Clear database")
            print("  python generate_sequences_parallel.py status # Show database status")
            return
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for available commands")
            return

    # Show current status first
    show_database_status(redis_client)

    # Configuration
    target_lengths = list(range(7, 26))  # 7 to 25
    max_sequences_per_length = 1000
    num_processes = min(cpu_count(), len(target_lengths))

    print(f"\nGeneration Configuration:")
    print(f"Target lengths: {target_lengths[0]}-{target_lengths[-1]}")
    print(f"Target: {max_sequences_per_length} sequences per length")
    print(f"Using {num_processes} processes")

    # Ask for confirmation if database has content
    total_existing = sum(redis_client.scard(f"sequences:length:{length}") for length in target_lengths)
    if total_existing > 0:
        print(f"\nDatabase contains {total_existing} existing sequences")
        proceed = input("Continue with generation? (y/n): ").strip().lower()
        if proceed != 'y':
            print("Generation cancelled")
            return

    # Prepare work for each length
    work_items = []
    for length in target_lengths:
        existing = get_existing_sequences(redis_client, length)
        needed = max_sequences_per_length - len(existing)

        if needed > 0:
            work_items.append((length, needed, existing))
            print(f"Length {length}: need {needed} more sequences (have {len(existing)})")
        else:
            print(f"Length {length}: already have {len(existing)} sequences")

    if not work_items:
        print("All lengths already have sufficient sequences")
        return

    # Generate in parallel
    print(f"\nStarting parallel generation...")
    start_time = time.time()

    with Pool(processes=num_processes) as pool:
        results = pool.map(generate_sequences_for_length, work_items)

    # Save results
    total_generated = 0
    total_attempts = 0

    for length, sequences, attempts in results:
        if sequences:
            save_sequences(redis_client, length, sequences)
            total_generated += len(sequences)
            print(f"Length {length}: generated {len(sequences)} sequences in {attempts} attempts")
        total_attempts += attempts

    # Summary
    elapsed = time.time() - start_time
    print(f"\nGeneration complete:")
    print(f"Total sequences generated: {total_generated}")
    print(f"Total attempts: {total_attempts}")
    print(f"Success rate: {(total_generated / total_attempts * 100):.1f}%")
    print(f"Time: {elapsed:.1f} seconds")

    # Show final status
    print("\nFinal database status:")
    show_database_status(redis_client)


if __name__ == "__main__":
    main()