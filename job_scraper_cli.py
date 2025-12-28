#!/usr/bin/env python3
"""
CLI wrapper for backward compatibility with modular structure
during the refactor-colab-job-scraper-split-monolith-fix-proxies-telegram-loop branch.

This provides the modular import structure that the monolithic job_scraper.py
attempts to import from, allowing it to work while the refactor is in progress.
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main CLI entry point"""
    try:
        # Import from existing job_scraper.py
        import job_scraper
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description='Multi-Platform Job Scraper Bot - CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python job_scraper_cli.py --run
  python job_scraper_cli.py --run --continuous
  python job_scraper_cli.py --test-telegram
  python job_scraper_cli.py --show-stats
  python job_scraper_cli.py --export-csv --export-json
  python job_scraper_cli.py --cleanup 30
        
Use 'python job_scraper.py' directly for Colab/interactive mode.
            """
        )
        
        parser.add_argument('--run', action='store_true', 
                            help='Run a single scraping cycle')
        parser.add_argument('--continuous', action='store_true',
                            help='Run continuously with intervals')
        parser.add_argument('--test-telegram', action='store_true',
                            help='Send test Telegram message')
        parser.add_argument('--show-stats', action='store_true',
                            help='Show database statistics')
        parser.add_argument('--export-csv', action='store_true',
                            help='Export jobs to CSV')
        parser.add_argument('--export-json', action='store_true',
                            help='Export jobs to JSON')
        parser.add_argument('--cleanup', type=int, metavar='DAYS',
                            help='Remove jobs older than DAYS days')
        
        args = parser.parse_args()
        
        # Handle the requested action
        if not any(vars(args).values()):
            parser.print_help()
            return 0
        
        # Initialize global components
        print("🚀 Initializing Job Scraper Bot...")
        try:
            job_scraper.setup_environment()
        except AttributeError:
            print("Warning: setup_environment() not found, continuing...")
        
        # Execute requested actions
        if args.show_stats:
            try:
                print("\n📊 Database Statistics:")
                print("=" * 50)
                # Try to get stats from orchestrator if available
                if hasattr(job_scraper, 'orchestrator') and job_scraper.orchestrator:
                    stats = job_scraper.orchestrator.get_status()
                    for key, value in stats.items():
                        print(f"{key}: {value}")
                else:
                    print("Orchestrator not initialized, run --run first")
                return 0
            except Exception as e:
                print(f"Error getting stats: {e}")
                return 1
        
        if args.test_telegram:
            try:
                print("📱 Testing Telegram connection...")
                # Create a simple test message integration
                import telegram
                from telegram import Bot
                
                # Try to read config
                if hasattr(job_scraper, 'CONFIG'):
                    token = job_scraper.CONFIG.get('telegram', {}).get('bot_token')
                    channel_id = job_scraper.CONFIG.get('telegram', {}).get('channel_id')
                    
                    if token and token != 'YOUR_BOT_TOKEN_HERE':
                        bot = Bot(token=token)
                        bot_info = bot.get_me()
                        print(f"✅ Bot connected: @{bot_info.username}")
                        
                        if channel_id and channel_id != '@your_channel':
                            print(f"📨 Channel configured: {channel_id}")
                        else:
                            print("⚠️  Channel not configured - update CONFIG['telegram']['channel_id']")
                    else:
                        print("⚠️  Bot token not configured - add your token to config.py")
                else:
                    print("⚠️  CONFIG not found - check job_scraper.py structure")
                return 0
            except Exception as e:
                print(f"❌ Telegram test failed: {e}")
                return 1
        
        if args.export_csv or args.export_json:
            try:
                print("🗄️  Starting export...")
                orchestrator = None
                
                # Initialize orchestrator
                if hasattr(job_scraper, 'JobScraperOrchestrator'):
                    orchestrator = job_scraper.JobScraperOrchestrator()
                    if hasattr(orchestrator, 'initialize'):
                        orchestrator.initialize()
                elif hasattr(job_scraper, 'initialize'):
                    # Fallback to initialize function
                    orchestrator = job_scraper.initialize()
                elif hasattr(job_scraper, 'orchestrator'):
                    orchestrator = job_scraper.orchestrator
                
                # Perform exports
                if args.export_csv:
                    if orchestrator and hasattr(orchestrator, 'db'):
                        filepath = orchestrator.db.export_to_csv()
                        print(f"✅ Exported to CSV: {filepath}")
                    else:
                        print("⚠️  Could not initialize database for CSV export")
                
                if args.export_json:
                    if orchestrator and hasattr(orchestrator, 'db'):
                        filepath = orchestrator.db.export_to_json()
                        print(f"✅ Exported to JSON: {filepath}")
                    else:
                        print("⚠️  Could not initialize database for JSON export")
                
                return 0
            except Exception as e:
                print(f"❌ Export failed: {e}")
                import traceback
                traceback.print_exc()
                return 1
        
        if args.cleanup:
            try:
                print(f"🗑️  Cleaning up jobs older than {args.cleanup} days...")
                orchestrator = None
                
                # Initialize orchestrator
                if hasattr(job_scraper, 'JobScraperOrchestrator'):
                    orchestrator = job_scraper.JobScraperOrchestrator()
                    if hasattr(orchestrator, 'initialize'):
                        orchestrator.initialize()
                elif hasattr(job_scraper, 'initialize'):
                    orchestrator = job_scraper.initialize()
                elif hasattr(job_scraper, 'orchestrator'):
                    orchestrator = job_scraper.orchestrator
                
                if orchestrator and hasattr(orchestrator, 'db'):
                    deleted = orchestrator.db.cleanup_old_jobs(args.cleanup)
                    print(f"✅ Cleaned up {deleted} old jobs")
                else:
                    print("⚠️  Could not initialize database for cleanup")
                
                return 0
            except Exception as e:
                print(f"❌ Cleanup failed: {e}")
                import traceback
                traceback.print_exc()
                return 1
        
        # Main scraping operations
        if args.run or args.continuous:
            try:
                print("🤖 Starting Job Scraper execution...")
                
                # Initialize orchestrator
                if hasattr(job_scraper, 'JobScraperOrchestrator'):
                    orchestrator = job_scraper.JobScraperOrchestrator()
                    orchestrator.initialize()
                    
                    stats = orchestrator.run_once()
                    
                    print(f"\n✅ Run complete!")
                    print(f"   📥 Total jobs found: {stats.total_jobs}")
                    print(f"   ⭐ New jobs saved: {stats.total_new}")
                    print(f"   📤 Jobs posted: {stats.jobs_posted}")
                    
                    if stats.linkedin_errors + stats.indeed_errors + stats.naukri_errors > 0:
                        print(f"   ⚠️  Errors: {stats.linkedin_errors + stats.indeed_errors + stats.naukri_errors}")
                    
                else:
                    print("⚠️  JobScraperOrchestrator not found in job_scraper module")
                    print("   Checking for legacy functions...")
                    
                    # Try legacy approach
                    if hasattr(job_scraper, 'initialize') and hasattr(job_scraper, 'run'):
                        print("   Using legacy initialize() and run() pattern...")
                        job_scraper.initialize()
                        job_scraper.run()
                    else:
                        print("❌ No compatible entry point found")
                        return 1
                
                # Handle continuous mode
                if args.continuous and hasattr(job_scraper, 'run_continuous'):
                    print(f"🔄 Entering continuous mode (every {job_scraper.CONFIG.get('schedule', {}).get('run_interval_hours', 6)} hours)...")
                    return job_scraper.run_continuous()
                
                return 0
            except Exception as e:
                print(f"❌ Runtime error: {e}")
                import traceback
                traceback.print_exc()
                return 1
        
        return 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This CLI requires job_scraper.py to be in the same directory")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())