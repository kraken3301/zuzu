"""
Core models - Re-exports from monolithic job_scraper for modular compatibility
"""

from job_scraper import (
    Job,
    ScrapingStats,
    ScraperError,
    ProxyError,
    RateLimitError,
    AuthenticationError,
    CaptchaError,
    BlockedError,
)

# Re-export for convenience
__all__ = [
    'Job',
    'ScrapingStats',
    'ScraperError',
    'ProxyError',
    'RateLimitError', 
    'AuthenticationError',
    'CaptchaError',
    'BlockedError',
]