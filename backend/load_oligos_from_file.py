#!/usr/bin/env python3
"""
Load sequences from backend/data/oligos.txt into Redis
Simple loader for your existing oligo sequences
"""

import redis
import json
import os
from collections import defaultdict
from typing import Dict, List

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content percentage"""
    if not sequence:
        return 0.0
    gc_count = sequence.count('G') + sequence.count('C')
    return (gc_count / len(sequence)) * 100


def categorize_by_gc(gc_content: float) -> str:
    """Categorize GC content into ranges"""
    if gc_content < 30:
        return "20_30"
    elif gc_content < 40:
        return "30_40"
    elif gc_content < 50:
        return "40_50"
    elif gc_content < 60:
        return "50_60"
    elif gc_content < 70:
        return "60_70"
    else:
        return "70_80"


def load_oligos_from_file(filepath: str) -> List[str]:
    """Load sequences from oligos.txt file"""

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return []

    sequences = []

    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip().upper()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Validate DNA sequence
                if not all(base in 'ATGC' for base in line):
                    print(f"⚠️ Line {line_num}: Invalid characters in sequence: {line}")
                    continue

                sequences.append(line)

        print(f"✅ Loaded {len(sequences)} sequences from {filepath}")
        return sequences

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []


def organize_sequences(sequences: List[str]) -> Dict[str, List[str]]:
    """Organize sequences by length and GC content"""

    organized = defaultdict(list)

    for seq in sequences:
        length = len(seq)
        gc_content = calculate_gc_content(seq)
        gc_range = categorize_by_gc(gc_content)

        # Create cache key format
        key = f"length_{length}:gc_{gc_range}"
        organized[key].append(seq)

    return dict(organized)


def load_to_redis(organized_sequences: Dict[str, List[str]], ttl: int = 3600):
    """Load organized sequences into Redis"""

    print("\n🗄️ Loading sequences into Redis...")

    total_loaded = 0

    for key, sequences in organized_sequences.items():
        cache_key = f"sequences:{key}"

        try:
            # Store in Redis with TTL
            redis_client.setex(cache_key, ttl, json.dumps(sequences))

            print(f"✅ {cache_key}: {len(sequences)} sequences")
            total_loaded += len(sequences)

            # Store metadata
            length = int(key.split('_')[1].split(':')[0])
            gc_range = key.split('_')[2:]
            gc_min, gc_max = map(int, '_'.join(gc_range).split('_'))

            metadata = {
                'length': length,
                'count': len(sequences),
                'gc_min': gc_min,
                'gc_max': gc_max,
                'source': 'oligos.txt',
                'loaded_at': 'now'
            }

            redis_client.setex(f"{cache_key}:metadata", ttl, json.dumps(metadata))

        except Exception as e:
            print(f"❌ Failed to load {cache_key}: {e}")

    print(f"\n🎉 Successfully loaded {total_loaded} sequences into Redis!")
    return total_loaded


def show_sequence_summary(sequences: List[str]):
    """Show summary of loaded sequences"""

    if not sequences:
        return

    print(f"\n📊 Sequence Summary:")
    print(f"Total sequences: {len(sequences)}")

    # Length distribution
    length_counts = defaultdict(int)
    gc_contents = []

    for seq in sequences:
        length_counts[len(seq)] += 1
        gc_contents.append(calculate_gc_content(seq))

    print(f"\nLength distribution:")
    for length in sorted(length_counts.keys()):
        print(f"  {length}nt: {length_counts[length]} sequences")

    if gc_contents:
        avg_gc = sum(gc_contents) / len(gc_contents)
        min_gc = min(gc_contents)
        max_gc = max(gc_contents)
        print(f"\nGC content:")
        print(f"  Range: {min_gc:.1f}% - {max_gc:.1f}%")
        print(f"  Average: {avg_gc:.1f}%")


def check_redis_status():
    """Check current Redis status"""

    print("\n📡 Redis Status:")

    try:
        redis_client.ping()
        print("✅ Redis connection: OK")

        keys = redis_client.keys("sequences:*")
        keys = [k for k in keys if not k.endswith(':metadata')]

        print(f"📦 Sequence sets: {len(keys)}")

        total_sequences = 0
        for key in keys:
            try:
                data = redis_client.get(key)
                if data:
                    sequences = json.loads(data)
                    ttl = redis_client.ttl(key)
                    print(f"  {key}: {len(sequences)} sequences (TTL: {ttl}s)")
                    total_sequences += len(sequences)
            except:
                print(f"  {key}: Invalid data")

        print(f"🧬 Total sequences: {total_sequences}")

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")


def clear_oligo_sequences():
    """Clear sequences loaded from oligos.txt"""

    print("🗑️ Clearing oligo sequences from Redis...")

    keys = redis_client.keys("sequences:*")
    if keys:
        redis_client.delete(*keys)
        print(f"✅ Cleared {len(keys)} sequence sets")
    else:
        print("ℹ️ No sequences to clear")


def main():
    """Main execution function"""

    import sys

    print("🧬 Oligos.txt Redis Loader")
    print("=" * 40)

    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "clear":
            clear_oligo_sequences()
            check_redis_status()
            return
        elif sys.argv[1] == "status":
            check_redis_status()
            return

    # Load sequences from file
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'oligos.txt')
    print(filepath)
    sequences = load_oligos_from_file(filepath)

    if not sequences:
        print("❌ No sequences loaded. Check your oligos.txt file.")
        return

    # Show summary
    show_sequence_summary(sequences)

    # Organize by length and GC content
    organized = organize_sequences(sequences)

    print(f"\n📋 Organized into {len(organized)} categories:")
    for key, seqs in organized.items():
        print(f"  {key}: {len(seqs)} sequences")

    # Load to Redis
    load_to_redis(organized)

    # Show final status
    check_redis_status()


if __name__ == "__main__":
    main()

    print("\n✅ Done!")
    print("\nUsage:")
    print("  python load_oligos_from_file.py        # Load sequences from oligos.txt")
    print("  python load_oligos_from_file.py clear  # Clear all sequences")
    print("  python load_oligos_from_file.py status # Show current Redis status")
    print("\nMake sure your oligos.txt file is in backend/data/oligos.txt")