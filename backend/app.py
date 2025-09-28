#!/usr/bin/env python3
"""
OligoDesigner Backend
Flask API for oligonucleotide design with penalty-based scoring
"""

import random
import itertools
from flask import Flask, request, jsonify
from flask_cors import CORS
import primer3

app = Flask(__name__)
CORS(app)

# Domain sequences repository
DOMAIN_SEQUENCES = {
    'a': 'GTCAGTGACCTGATCGACTGATCG',
    'b': 'CGATCAGTCGATCAGGTCACTGAC',
    'c': 'TACTGACGTCAGTGCAGTGACGTA',
    'd': 'TACGTCACTGCACTGACGTCAGTA',
    'e': 'GACTAGCTGACGTACGTGACTAGC',
    'f': 'GCTAGTCACGTACGTCAGCTAGTC'
}


# Generate reverse complements for starred domains
def get_reverse_complement(seq):
    """Get reverse complement of DNA sequence"""
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
    return ''.join(complement.get(base, base) for base in reversed(seq))


# Add reverse complements to domain repository
for domain, seq in list(DOMAIN_SEQUENCES.items()):
    DOMAIN_SEQUENCES[f"{domain}*"] = get_reverse_complement(seq)


def generate_random_sequence(length):
    """Generate random DNA sequence of given length"""
    return ''.join(random.choices('ATGC', k=length))


def get_domain_sequence(domain_name, length=None):
    """Get sequence for a domain, generating random if not in repository"""
    if domain_name in DOMAIN_SEQUENCES:
        return DOMAIN_SEQUENCES[domain_name]
    elif length:
        return generate_random_sequence(length)
    else:
        return generate_random_sequence(20)  # Default length


def construct_strand_sequence(domains):
    """Construct full strand sequence from domain list"""
    sequence = ""
    for domain in domains:
        if '*' in domain:
            base_domain = domain.replace('*', '')
            domain_seq = get_domain_sequence(base_domain)
            sequence += get_reverse_complement(domain_seq)
        else:
            sequence += get_domain_sequence(domain)
    return sequence


def calculate_hairpin_tm(sequence):
    """Calculate hairpin melting temperature using primer3"""
    try:
        result = primer3.calc_hairpin_tm(sequence)
        return result
    except:
        return 0.0


def calculate_self_dimer_tm(sequence):
    """Calculate self-dimer melting temperature using primer3"""
    try:
        result = primer3.calc_homodimer_tm(sequence)
        return result
    except:
        return 0.0


def calculate_cross_dimer_tm(seq1, seq2):
    """Calculate cross-dimer melting temperature using primer3"""
    try:
        result = primer3.calc_heterodimer_tm(seq1, seq2)
        return result
    except:
        return 0.0


def calculate_3prime_stability(sequence):
    """Calculate 3' end stability (simplified)"""
    if len(sequence) < 5:
        return 0.0

    # Check last 5 bases for GC content
    three_prime = sequence[-5:]
    gc_count = three_prime.count('G') + three_prime.count('C')
    return (gc_count / 5.0) * 100


def calculate_gc_content(sequence):
    """Calculate GC content percentage"""
    if not sequence:
        return 0.0
    gc_count = sequence.count('G') + sequence.count('C')
    return (gc_count / len(sequence)) * 100


def calculate_strand_set_score(strand_sequences, settings=None):
    """Calculate penalty-based score for a strand set"""
    if settings is None:
        settings = {
            'hairpin_threshold': 32.0,
            'self_dimer_threshold': 45.0,
            'cross_dimer_threshold': 40.0,
            'three_prime_threshold': 8.0,
            'gc_min': 30.0,
            'gc_max': 70.0
        }

    score = 100.0  # Start with perfect score
    penalties = []
    details = {
        'score': score,
        'penalties': penalties,
        'hairpin_scores': [],
        'self_dimer_scores': [],
        'cross_dimer_scores': [],
        'three_prime_scores': [],
        'gc_content_scores': []
    }

    # 1. Hairpin penalties
    for strand_name, sequence in strand_sequences.items():
        if sequence:
            hairpin_tm = calculate_hairpin_tm(sequence)
            details['hairpin_scores'].append(hairpin_tm)

            if hairpin_tm > settings['hairpin_threshold']:
                penalty = (hairpin_tm - settings['hairpin_threshold']) * 2.0
                score -= penalty
                penalties.append(f"Hairpin penalty {strand_name}: {penalty:.1f}")

    # 2. Self-dimer penalties
    for strand_name, sequence in strand_sequences.items():
        if sequence:
            self_dimer_tm = calculate_self_dimer_tm(sequence)
            details['self_dimer_scores'].append(self_dimer_tm)

            if self_dimer_tm > settings['self_dimer_threshold']:
                penalty = (self_dimer_tm - settings['self_dimer_threshold']) * 1.5
                score -= penalty
                penalties.append(f"Self-dimer penalty {strand_name}: {penalty:.1f}")

    # 3. Cross-dimer penalties (high penalty as requested)
    strand_list = list(strand_sequences.items())
    for i, (name1, seq1) in enumerate(strand_list):
        for j, (name2, seq2) in enumerate(strand_list[i + 1:], i + 1):
            if seq1 and seq2:
                cross_dimer_tm = calculate_cross_dimer_tm(seq1, seq2)
                details['cross_dimer_scores'].append(cross_dimer_tm)

                if cross_dimer_tm > settings['cross_dimer_threshold']:
                    penalty = (cross_dimer_tm - settings['cross_dimer_threshold']) * 5.0  # High penalty
                    score -= penalty
                    penalties.append(f"Cross-dimer penalty {name1}-{name2}: {penalty:.1f}")

    # 4. 3' end stability penalties
    for strand_name, sequence in strand_sequences.items():
        if sequence:
            three_prime_stability = calculate_3prime_stability(sequence)
            details['three_prime_scores'].append(three_prime_stability)

            # Penalty for too high 3' stability
            if three_prime_stability > 80.0:
                penalty = (three_prime_stability - 80.0) * 0.5
                score -= penalty
                penalties.append(f"3' stability penalty {strand_name}: {penalty:.1f}")

    # 5. GC content penalties
    for strand_name, sequence in strand_sequences.items():
        if sequence:
            gc_content = calculate_gc_content(sequence)
            details['gc_content_scores'].append(gc_content)

            if gc_content < settings['gc_min'] or gc_content > settings['gc_max']:
                penalty = max(settings['gc_min'] - gc_content, gc_content - settings['gc_max']) * 0.3
                score -= penalty
                penalties.append(f"GC content penalty {strand_name}: {penalty:.1f}")

    # Ensure score doesn't go below 0
    score = max(0.0, score)
    details['score'] = score

    return score, details


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'OligoDesigner backend is running'})


