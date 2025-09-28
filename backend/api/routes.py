"""
Simplified API routes for OligoDesigner
Only handles individual sequences by length, no orthogonal sets
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from typing import Dict, List, Any, Optional

from core.models import Domain, Strand, ValidationSettings, ValidationResult
from core.generator import SequenceGenerator
from core.validator import SequenceValidator

logger = logging.getLogger(__name__)


def create_routes(redis_client):
    """Create API routes with Redis client dependency injection"""

    # Create blueprint for API routes
    api_bp = Blueprint('api', __name__, url_prefix='/api')

    @api_bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            redis_status = "connected"
            total_sequences = 0

            if redis_client:
                redis_client.ping()
                # Count total sequences across all lengths
                for length in range(7, 26):
                    total_sequences += redis_client.scard(f"sequences:length:{length}")
        except Exception as e:
            redis_status = f"error: {str(e)}"

        return jsonify({
            'status': 'healthy',
            'service': 'oligodesigner',
            'redis': redis_status,
            'total_sequences': total_sequences,
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat()
        })

    @api_bp.route('/design/generate', methods=['POST'])
    def generate_design():
        """Generate oligonucleotide design using individual sequences by length"""
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            # Parse request data
            domains_data = data.get('domains', [])
            strands_data = data.get('strands', [])
            settings_data = data.get('settings', {})

            logger.info(f"Design request: {len(domains_data)} domains, {len(strands_data)} strands")

            # Create validation settings
            settings = ValidationSettings(**{k: v for k, v in settings_data.items()
                                             if hasattr(ValidationSettings, k)})

            # Create domain objects
            domains = []
            for i, domain_data in enumerate(domains_data):
                domain = Domain(
                    id=domain_data.get('id', i),
                    name=domain_data.get('name', f'domain_{i}'),
                    length=domain_data.get('length', 20),
                    sequence=domain_data.get('fixedSequence', ''),
                    role=domain_data.get('role', 'binding'),
                    isComplement=domain_data.get('isComplement', False),
                    complementOf=domain_data.get('complementOf', None)
                )
                domains.append(domain)

            # Check sequence availability for required lengths
            generator = SequenceGenerator(redis_client)
            required_lengths = [d.length for d in domains if not d.isComplement and not d.sequence]
            availability = generator.check_sequences_available(required_lengths)

            # Check if all required lengths are available
            missing_lengths = [length for length, info in availability.items() if not info['available']]
            if missing_lengths:
                return jsonify({
                    'error': 'Sequences not available for required lengths',
                    'missing_lengths': missing_lengths,
                    'availability': availability
                }), 400

            # Generate sequences for domains that don't have fixed sequences
            domains_to_design = [d for d in domains if not d.sequence]
            if domains_to_design:
                design_success = generator.design_domain_sequences(domains_to_design)

                if not design_success:
                    return jsonify({
                        'error': 'Failed to design domain sequences',
                        'details': 'Sequence generation failed - may be cross-dimer conflicts'
                    }), 400

            # Create strand objects and generate sequences
            strands = []
            for i, strand_data in enumerate(strands_data):
                # Get domain IDs for this strand - check multiple possible keys
                domain_ids = strand_data.get('domains', [])
                if not domain_ids:
                    domain_ids = strand_data.get('domainIds', [])
                if not domain_ids:
                    domain_ids = strand_data.get('domain_ids', [])

                logger.info(f"Strand {i}: domain_ids = {domain_ids}, strand_data = {strand_data}")

                # Concatenate sequences from domains
                strand_sequence = ""
                for domain_id in domain_ids:
                    domain = next((d for d in domains if d.id == domain_id), None)
                    if domain and domain.sequence:
                        strand_sequence += domain.sequence
                        logger.info(f"Added domain {domain_id} sequence: {domain.sequence}")

                strand = Strand(
                    id=strand_data.get('id', i),
                    name=strand_data.get('name', f'strand_{i}'),
                    domainIds=domain_ids,
                    sequence=strand_sequence,
                    validated=False
                )
                strands.append(strand)
                logger.info(
                    f"Created strand: {strand.name}, sequence: {strand.sequence}, domainIds: {strand.domainIds}")

            # Validate all sequences
            validator = SequenceValidator(settings)
            validation_results = {}

            # Validate each strand
            for strand in strands:
                if strand.sequence:
                    strand_validation = validator.validate_strand(strand, domains)
                    validation_results[strand.id] = strand_validation
                    strand.validated = True

            # Validate cross-interactions between strands
            cross_validation = validator.validate_cross_interactions(strands)

            # Convert validation results to serializable format
            serialized_validation = {}
            for strand_id, results in validation_results.items():
                serialized_validation[str(strand_id)] = {
                    check_name: {
                        'passed': result.passed,
                        'value': str(result.value),
                        'threshold': str(result.threshold),
                        'details': result.details,
                        'check_type': getattr(result, 'check_type', check_name)
                    } for check_name, result in results.items()
                }

            # Convert cross-validation results
            serialized_cross_validation = {}
            for (strand1_id, strand2_id), results in cross_validation.items():
                pair_key = f"{strand1_id}_{strand2_id}"
                serialized_cross_validation[pair_key] = {
                    check_name: {
                        'passed': result.passed,
                        'value': str(result.value),
                        'threshold': str(result.threshold),
                        'details': result.details,
                        'check_type': getattr(result, 'check_type', check_name)
                    } for check_name, result in results.items()
                }

            # Create response
            response = {
                'success': True,
                'domains': [
                    {
                        'id': d.id,
                        'name': d.name,
                        'sequence': d.sequence,
                        'length': d.length,
                        'role': d.role,
                        'isComplement': d.isComplement,
                        'complementOf': d.complementOf
                    }
                    for d in domains
                ],
                'strands': [
                    {
                        'id': s.id,
                        'name': s.name,
                        'sequence': s.sequence,
                        'domainIds': s.domainIds,
                        'validated': s.validated
                    }
                    for s in strands
                ],
                'validation': {
                    'strand_validation': serialized_validation,
                    'cross_validation': serialized_cross_validation
                },
                'metadata': {
                    'generation_timestamp': datetime.now().isoformat(),
                    'total_domains': len(domains),
                    'total_strands': len(strands),
                    'sequences_used': len(generator.used_sequences),
                    'validation_settings': settings.__dict__
                }
            }

            return jsonify(response)

        except Exception as e:
            logger.error(f"Error in generate_design: {e}")
            return jsonify({'error': f'Design generation failed: {str(e)}'}), 500

    @api_bp.route('/sequences/lengths', methods=['GET'])
    def get_available_lengths():
        """List all available lengths with sequence counts"""
        try:
            if not redis_client:
                return jsonify({'error': 'Redis cache not available'}), 503

            generator = SequenceGenerator(redis_client)
            available_lengths = generator.list_available_lengths()

            return jsonify({
                'success': True,
                'total_lengths': len(available_lengths),
                'available_lengths': available_lengths
            })

        except Exception as e:
            logger.error(f"Error in get_available_lengths: {e}")
            return jsonify({'error': f'Failed to retrieve lengths: {str(e)}'}), 500

    @api_bp.route('/sequences/length/<int:length>', methods=['GET'])
    def get_length_details(length):
        """Get detailed information about sequences for a specific length"""
        try:
            if not redis_client:
                return jsonify({'error': 'Redis cache not available'}), 503

            generator = SequenceGenerator(redis_client)
            length_info = generator.get_length_info(length)

            if not length_info:
                return jsonify({'error': f'No sequences found for length {length}'}), 404

            # Get detailed statistics
            stats = generator.get_sequence_statistics(length)

            return jsonify({
                'success': True,
                'length': length,
                'info': length_info,
                'statistics': stats
            })

        except Exception as e:
            logger.error(f"Error in get_length_details: {e}")
            return jsonify({'error': f'Failed to retrieve length details: {str(e)}'}), 500

    @api_bp.route('/sequences/available', methods=['POST'])
    def get_available_sequences():
        """Check availability of sequences for given domain specifications"""
        try:
            data = request.json
            if not data or 'domains' not in data:
                return jsonify({'error': 'Missing domains in request'}), 400

            domains_specs = data['domains']
            generator = SequenceGenerator(redis_client)

            # Extract required lengths
            required_lengths = []
            for domain_spec in domains_specs:
                length = domain_spec.get('length', 20)
                if length not in required_lengths:
                    required_lengths.append(length)

            # Check availability
            availability = generator.check_sequences_available(required_lengths)

            # Get sample sequences for each length
            samples = {}
            for length in required_lengths:
                if availability[length]['available']:
                    sample_seqs = generator.get_sequences_from_redis(length, count=3)
                    samples[length] = sample_seqs

            return jsonify({
                'success': True,
                'required_lengths': required_lengths,
                'availability': availability,
                'samples': samples,
                'all_available': all(info['available'] for info in availability.values())
            })

        except Exception as e:
            logger.error(f"Error in check_sequence_availability: {e}")
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500

    @api_bp.route('/design/validate', methods=['POST'])
    def validate_design():
        """Validate existing sequences without generating new ones"""
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            # Parse domains and strands
            domains_data = data.get('domains', [])
            strands_data = data.get('strands', [])
            settings_data = data.get('settings', {})

            # Create objects
            domains = []
            for domain_data in domains_data:
                domain = Domain(
                    id=domain_data.get('id', 0),
                    name=domain_data.get('name', ''),
                    length=domain_data.get('length', len(domain_data.get('sequence', ''))),
                    sequence=domain_data.get('sequence', ''),
                    role=domain_data.get('role', 'binding'),
                    isComplement=domain_data.get('isComplement', False),
                    complementOf=domain_data.get('complementOf', None)
                )
                domains.append(domain)

            strands = []
            for strand_data in strands_data:
                strand = Strand(
                    id=strand_data.get('id', 0),
                    name=strand_data.get('name', ''),
                    domainIds=strand_data.get('domainIds', []),
                    sequence=strand_data.get('sequence', ''),
                    validated=False
                )
                strands.append(strand)

            # Create validation settings
            settings = ValidationSettings(**{k: v for k, v in settings_data.items()
                                             if hasattr(ValidationSettings, k)})

            # Perform validation
            validator = SequenceValidator(settings)
            validation_results = {}

            # Validate each strand
            for strand in strands:
                if strand.sequence:
                    strand_validation = validator.validate_strand(strand, domains)
                    validation_results[strand.id] = {
                        check_name: result.to_dict() for check_name, result in strand_validation.items()
                    }

            # Validate cross-interactions
            cross_validation = validator.validate_cross_interactions(strands)
            cross_results = {}
            for (strand1_id, strand2_id), results in cross_validation.items():
                pair_key = f"{strand1_id}_{strand2_id}"
                cross_results[pair_key] = {
                    check_name: result.to_dict() for check_name, result in results.items()
                }

            return jsonify({
                'success': True,
                'validation': {
                    'strand_validation': validation_results,
                    'cross_validation': cross_results
                },
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in validate_design: {e}")
            return jsonify({'error': f'Validation failed: {str(e)}'}), 500

    @api_bp.route('/database/stats', methods=['GET'])
    def get_database_stats():
        """Get Redis database statistics"""
        try:
            if not redis_client:
                return jsonify({'error': 'Redis cache not available'}), 503

            generator = SequenceGenerator(redis_client)
            stats = generator.get_database_stats()

            return jsonify({
                'success': True,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in get_database_stats: {e}")
            return jsonify({'error': f'Failed to retrieve stats: {str(e)}'}), 500

    @api_bp.route('/cache/status', methods=['GET'])
    def cache_status():
        """Get Redis cache status and statistics"""
        try:
            if not redis_client:
                return jsonify({
                    'connected': False,
                    'error': 'Redis not available'
                })

            # Test connection
            redis_client.ping()

            # Count sequence keys and total sequences
            sequence_keys = 0
            total_sequences = 0

            for length in range(7, 26):
                key = f"sequences:length:{length}"
                if redis_client.exists(key):
                    sequence_keys += 1
                    total_sequences += redis_client.scard(key)

            # Get Redis info
            info = redis_client.info()

            stats = {
                'connected': True,
                'total_keys': redis_client.dbsize(),
                'sequence_keys': sequence_keys,
                'total_sequences': total_sequences,
                'memory_usage': info.get('used_memory_human', 'unknown'),
                'uptime': info.get('uptime_in_seconds', 0),
                'last_updated': datetime.now().isoformat()
            }

            return jsonify(stats)

        except Exception as e:
            logger.error(f"Error in cache_status: {e}")
            return jsonify({
                'connected': False,
                'error': str(e)
            })

    # Error handlers
    @api_bp.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400

    @api_bp.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': str(error)}), 404

    @api_bp.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

    return api_bp