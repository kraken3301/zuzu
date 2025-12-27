#!/usr/bin/env python3
"""
Basic functionality test for the Multi-Platform Job Scraper
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test core imports
        from job_scraper import (
            Job, ScrapingStats, DatabaseManager, ProxyManager,
            HTTPClient, BrowserManager, LinkedInScraper,
            IndeedScraper, NaukriScraper, SupersetScraper,
            TelegramPoster, JobScraperOrchestrator
        )
        print("✅ All core classes imported successfully")
        
        # Test utility functions
        from job_scraper import (
            initialize, run, show_stats, search_jobs,
            test_linkedin, test_indeed, test_naukri
        )
        print("✅ All utility functions imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False

def test_config():
    """Test configuration validation"""
    print("\n📋 Testing configuration...")
    
    try:
        from job_scraper import CONFIG, validate_config
        
        is_valid, errors = validate_config()
        
        if is_valid:
            print("✅ Configuration is valid")
            print(f"   Telegram enabled: {CONFIG['telegram']['enabled']}")
            print(f"   LinkedIn enabled: {CONFIG['linkedin']['enabled']}")
            print(f"   Indeed enabled: {CONFIG['indeed']['enabled']}")
            print(f"   Naukri enabled: {CONFIG['naukri']['enabled']}")
            print(f"   Superset enabled: {CONFIG['superset']['enabled']}")
        else:
            print("⚠️  Configuration has issues:")
            for error in errors:
                print(f"   - {error}")
        
        return is_valid
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n🗃️ Testing database...")

    try:
        from job_scraper import DatabaseManager, setup_environment

        # Setup environment first to create directories
        setup_environment()

        db = DatabaseManager()
        stats = db.get_stats()

        print("✅ Database initialized successfully")
        print(f"   Total jobs: {stats['total_jobs']}")
        print(f"   Unposted jobs: {stats['unposted']}")

        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_job_class():
    """Test Job dataclass functionality"""
    print("\n💼 Testing Job class...")
    
    try:
        from job_scraper import Job
        
        # Create a test job
        job = Job(
            id="test123",
            title="Software Engineer",
            company="Test Company",
            location="Bangalore",
            source="test",
            url="https://example.com/job",
            experience="0-2 years",
            salary="5-10 LPA",
            skills=["Python", "JavaScript", "SQL"],
            keyword_matched="python"
        )
        
        # Test job properties
        assert job.id == "test123"
        assert job.title == "Software Engineer"
        assert job.company == "Test Company"
        assert len(job.skills) == 3
        
        # Test ID generation
        test_id = Job.generate_id("Software Engineer", "Test Company", "test")
        assert len(test_id) == 16
        
        # Test Telegram message formatting
        message = job.to_telegram_message()
        assert "🚨 NEW JOB ALERT" in message
        assert "Software Engineer" in message
        assert "Test Company" in message
        
        print("✅ Job class working correctly")
        print(f"   Generated ID: {test_id}")
        print(f"   Telegram message preview: {message[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Job class test failed: {e}")
        return False

def test_logging():
    """Test logging setup"""
    print("\n📝 Testing logging...")

    try:
        from job_scraper import LogManager, setup_environment

        # Setup environment first to create directories
        setup_environment()

        log_manager = LogManager()
        log_manager.setup()

        logger = LogManager.get_logger("TestLogger")
        logger.info("This is a test log message")

        print("✅ Logging setup successful")
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        MULTI-PLATFORM JOB SCRAPER - BASIC TESTS               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Job Class", test_job_class),
        ("Logging", test_logging),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed! The scraper is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())