@app.route('/api/generate-strand-sets', methods=['POST'])
def generate_strand_sets():
    """Generate strand sets based on domain specifications"""
    try:
        data = request.get_json()
        strands = data.get('strands', [])
        max_sets = min(data.get('max_sets', 100), 1000)  # Cap at 1000 as requested

        if not strands:
            return jsonify({'error': 'No strands provided'}), 400

        # Generate strand sets
        strand_sets = []

        for _ in range(max_sets):
            strand_set = {}
            for strand in strands:
                # Generate sequence for each strand
                domains = strand.get('domains', [])
                sequence = construct_strand_sequence(domains)
                strand_set[strand['name']] = sequence

            strand_sets.append({
                'strands': strand_set,
                'id': len(strand_sets)
            })

        return jsonify({
            'success': True,
            'strand_sets': strand_sets,
            'count': len(strand_sets)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-optimized-strand-sets', methods=['POST'])
def generate_optimized_strand_sets():
    """Generate and optimize strand sets with penalty-based scoring"""
    try:
        data = request.get_json()
        strands = data.get('strands', [])
        max_sets = min(data.get('max_sets', 100), 1000)  # Cap at 1000 as requested

        if not strands:
            return jsonify({'error': 'No strands provided'}), 400

        # Generate and score strand sets
        scored_sets = []

        for _ in range(max_sets):
            strand_sequences = {}
            for strand in strands:
                domains = strand.get('domains', [])
                sequence = construct_strand_sequence(domains)
                strand_sequences[strand['name']] = sequence

            # Calculate score for this set
            score, details = calculate_strand_set_score(strand_sequences)

            scored_sets.append({
                'strands': strand_sequences,
                'score': score,
                'details': details,
                'id': len(scored_sets)
            })

        # Sort by score (highest first)
        scored_sets.sort(key=lambda x: x['score'], reverse=True)

        # Return top 10 sets
        top_sets = scored_sets[:10]

        return jsonify({
            'success': True,
            'optimized_sets': top_sets,
            'total_generated': len(scored_sets),
            'returned': len(top_sets)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate-strand-set', methods=['POST'])
def validate_strand_set():
    """Validate a specific strand set"""
    try:
        data = request.get_json()
        strand_sequences = data.get('strands', {})

        if not strand_sequences:
            return jsonify({'error': 'No strand sequences provided'}), 400

        # Calculate detailed validation results
        score, details = calculate_strand_set_score(strand_sequences)

        # Add individual strand analyses
        strand_analyses = {}
        for strand_name, sequence in strand_sequences.items():
            if sequence:
                strand_analyses[strand_name] = {
                    'length': len(sequence),
                    'gc_content': calculate_gc_content(sequence),
                    'hairpin_tm': calculate_hairpin_tm(sequence),
                    'self_dimer_tm': calculate_self_dimer_tm(sequence),
                    'three_prime_stability': calculate_3prime_stability(sequence)
                }

        return jsonify({
            'success': True,
            'score': score,
            'details': details,
            'strand_analyses': strand_analyses
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting OligoDesigner Backend...")
    print("Available endpoints:")
    print("  GET  /api/health - Health check")
    print("  POST /api/generate-strand-sets - Generate strand sets")
    print("  POST /api/generate-optimized-strand-sets - Generate optimized strand sets")
    print("  POST /api/validate-strand-set - Validate specific strand set")

    app.run(debug=True, host='0.0.0.0', port=5000)