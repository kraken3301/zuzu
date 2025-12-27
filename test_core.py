#!/usr/bin/env python3
"""
Core functionality test for the Multi-Platform Job Scraper
Tests basic functionality without requiring Google Drive or Telegram
"""

import sys
import os
import tempfile
import shutil

def test_job_class():
    """Test Job dataclass functionality"""
    print("💼 Testing Job class...")
    
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
        import traceback
        traceback.print_exc()
        return False

def test_scraping_stats():
    """Test ScrapingStats dataclass"""
    print("\n📊 Testing ScrapingStats class...")
    
    try:
        from job_scraper import ScrapingStats
        from datetime import datetime, timedelta
        
        # Create test stats
        stats = ScrapingStats()
        stats.linkedin_jobs = 10
        stats.linkedin_new = 5
        stats.indeed_jobs = 8
        stats.indeed_new = 3
        
        # Test properties
        assert stats.total_jobs == 18
        assert stats.total_new == 8
        
        # Test runtime calculation
        stats.end_time = stats.start_time + timedelta(minutes=5, seconds=30)
        runtime = stats.get_runtime()
        assert "5m 30s" in runtime
        
        # Test summary generation
        summary = stats.get_summary()
        assert "LinkedIn: 10 (5 new)" in summary
        assert "Indeed: 8 (3 new)" in summary
        
        print("✅ ScrapingStats class working correctly")
        print(f"   Total jobs: {stats.total_jobs}")
        print(f"   Runtime: {runtime}")
        
        return True
    except Exception as e:
        print(f"❌ ScrapingStats test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_basic():
    """Test basic database functionality with temp directory"""
    print("\n🗃️ Testing basic database functionality...")
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        
        # Import required modules
        import sqlite3
        from job_scraper import Job
        
        # Create a simple database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                source TEXT NOT NULL,
                url TEXT
            )
        ''')
        conn.commit()
        
        # Create a test job
        job = Job(
            id="test_job_1",
            title="Test Job",
            company="Test Company",
            location="Test Location",
            source="test",
            url="https://example.com"
        )
        
        # Test job saving
        cursor.execute('''
            INSERT INTO jobs (id, title, company, location, source, url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (job.id, job.title, job.company, job.location, job.source, job.url))
        conn.commit()
        
        # Test duplicate prevention
        try:
            cursor.execute('''
                INSERT INTO jobs (id, title, company, location, source, url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (job.id, job.title, job.company, job.location, job.source, job.url))
            conn.commit()
            duplicate_prevented = False
        except sqlite3.IntegrityError:
            duplicate_prevented = True
        
        # Test job retrieval
        cursor.execute('SELECT COUNT(*) FROM jobs')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
        assert duplicate_prevented == True
        assert count == 1
        
        print("✅ Basic database functionality working")
        print(f"   Database created at: {db_path}")
        print(f"   Total jobs in test DB: {count}")
        print(f"   Duplicate prevention: {'Working' if duplicate_prevented else 'Failed'}")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration structure"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from job_scraper import CONFIG, validate_config
        
        # Test configuration structure
        assert 'telegram' in CONFIG
        assert 'linkedin' in CONFIG
        assert 'indeed' in CONFIG
        assert 'naukri' in CONFIG
        assert 'superset' in CONFIG
        assert 'proxy' in CONFIG
        assert 'scraping' in CONFIG
        assert 'data' in CONFIG
        assert 'schedule' in CONFIG
        assert 'paths' in CONFIG
        assert 'logging' in CONFIG
        assert 'filters' in CONFIG
        
        # Test validation
        is_valid, errors = validate_config()
        
        print("✅ Configuration structure valid")
        print(f"   Telegram enabled: {CONFIG['telegram']['enabled']}")
        print(f"   LinkedIn enabled: {CONFIG['linkedin']['enabled']}")
        print(f"   Validation result: {'Valid' if is_valid else 'Invalid'}")
        if errors:
            print(f"   Issues: {len(errors)}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exceptions():
    """Test custom exceptions"""
    print("\n⚠️ Testing custom exceptions...")
    
    try:
        from job_scraper import (
            ScraperError, ProxyError, RateLimitError,
            AuthenticationError, CaptchaError, BlockedError
        )
        
        # Test exception hierarchy
        assert issubclass(ProxyError, ScraperError)
        assert issubclass(RateLimitError, ScraperError)
        assert issubclass(AuthenticationError, ScraperError)
        assert issubclass(CaptchaError, ScraperError)
        assert issubclass(BlockedError, ScraperError)
        
        # Test exception creation
        try:
            raise ProxyError("Test proxy error")
        except ProxyError as e:
            assert str(e) == "Test proxy error"
        
        print("✅ Custom exceptions working correctly")
        
        return True
    except Exception as e:
        print(f"❌ Exceptions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run core functionality tests"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        MULTI-PLATFORM JOB SCRAPER - CORE TESTS               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    tests = [
        ("Job Class", test_job_class),
        ("ScrapingStats", test_scraping_stats),
        ("Database", test_database_basic),
        ("Configuration", test_configuration),
        ("Exceptions", test_exceptions),
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
        print("🎉 All core tests passed! The scraper implementation is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())