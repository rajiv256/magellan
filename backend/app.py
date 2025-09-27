"""
Main Flask application for OligoDesigner
Integrates all components and provides REST API
"""

import os
import logging
import redis
from flask import Flask, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Enable CORS for frontend communication
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Configuration
app.config.update({
    'DEBUG': os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
    'JSON_SORT_KEYS': False
})

# Initialize Redis connection
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connection established")
except Exception as e:
    logger.error(f"❌ Redis connection failed: {e}")
    logger.warning("Application will continue without Redis caching")
    redis_client = None

# Import and register API routes
try:
    from api.routes import create_routes

    api_blueprint = create_routes(redis_client)
    app.register_blueprint(api_blueprint)
    logger.info("✅ API routes registered")
except Exception as e:
    logger.error(f"❌ Error registering API routes: {e}")
    raise


# Root endpoint
@app.route('/')
def root():
    """Root endpoint with API information"""
    return jsonify({
        'service': 'OligoDesigner API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'sequences': '/api/sequences/available',
            'design': '/api/design/generate',
            'validate': '/api/validate/sequence',
            'cache': '/api/cache/status',
            'utils': '/api/utils/reverse-complement',
            'analysis': '/api/analysis/thermodynamics'
        },
        'redis_connected': redis_client is not None,
        'frontend_url': 'http://localhost:3000'
    })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested URL was not found on the server',
        'available_endpoints': [
            '/api/health',
            '/api/sequences/available',
            '/api/design/generate',
            '/api/validate/sequence',
            '/api/cache/status'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred on the server'
    }), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad request',
        'message': 'The request could not be understood by the server'
    }), 400


def check_and_populate_cache():
    """Check if Redis has sequences, populate if empty"""
    if not redis_client:
        logger.warning("Redis not available, skipping cache check")
        return

    try:
        # Check for existing sequences
        sequence_keys = redis_client.keys("sequences:*")
        sequence_data_keys = [k for k in sequence_keys if not k.endswith(':metadata')]

        if not sequence_data_keys:
            logger.info("No sequences found in Redis cache")

            # Try to load from oligos.txt
            try:
                import subprocess
                import sys

                # Run load_oligos.py script
                logger.info("Attempting to load sequences from oligos.txt...")

                script_path = os.path.join(os.path.dirname(__file__), 'load_oligos.py')
                if os.path.exists(script_path):
                    result = subprocess.run([sys.executable, script_path],
                                            capture_output=True, text=True, timeout=30)

                    if result.returncode == 0:
                        logger.info("✅ Successfully loaded sequences from oligos.txt")

                        # Check what was loaded
                        new_keys = redis_client.keys("sequences:*")
                        data_keys = [k for k in new_keys if not k.endswith(':metadata')]

                        total_sequences = 0
                        for key in data_keys:
                            try:
                                import json
                                data = redis_client.get(key)
                                if data:
                                    sequences = json.loads(data)
                                    total_sequences += len(sequences)
                            except:
                                pass

                        logger.info(f"📊 Loaded {len(data_keys)} sequence sets with {total_sequences} total sequences")
                    else:
                        logger.warning(f"⚠️ Failed to load sequences: {result.stderr}")
                        _create_sample_sequences()
                else:
                    logger.warning("load_oligos.py not found, creating sample sequences")
                    _create_sample_sequences()

            except Exception as e:
                logger.error(f"Error loading sequences: {e}")
                _create_sample_sequences()
        else:
            logger.info(f"✅ Found {len(sequence_data_keys)} sequence sets in Redis cache")

            # Log cache summary
            total_sequences = 0
            for key in sequence_data_keys[:5]:  # Show first 5 sets
                try:
                    import json
                    data = redis_client.get(key)
                    if data:
                        sequences = json.loads(data)
                        logger.info(f"  {key}: {len(sequences)} sequences")
                        total_sequences += len(sequences)
                except:
                    pass

            if len(sequence_data_keys) > 5:
                logger.info(f"  ... and {len(sequence_data_keys) - 5} more sets")

    except Exception as e:
        logger.error(f"Error checking cache: {e}")


def _create_sample_sequences():
    """Create minimal sample sequences for testing"""
    logger.info("Creating sample sequences for testing...")

    try:
        import json

        # Sample sequences for testing
        sample_data = {
            "sequences:length_15:gc_40_50": [
                "ATCGATCGATCGATC",
                "CGATCGATCGATCGA",
                "GATCGATCGATCGAT"
            ],
            "sequences:length_20:gc_40_50": [
                "ATCGATCGATCGATCGATCG",
                "CGATCGATCGATCGATCGAT",
                "GATCGATCGATCGATCGATC",
                "TACGTACGTACGTACGTACG",
                "ACGTACGTACGTACGTACGT"
            ],
            "sequences:length_25:gc_40_50": [
                "ATCGATCGATCGATCGATCGATCG",
                "CGATCGATCGATCGATCGATCGAT"
            ]
        }

        for cache_key, sequences in sample_data.items():
            redis_client.setex(cache_key, 3600, json.dumps(sequences))
            logger.info(f"  Created {cache_key}: {len(sequences)} sequences")

        logger.info("✅ Sample sequences created successfully")

    except Exception as e:
        logger.error(f"Failed to create sample sequences: {e}")


def initialize_app():
    """Initialize application components"""
    logger.info("🚀 Initializing OligoDesigner application...")

    # Check Redis and populate cache if needed
    check_and_populate_cache()

    # Log application status
    logger.info("📊 Application Status:")
    logger.info(f"  Flask Debug: {app.config['DEBUG']}")
    logger.info(f"  Redis Connected: {redis_client is not None}")

    if redis_client:
        try:
            info = redis_client.info()
            memory_usage = info.get('used_memory_human', 'Unknown')
            logger.info(f"  Redis Memory: {memory_usage}")
        except:
            pass

    logger.info("✅ Application initialization complete")


def create_app():
    """Application factory for testing"""
    return app


if __name__ == '__main__':
    # Initialize application
    initialize_app()

    # Development server settings
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    logger.info("🌐 Starting development server...")
    logger.info(f"  Host: {host}")
    logger.info(f"  Port: {port}")
    logger.info(f"  Debug: {debug}")
    logger.info("=" * 50)

    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("👋 Server shutdown requested")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        logger.info("🛑 Server stopped")