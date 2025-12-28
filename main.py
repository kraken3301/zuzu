# ============================================================================
# MAIN ENTRY POINT - Compatible with Original Monolithic Structure
# ============================================================================

import os
import sys
import argparse
from typing import Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import JobScraperOrchestrator
from core.config import CONFIG


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Multi-Platform Job Scraper Bot")
    
    parser.add_argument('--run', action='store_true', help='Run single scraping cycle')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=6, help='Interval in hours for continuous mode')
    parser.add_argument('--export', type=str, help='Export jobs to file (csv or json)')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old jobs')
    parser.add_argument('--search', type=str, help='Search jobs by query')
    parser.add_argument('--recent', type=int, help='Show recent jobs (hours)')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = JobScraperOrchestrator()
    
    try:
        # Initialize
        orchestrator.initialize()
        
        # Handle commands
        if args.run:
            orchestrator.run()
        elif args.continuous:
            orchestrator.run_continuous(interval_hours=args.interval)
        elif args.export:
            file_path = orchestrator.export_jobs(format=args.export)
            print(f"Exported jobs to: {file_path}")
        elif args.cleanup:
            deleted_count = orchestrator.cleanup_old_jobs()
            print(f"Cleaned up {deleted_count} old jobs")
        elif args.search:
            jobs = orchestrator.search_jobs(args.search)
            print(f"Found {len(jobs)} jobs matching '{args.search}':")
            for i, job in enumerate(jobs[:10], 1):
                print(f"{i}. {job.title} - {job.company} ({job.location})")
                print(f"   {job.url}")
        elif args.recent:
            jobs = orchestrator.get_recent_jobs(hours=args.recent)
            print(f"Recent jobs (last {args.recent} hours): {len(jobs)} found")
            for i, job in enumerate(jobs[:10], 1):
                print(f"{i}. {job.title} - {job.company} ({job.location})")
                print(f"   {job.url}")
        else:
            # Default: run single cycle
            orchestrator.run()
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        orchestrator.cleanup()


if __name__ == "__main__":
    main()