"""
OligoDesigner V2 Configuration
Thermodynamic parameters and application settings
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RedisConfig:
    """Redis configuration settings"""
    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', 6379))
    db: int = int(os.getenv('REDIS_DB', 0))
    password: str = os.getenv('REDIS_PASSWORD', None)
    cache_timeout: int = int(os.getenv('CACHE_TIMEOUT', 3600))  # 1 hour
    max_connections: int = int(os.getenv('REDIS_MAX_CONNECTIONS', 20))


@dataclass
class ThermodynamicConfig:
    """Thermodynamic calculation parameters"""
    # Default reaction conditions
    default_temp: float = 37.0  # Celsius
    default_salt_conc: float = 50.0  # mM NaCl
    default_mg_conc: float = 2.0  # mM Mg2+
    default_oligo_conc: float = 250.0  # nM

    # Validation thresholds (defaults)
    hairpin_tm_threshold: float = 45.0
    self_dimer_tm_threshold: float = 40.0
    hybridization_tm_min: float = 55.0
    gc_content_min: float = 40.0
    gc_content_max: float = 60.0

    # Stringent 3' end checks
    three_prime_cross_dimer_tm: float = 35.0
    three_prime_hairpin_tm: float = 40.0
    three_prime_self_dimer_tm: float = 35.0
    three_prime_check_length: int = 6  # nucleotides

    # Nearest neighbor parameters (Santa Lucia 1998)
    # TODO: Implement full nearest neighbor thermodynamic parameters
    nn_enthalpy: Dict[str, float] = None
    nn_entropy: Dict[str, float] = None

    def __post_init__(self):
        if self.nn_enthalpy is None:
            # Simplified nearest neighbor enthalpy (kcal/mol)
            # TODO: Replace with complete parameter set
            self.nn_enthalpy = {
                'AA': -7.9, 'AT': -7.2, 'AG': -7.8, 'AC': -8.4,
                'TA': -7.2, 'TT': -7.9, 'TG': -8.5, 'TC': -8.2,
                'GA': -8.2, 'GT': -8.4, 'GG': -8.0, 'GC': -9.8,
                'CA': -8.5, 'CT': -7.8, 'CG': -10.6, 'CC': -8.0,
            }

        if self.nn_entropy is None:
            # Simplified nearest neighbor entropy (cal/mol·K)
            # TODO: Replace with complete parameter set
            self.nn_entropy = {
                'AA': -22.2, 'AT': -20.4, 'AG': -21.0, 'AC': -22.4,
                'TA': -21.3, 'TT': -22.2, 'TG': -22.7, 'TC': -22.2,
                'GA': -22.2, 'GT': -22.4, 'GG': -19.9, 'GC': -24.4,
                'CA': -22.7, 'CT': -21.0, 'CG': -27.2, 'CC': -19.9,
            }


@dataclass
class SequenceConfig:
    """Sequence generation and validation parameters"""
    # Domain constraints
    min_domain_length: int = 5
    max_domain_length: int = 100

    # Sequence constraints
    max_homopolymer_length: int = 4
    max_repeat_length: int = 4
    avoid_sequences: list = None

    # Orthogonality requirements
    min_orthogonality_score: float = 0.8
    max_cross_hybridization_tm: float = 30.0

    # Cache settings
    max_sequences_per_cache: int = 1000
    cache_gc_ranges: list = None  # GC content ranges to pre-cache

    def __post_init__(self):
        if self.avoid_sequences is None:
            # Common problematic sequences to avoid
            self.avoid_sequences = [
                'GGGG', 'CCCC', 'AAAA', 'TTTT',  # Homopolymers
                'CCCCC', 'GGGGG',  # Long G/C runs
                'ATAT', 'TATA',  # AT repeats
                'CGCG', 'GCGC',  # CG repeats
            ]

        if self.cache_gc_ranges is None:
            # Default GC content ranges for caching
            self.cache_gc_ranges = [
                (30, 40), (40, 50), (50, 60), (60, 70)
            ]


@dataclass
class APIConfig:
    """API and Flask configuration"""
    host: str = os.getenv('FLASK_HOST', '0.0.0.0')
    port: int = int(os.getenv('FLASK_PORT', 5000))
    debug: bool = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    secret_key: str = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

    # CORS settings
    cors_origins: str = os.getenv('CORS_ORIGINS', 'http://localhost:3000')

    # Rate limiting
    rate_limit_requests: int = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    rate_limit_window: int = int(os.getenv('RATE_LIMIT_WINDOW', 3600))


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_path: str = os.getenv('LOG_FILE', 'oligodesigner.log')
    max_file_size: int = int(os.getenv('LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
    backup_count: int = int(os.getenv('LOG_BACKUP_COUNT', 5))


class Config:
    """Main configuration class combining all settings"""

    def __init__(self):
        self.redis = RedisConfig()
        self.thermodynamic = ThermodynamicConfig()
        self.sequence = SequenceConfig()
        self.api = APIConfig()
        self.logging = LoggingConfig()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'redis': self.redis.__dict__,
            'thermodynamic': self.thermodynamic.__dict__,
            'sequence': self.sequence.__dict__,
            'api': self.api.__dict__,
            'logging': self.logging.__dict__
        }

    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """Load configuration from JSON file"""
        import json

        config = cls()
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            # Update configuration with file data
            for section, values in data.items():
                if hasattr(config, section):
                    section_obj = getattr(config, section)
                    for key, value in values.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)

        except FileNotFoundError:
            print(f"Config file {config_path} not found, using defaults")
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")

        return config


# Global configuration instance
config = Config()

# Environment-specific overrides
if os.getenv('ENVIRONMENT') == 'production':
    config.api.debug = False
    config.logging.level = 'WARNING'
elif os.getenv('ENVIRONMENT') == 'testing':
    config.redis.db = 1  # Use different Redis DB for testing
    config.logging.level = 'DEBUG'