"""
Core orchestrator - Re-exports from monolithic job_scraper for modular compatibility
"""

from job_scraper import (
    JobScraperOrchestrator,
)

# Re-export for convenience
__all__ = [
    'JobScraperOrchestrator',
]