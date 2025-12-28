#!/usr/bin/env python3
"""
Main entry point for the modular job scraper.

This serves as the primary command-line interface and main orchestrator
for the multi-platform job scraper bot.
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from job_scraper import (
    JobScraperOrchestrator,
    LogManager,
    validate_config,
    setup_environment as setup_colab_environment
)


def setup_logging():
    """Initialize the logging system"""
    log_manager = LogManager()
    log_manager.setup()
    return log_manager


def main():
    """Main entry point with CLI interface"""
    parser = argparse.ArgumentParser(
        description='Multi-Platform Job Scraper Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py --run
  python main.py --run --continuous
  python main.py --test-telegram
  python main.py --show-stats
  python main.py --export-csv --export-json
  python main.py --cleanup --days 30
        
For Google Colab, run: initialize() and then run() or run_continuous()
        """
    )
    
    parser.add_argument('--run', action='store_true',
                        help='Run a single scraping cycle')
    parser.add_argument('--continuous', action='store_true',
                        help='Run continuously with configured intervals')
    parser.add_argument('--test-telegram', action='store_true',
                        help='Test Telegram bot connection')
    parser.add_argument('--show-stats', action='store_true',
                        help='Show database statistics')
    parser.add_argument('--export-csv', action='store_true',
                        help='Export jobs to CSV')
    parser.add_argument('--export-json', action='store_true',
                        help='Export jobs to JSON')
    parser.add_argument('--cleanup', type=int, metavar='DAYS',
                        help='Clean up jobs older than DAYS days')
    parser.add_argument('--setup-colab', action='store_true',
                        help='Set up Colab environment (mount drive)')
    
    args = parser.parse_args()
    
    # Setup logging first
    log_manager = setup_logging()
    logger = log_manager.get_logger(__name__)
    
    valid, errors = validate_config()
    if not valid:
        logger.warning("Configuration validation failed:")
        for error in errors:
            logger.warning(f"  - {error}")
        logger.info("Continuing with warnings...")
    
    # Colab setup if requested
    if args.setup_colab:
        logger.info("Setting up Colab environment...")
        setup_colab_environment()
    
    # Initialize orchestrator
    orchestrator = JobScraperOrchestrator()
    orchestrator.initialize()
    
    # Execute commands based on arguments
    if args.test_telegram:
        if orchestrator.telegram.test_connection():
            logger.info("Telegram connection successful")
        else:
            logger.error("Telegram connection failed")
            return 1
    
    if args.show_stats:
        stats = orchestrator.get_status()
        logger.info("Current status:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
    
    if args.export_csv or args.export_json:
        if args.export_csv:
            filepath = orchestrator.db.export_to_csv()
            logger.info(f"Exported to CSV: {filepath}")
        if args.export_json:
            filepath = orchestrator.db.export_to_json()
            logger.info(f"Exported to JSON: {filepath}")
    
    if args.cleanup:
        deleted = orchestrator.db.cleanup_old_jobs(args.cleanup)
        logger.info(f"Cleaned up {deleted} jobs older than {args.cleanup} days")
    
    if args.run or args.continuous:
        if args.continuous:
            logger.info("Starting continuous scraping mode...")
            orchestrator.run_continuous()
        else:
            logger.info("Running single scraping cycle...")
            stats = orchestrator.run_once()
            logger.info(f"Run complete: {stats.total_new} new jobs found")
    elif not any([args.test_telegram, args.show_stats, 
                  args.export_csv, args.export_json, 
                  args.cleanup, args.setup_colab]):
        parser.print_help()
    
    return 0


# Interactive helper functions for Colab/ipython
class InteractiveScraper:
    """Interactive wrapper for Jupyter/Colab environments"""
    
    def __init__(self):
        self._orchestrator = None
        self._log_manager = setup_logging()
    
    def initialize(self):
        """Initialize the scraper system"""
        if self._orchestrator is None:
            self._orchestrator = JobScraperOrchestrator()
            self._orchestrator.initialize()
        else:
            print("Scraper already initialized!")
        return self._orchestrator
    
    def run(self):
        """Run single scraping cycle"""
        if self._orchestrator is None:
            print("Initialize scraper first: initialize()")
            return None
        return self._orchestrator.run_once()
    
    def run_continuous(self, interval_hours=None):
        """Run scraping continuously"""
        if self._orchestrator is None:
            print("Initialize scraper first: initialize()")
            return None
        return self._orchestrator.run_continuous(interval_hours)
    
    def get_stats(self):
        """Get current status/statistics"""
        if self._orchestrator is None:
            print("Initialize scraper first: initialize()")
            return None
        return self._orchestrator.get_status()
    
    def shutdown(self):
        """Graceful shutdown"""
        if self._orchestrator:
            self._orchestrator.shutdown()
            self._orchestrator = None
        else:
            print("No orchestrator to shutdown")
    
    def __getattr__(self, name):
        """Forward all other methods to orchestrator"""
        if self._orchestrator and hasattr(self._orchestrator, name):
            return getattr(self._orchestrator, name)
        raise AttributeError(f"No attribute '{name}'")


# Global interactive instance
_interactive_instance = InteractiveScraper()


def initialize():
    """Interactive function for Jupyter/Colab"""
    setup_environment()
    return _interactive_instance.initialize()


def run():
    """Interactive function for single run"""
    return _interactive_instance.run()


def run_continuous(interval_hours=None):
    """Interactive function for continuous mode"""
    if interval_hours is not None:
        from job_scraper import CONFIG
        CONFIG['schedule']['run_interval_hours'] = interval_hours
    return _interactive_instance.run_continuous()


def get_stats():
    """Interactive function for status"""
    stats = _interactive_instance.get_stats()
    if stats:
        print("Current Status:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    return stats


def shutdown():
    """Interactive function for shutdown"""
    _interactive_instance.shutdown()


if __name__ == "__main__":
    sys.exit(main())