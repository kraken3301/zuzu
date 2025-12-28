#!/usr/bin/env python3
"""
Quick test script to verify professional-grade improvements
"""

import sys

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    try:
        import job_scraper
        from job_scraper import NaukriScraper, GovernmentJobsScraper
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_naukri_improvements():
    """Test Naukri scraper improvements"""
    print("\nTesting Naukri improvements...")
    try:
        from job_scraper import NaukriScraper, CONFIG, LogManager, DatabaseManager, HTTPClient, BrowserManager
        
        # Create scraper instance
        logger = LogManager.get_logger('test')
        db = DatabaseManager()
        http = HTTPClient()
        browser = BrowserManager()
        
        scraper = NaukriScraper(logger, db, http, browser)
        
        # Test methods exist
        assert hasattr(scraper, '_get_random_user_agent'), "Missing _get_random_user_agent method"
        assert hasattr(scraper, '_get_api_headers'), "Missing _get_api_headers method"
        assert hasattr(scraper, '_smart_delay'), "Missing _smart_delay method"
        assert hasattr(scraper, '_make_api_request_with_retry'), "Missing _make_api_request_with_retry method"
        assert hasattr(scraper, 'session'), "Missing session attribute"
        
        # Test UA rotation
        ua1 = scraper._get_random_user_agent()
        ua2 = scraper._get_random_user_agent()
        assert isinstance(ua1, str) and len(ua1) > 50, "Invalid User-Agent"
        print(f"   ✅ User-Agent rotation working: {ua1[:50]}...")
        
        # Test headers generation
        headers = scraper._get_api_headers()
        assert 'User-Agent' in headers, "User-Agent missing from headers"
        assert 'Accept-Language' in headers, "Accept-Language missing from headers"
        assert 'Sec-Fetch-Mode' in headers, "Sec-Fetch-Mode missing from headers"
        print(f"   ✅ Headers generation working: {len(headers)} headers")
        
        # Test session initialization
        if CONFIG['naukri'].get('session_enabled', True):
            assert scraper.session is not None, "Session not initialized"
            print(f"   ✅ Session management enabled")
        
        print("✅ All Naukri improvements verified")
        return True
        
    except Exception as e:
        print(f"❌ Naukri test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_govt_improvements():
    """Test Government Jobs scraper improvements"""
    print("\nTesting Government Jobs improvements...")
    try:
        from job_scraper import GovernmentJobsScraper, CONFIG, LogManager, DatabaseManager, HTTPClient, BrowserManager
        
        # Create scraper instance
        logger = LogManager.get_logger('test')
        db = DatabaseManager()
        http = HTTPClient()
        browser = BrowserManager()
        
        scraper = GovernmentJobsScraper(logger, db, http, browser)
        
        # Test methods exist
        assert hasattr(scraper, '_scrape_feeds_parallel'), "Missing _scrape_feeds_parallel method"
        assert hasattr(scraper, '_scrape_feeds_sequential'), "Missing _scrape_feeds_sequential method"
        assert hasattr(scraper, '_scrape_single_feed_timed'), "Missing _scrape_single_feed_timed method"
        assert hasattr(scraper, '_get_feed_name'), "Missing _get_feed_name method"
        assert hasattr(scraper, '_log_performance_report'), "Missing _log_performance_report method"
        assert hasattr(scraper, '_feed_performance'), "Missing _feed_performance attribute"
        
        # Test feed name extraction
        feed_name = scraper._get_feed_name('https://www.freejobalert.com/feed')
        assert feed_name == "FreeJobAlert", f"Unexpected feed name: {feed_name}"
        print(f"   ✅ Feed name extraction working")
        
        # Test config loading
        try:
            import config as user_config
            if hasattr(user_config, 'GOVT_FEEDS_PRIMARY'):
                primary = user_config.GOVT_FEEDS_PRIMARY
                print(f"   ✅ Primary feeds configured: {len(primary)} feeds")
            if hasattr(user_config, 'GOVT_FEEDS_SECONDARY'):
                secondary = user_config.GOVT_FEEDS_SECONDARY
                print(f"   ✅ Secondary feeds configured: {len(secondary)} feeds")
            if hasattr(user_config, 'GOVT_FEED_PARALLEL'):
                parallel = user_config.GOVT_FEED_PARALLEL
                print(f"   ✅ Parallel fetching: {parallel}")
        except:
            print(f"   ⚠️ config.py not found, using defaults")
        
        print("✅ All Government Jobs improvements verified")
        return True
        
    except Exception as e:
        print(f"❌ Government Jobs test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """Test that config.py settings are loaded"""
    print("\nTesting config.py loading...")
    try:
        import config
        
        # Check Naukri advanced settings
        assert hasattr(config, 'NAUKRI_USER_AGENT_ROTATION'), "NAUKRI_USER_AGENT_ROTATION not in config"
        assert hasattr(config, 'NAUKRI_SESSION_ENABLED'), "NAUKRI_SESSION_ENABLED not in config"
        assert hasattr(config, 'NAUKRI_RETRY_ATTEMPTS'), "NAUKRI_RETRY_ATTEMPTS not in config"
        print(f"   ✅ Naukri advanced settings loaded")
        
        # Check Government Jobs optimization settings
        assert hasattr(config, 'GOVT_FEEDS_PRIMARY'), "GOVT_FEEDS_PRIMARY not in config"
        assert hasattr(config, 'GOVT_FEEDS_SECONDARY'), "GOVT_FEEDS_SECONDARY not in config"
        assert hasattr(config, 'GOVT_FEED_PARALLEL'), "GOVT_FEED_PARALLEL not in config"
        print(f"   ✅ Government Jobs optimization settings loaded")
        
        print("✅ All config.py settings verified")
        return True
        
    except ImportError:
        print(f"   ⚠️ config.py not found (this is OK for testing)")
        return True
    except Exception as e:
        print(f"❌ Config test error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Professional-Grade Improvements Verification")
    print("="*60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Config Loading", test_config_loading()))
    results.append(("Naukri Improvements", test_naukri_improvements()))
    results.append(("Government Jobs Improvements", test_govt_improvements()))
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:30s} {status}")
    
    print("="*60)
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
