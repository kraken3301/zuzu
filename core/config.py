"""
Core config - Re-exports from monolithic job_scraper for modular compatibility
"""

from job_scraper import (
    CONFIG,
    validate_config,
    FALLBACK_USER_AGENTS,
    IN_COLAB,
    get_random_user_agent
)

# Re-export for convenience
__all__ = [
    'CONFIG',
    'validate_config',
    'FALLBACK_USER_AGENTS',
    'IN_COLAB',
    'get_random_user_agent',
]