#!/usr/bin/env python3
"""
Example usage of the Multi-Platform Job Scraper Bot

This script demonstrates how to use the job scraper in different scenarios.
"""

from job_scraper import (
    initialize, run, run_continuous, keep_alive,
    test_linkedin, test_indeed, test_naukri, test_telegram,
    show_stats, show_recent_jobs, search_jobs, export_all,
    cleanup, shutdown
)

def example_single_run():
    """Example: Run a single scraping cycle"""
    print("🚀 Running single scraping cycle...")
    
    # Initialize the scraper
    if initialize():
        # Run the scraper
        stats = run()
        
        # Show results
        print(f"\n✅ Scraping complete!")
        print(f"   Found {stats.total_jobs} total jobs")
        print(f"   {stats.total_new} new jobs saved")
        print(f"   {stats.jobs_posted} jobs posted to Telegram")
        
        # Show recent jobs
        show_recent_jobs(5)
        
        # Show statistics
        show_stats()

def example_test_scrapers():
    """Example: Test individual scrapers"""
    print("🧪 Testing individual scrapers...")
    
    if initialize():
        print("\n1️⃣ Testing LinkedIn scraper...")
        linkedin_jobs = test_linkedin()
        print(f"   Found {len(linkedin_jobs)} LinkedIn jobs")
        
        print("\n2️⃣ Testing Indeed scraper...")
        indeed_jobs = test_indeed()
        print(f"   Found {len(indeed_jobs)} Indeed jobs")
        
        print("\n3️⃣ Testing Naukri scraper...")
        naukri_jobs = test_naukri()
        print(f"   Found {len(naukri_jobs)} Naukri jobs")
        
        print("\n4️⃣ Testing Telegram connection...")
        test_telegram()

def example_database_operations():
    """Example: Database operations"""
    print("🗃️ Database operations...")
    
    if initialize():
        # Show statistics
        print("\n📊 Database Statistics:")
        show_stats()
        
        # Search jobs
        print("\n🔍 Searching for Python jobs...")
        python_jobs = search_jobs("Python")
        print(f"   Found {len(python_jobs)} Python jobs")
        
        # Show recent jobs
        print("\n📋 Recent unposted jobs:")
        show_recent_jobs(3)
        
        # Export data
        print("\n📤 Exporting data...")
        export_all()
        
        # Cleanup old jobs
        print("\n🗑️ Cleaning up old jobs...")
        cleanup(30)

def example_continuous_mode():
    """Example: Run in continuous mode (for long-running sessions)"""
    print("🔄 Running in continuous mode...")
    print("   This will run every 6 hours until stopped")
    print("   Press Ctrl+C to stop")
    
    if initialize():
        # Enable keep-alive for Colab
        keep_alive()
        
        # Run continuously
        try:
            run_continuous()
        except KeyboardInterrupt:
            print("\n⏹️  Stopped by user")
            shutdown()

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        MULTI-PLATFORM JOB SCRAPER - EXAMPLE USAGE              ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("Select an example to run:")
    print("1. Single scraping run")
    print("2. Test individual scrapers")
    print("3. Database operations")
    print("4. Continuous mode (long-running)")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        example_single_run()
    elif choice == "2":
        example_test_scrapers()
    elif choice == "3":
        example_database_operations()
    elif choice == "4":
        example_continuous_mode()
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")
    
    # Clean shutdown
    shutdown()