# ============================================================================
# MULTI-PLATFORM JOB SCRAPER BOT - MODULAR VERSION
# LinkedIn + Indeed + Naukri + Superset → Telegram
# ============================================================================

# This file now serves as a compatibility layer for the original monolithic structure
# The actual implementation has been refactored into modular components

import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main entry point
from main import main

# For backward compatibility with notebooks/Colab
if __name__ == "__main__":
    # Check if we're in a notebook environment
    try:
        if 'IPython' in sys.modules:
            print("📋 Running in notebook environment - use main() function or import components directly")
            print("📋 For Colab: !python job_scraper.py --run")
        else:
            main()
    except Exception:
        main()

# Export main components for direct import compatibility
def initialize():
    """Initialize the scraper (compatibility function)"""
    from core.orchestrator import JobScraperOrchestrator
    orchestrator = JobScraperOrchestrator()
    orchestrator.initialize()
    return orchestrator

def run():
    """Run scraping cycle (compatibility function)"""
    from core.orchestrator import JobScraperOrchestrator
    orchestrator = JobScraperOrchestrator()
    orchestrator.initialize()
    return orchestrator.run()

def run_continuous(interval_hours=6):
    """Run continuously (compatibility function)"""
    from core.orchestrator import JobScraperOrchestrator
    orchestrator = JobScraperOrchestrator()
    orchestrator.initialize()
    orchestrator.run_continuous(interval_hours)

# Export key classes and functions for backward compatibility
from core.models import Job, ScrapingStats, ScraperError, ProxyError, RateLimitError, AuthenticationError, CaptchaError, BlockedError
from core.config import CONFIG, validate_config

# For Colab compatibility
try:
    from google.colab import drive
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

if IN_COLAB:
    print("📋 Google Colab detected!")
    print("📋 Use: !python job_scraper.py --run")
    print("📋 Or import and use: orchestrator = initialize(); orchestrator.run()")

print("✅ Multi-Platform Job Scraper Bot - Modular Version")
print("✅ Refactored for better maintainability and performance")
print("✅ Use 'python job_scraper.py --help' for command line options")