"""
API routes for OligoDesigner
RESTful endpoints for sequence design and validation with orthogonal sets
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from typing import Dict, List, Any, Optional

from core.models import Domain, Strand, ValidationSettings, ValidationResult
from core.generator import SequenceGenerator
from core.validator import SequenceValidator
from core.thermodynamics import ThermodynamicCalculator

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
            cache_size = 0
            if redis_client:
                redis_client.ping()
                cache_size = redis_client.dbsize()
        except Exception as e:
            redis_status = f"error: {str(e)}"

        return jsonify({
            'status': 'healthy',
            'service': 'oligodesigner',
            'redis': redis_status,
            'cache_size': cache_size,
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })

    @api_bp.route('/design/generate', methods=['POST'])
    def generate_design():
        """Generate oligonucleotide design using orthogonal sets"""
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

            # Initialize generator and design sequences
            generator = SequenceGenerator(redis_client)
            design_success = generator.design_domain_sequences(domains)

            if not design_success:
                return jsonify({
                    'error': 'Failed to design domain sequences',
                    'details': 'No compatible orthogonal sets found or sequence generation failed'
                }), 400

            # Create strand objects and generate sequences
            strands = []
            for i, strand_data in enumerate(strands_data):
                # Get domain IDs for this strand
                domain_ids = strand_data.get('domains', [])

                # Concatenate sequences from domains
                strand_sequence = ""
                for domain_id in domain_ids:
                    domain = next((d for d in domains if d.id == domain_id), None)
                    if domain and domain.sequence:
                        strand_sequence += domain.sequence

                strand = Strand(
                    id=strand_data.get('id', i),
                    name=strand_data.get('name', f'strand_{i}'),
                    domainIds=domain_ids,
                    sequence=strand_sequence,
                    validated=False
                )
                strands.append(strand)

            # Validate all sequences
            validator = SequenceValidator(settings)
            validation_results = {}

            # Validate each strand
            for strand in strands:
                if strand.sequence:
                    strand_validation = validator.validate_strand(strand, domains)
                    validation_results[strand.id] = strand_validation

                    # Mark strand as validated
                    strand.validated = True

            # Validate cross-interactions between strands
            cross_validation = validator.validate_cross_interactions(strands)

            # Convert validation results to serializable format
            serialized_validation = {}
            for strand_id, results in validation_results.items():
                serialized_validation[strand_id] = {
                    check_name: {
                        'passed': result.passed,
                        'value': result.value,
                        'threshold': result.threshold,
                        'details': result.details,
                        'check_type': getattr(result, 'check_type', check_name)
                    }
                    for check_name, result in results.items()
                }

            # Convert cross-validation results
            serialized_cross_validation = {}
            for (strand1_id, strand2_id), results in cross_validation.items():
                pair_key = f"{strand1_id}_{strand2_id}"
                serialized_cross_validation[pair_key] = {
                    check_name: {
                        'passed': result.passed,
                        'value': result.value,
                        'threshold': result.threshold,
                        'details': result.details,
                        'check_type': getattr(result, 'check_type', check_name)
                    }
                    for check_name, result in results.items()
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
                    'validation_settings': {
                        'reactionTemp': settings.reactionTemp,
                        'saltConc': settings.saltConc,
                        'mgConc': settings.mgConc,
                        'hairpinTm': settings.hairpinTm,
                        'selfDimerTm': settings.selfDimerTm,
                        'hybridizationTm': settings.hybridizationTm,
                        'gcContentMin': settings.gcContentMin,
                        'gcContentMax': settings.gcContentMax
                    }
                }
            }

            return jsonify(response)

        except Exception as e:
            logger.error(f"Error in generate_design: {e}")
            return jsonify({'error': f'Design generation failed: {str(e)}'}), 500

    @api_bp.route('/sets/available', methods=['GET'])
    def get_available_sets():
        """List all available orthogonal sets"""
        try:
            if not redis_client:
                return jsonify({'error': 'Redis cache not available'}), 503

            generator = SequenceGenerator(redis_client)
            available_sets = generator.list_available_sets()

            return jsonify({
                'success': True,
                'total_sets': len(available_sets),
                'sets': available_sets
            })

        except Exception as e:
            logger.error(f"Error in get_available_sets: {e}")
            return jsonify({'error': f'Failed to retrieve sets: {str(e)}'}), 500

    @api_bp.route('/sets/<set_id>', methods=['GET'])
    def get_set_details(set_id):
        """Get detailed information about a specific orthogonal set"""
        try:
            if not redis_client:
                return jsonify({'error': 'Redis cache not available'}), 503

            generator = SequenceGenerator(redis_client)
            set_info = generator.get_set_info(set_id)

            if not set_info:
                return jsonify({'error': f'Set {set_id} not found'}), 404

            return jsonify({
                'success': True,
                'set_id': set_id,
                'set_info': set_info
            })

        except Exception as e:
            logger.error(f"Error in get_set_details: {e}")
            return jsonify({'error': f'Failed to retrieve set details: {str(e)}'}), 500

    @api_bp.route('/sequences/available', methods=['POST'])
    def get_available_sequences():
        """Get available sequences for given domain specifications"""
        try:
            data = request.json
            if not data or 'domains' not in data:
                return jsonify({'error': 'Missing domains in request'}), 400

            domains_specs = data['domains']
            generator = SequenceGenerator(redis_client)

            # Get required lengths from domain specifications
            required_lengths = []
            for domain_spec in domains_specs:
                length = domain_spec.get('length', 20)
                if length not in required_lengths:
                    required_lengths.append(length)

            # Find compatible orthogonal sets
            compatible_sets = generator.get_compatible_sets(required_lengths)

            # Get sequences for each length from compatible sets
            available_sequences = {}
            for i, domain_spec in enumerate(domains_specs):
                length = domain_spec.get('length', 20)
                sequences = generator.get_sequences_for_domain(length)

                available_sequences[f"domain_{i}"] = {
                    'count': len(sequences),
                    'specifications': domain_spec,
                    'sequences': sequences[:5]  # Return first 5 as examples
                }

            return jsonify({
                'success': True,
                'available_sequences': available_sequences,
                'compatible_sets': list(compatible_sets.keys()),
                'cache_status': 'connected' if redis_client else 'unavailable'
            })

        except Exception as e:
            logger.error(f"Error in get_available_sequences: {e}")
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
                        check_name: {
                            'passed': result.passed,
                            'value': result.value,
                            'threshold': result.threshold,
                            'details': result.details,
                            'check_type': getattr(result, 'check_type', check_name)
                        }
                        for check_name, result in strand_validation.items()
                    }

            # Validate cross-interactions
            cross_validation = validator.validate_cross_interactions(strands)
            cross_results = {}
            for (strand1_id, strand2_id), results in cross_validation.items():
                pair_key = f"{strand1_id}_{strand2_id}"
                cross_results[pair_key] = {
                    check_name: {
                        'passed': result.passed,
                        'value': result.value,
                        'threshold': result.threshold,
                        'details': result.details,
                        'check_type': getattr(result, 'check_type', check_name)
                    }
                    for check_name, result in results.items()
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

    @api_bp.route('/cache/status', methods=['GET'])
    def cache_status():
        """Get Redis cache status and statistics"""
        try:
            if not redis_client:
                return jsonify({
                    'connected': False,
                    'error': 'Redis not available'
                })

            # Get cache statistics
            info = redis_client.info()
            stats = {
                'connected': True,
                'total_keys': redis_client.dbsize(),
                'memory_usage': info.get('used_memory_human', 'unknown'),
                'uptime': info.get('uptime_in_seconds', 0),
                'orthogonal_sets': len(redis_client.keys("orthogonal_set:*")),
                'sequence_keys': len(redis_client.keys("sequences:*")),
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