#!/usr/bin/env python3
"""
Test script to verify the refactoring improvements
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("🧪 Testing imports...")
    
    try:
        # Core modules
        from core.models import Job, ScrapingStats
        from core.config import CONFIG, load_config
        from core.log_manager import LogManager
        from core.database_manager import DatabaseManager
        from core.proxy_manager import ProxyManager
        from core.http_client import HTTPClient
        from core.browser_manager import BrowserManager
        from core.telegram_poster import TelegramPoster
        from core.orchestrator import JobScraperOrchestrator
        
        # Scrapers
        from scrapers.base_scraper import BaseScraper
        from scrapers.linkedin_scraper import LinkedInScraper
        from scrapers.indeed_scraper import IndeedScraper
        from scrapers.naukri_scraper import NaukriScraper
        from scrapers.superset_scraper import SupersetScraper
        
        # Utilities
        from utils.helpers import get_random_user_agent, clean_text
        
        print("✅ All imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_telegram_async_fix():
    """Test the Telegram async event loop fix"""
    print("🧪 Testing Telegram async fix...")
    
    try:
        from core.telegram_poster import TelegramPoster
        
        # Create poster (will fail connection but that's expected)
        poster = TelegramPoster()
        
        # Test that the _run_async method exists and has the fix
        assert hasattr(poster, '_run_async'), "_run_async method missing"
        
        # Check that the method handles event loop detection
        import inspect
        source = inspect.getsource(poster._run_async)
        assert 'get_running_loop' in source, "Event loop detection not implemented"
        assert 'create_task' in source, "create_task fallback not implemented"
        
        print("✅ Telegram async fix verified")
        return True
        
    except Exception as e:
        print(f"❌ Telegram async test failed: {e}")
        return False

def test_proxy_improvements():
    """Test proxy management improvements"""
    print("🧪 Testing proxy improvements...")
    
    try:
        from core.proxy_manager import ProxyManager
        
        # Create proxy manager
        manager = ProxyManager()
        
        # Test that domain-specific methods exist
        assert hasattr(manager, 'should_retry_without_proxy'), "should_retry_without_proxy missing"
        assert hasattr(manager, 'get_proxy_for_domain'), "get_proxy_for_domain missing"
        
        # Test that the methods are properly implemented
        import inspect
        
        # Check should_retry_without_proxy implementation
        retry_source = inspect.getsource(manager.should_retry_without_proxy)
        assert 'domain_blacklist' in retry_source, "Domain blacklist not used in retry logic"
        
        # Check get_proxy_for_domain implementation  
        proxy_source = inspect.getsource(manager.get_proxy_for_domain)
        assert 'domain_blacklist' in proxy_source, "Domain blacklist not used in proxy selection"
        
        print("✅ Proxy improvements verified")
        return True
        
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
        return False

def test_linkedin_selector_flexibility():
    """Test LinkedIn scraper selector flexibility"""
    print("🧪 Testing LinkedIn selector flexibility...")
    
    try:
        from scrapers.linkedin_scraper import LinkedInScraper
        
        # Check that flexible selectors are defined
        assert hasattr(LinkedInScraper, 'CARD_SELECTORS'), "CARD_SELECTORS missing"
        assert hasattr(LinkedInScraper, 'TITLE_SELECTORS'), "TITLE_SELECTORS missing"
        assert hasattr(LinkedInScraper, 'COMPANY_SELECTORS'), "COMPANY_SELECTORS missing"
        assert hasattr(LinkedInScraper, 'LOCATION_SELECTORS'), "LOCATION_SELECTORS missing"
        
        # Check that multiple selectors are provided for flexibility
        assert len(LinkedInScraper.CARD_SELECTORS) > 1, "Not enough card selectors"
        assert len(LinkedInScraper.TITLE_SELECTORS) > 1, "Not enough title selectors"
        assert len(LinkedInScraper.COMPANY_SELECTORS) > 1, "Not enough company selectors"
        
        # Check that methods use flexible selectors
        import inspect
        find_cards_source = inspect.getsource(LinkedInScraper._find_job_cards)
        assert 'CARD_SELECTORS' in find_cards_source, "Flexible selectors not used in _find_job_cards"
        
        print("✅ LinkedIn selector flexibility verified")
        return True
        
    except Exception as e:
        print(f"❌ LinkedIn selector test failed: {e}")
        return False

def test_superset_login_improvements():
    """Test Superset scraper login improvements"""
    print("🧪 Testing Superset login improvements...")
    
    try:
        from scrapers.superset_scraper import SupersetScraper
        
        # Check that specific selectors are used
        import inspect
        login_source = inspect.getsource(SupersetScraper._login)
        
        # Should use multiple specific selectors for email input
        email_selectors = [
            'input[type="email"][name="email"]',
            'input[type="email"][id="email"]',
            'input[type="email"][placeholder*="email"]'
        ]
        
        for selector in email_selectors:
            assert selector in login_source, f"Specific email selector {selector} not found"
        
        # Should use multiple specific selectors for password input
        password_selectors = [
            'input[type="password"][name="password"]',
            'input[type="password"][id="password"]',
            'input[type="password"][placeholder*="password"]'
        ]
        
        for selector in password_selectors:
            assert selector in login_source, f"Specific password selector {selector} not found"
        
        print("✅ Superset login improvements verified")
        return True
        
    except Exception as e:
        print(f"❌ Superset login test failed: {e}")
        return False

def test_modular_structure():
    """Test that the modular structure is properly organized"""
    print("🧪 Testing modular structure...")
    
    try:
        # Check that directories exist
        assert os.path.exists('core'), "core directory missing"
        assert os.path.exists('scrapers'), "scrapers directory missing"
        assert os.path.exists('utils'), "utils directory missing"
        
        # Check that main files exist
        assert os.path.exists('main.py'), "main.py missing"
        assert os.path.exists('job_scraper.py'), "job_scraper.py missing"
        
        # Check core files
        core_files = [
            'core/models.py',
            'core/config.py', 
            'core/log_manager.py',
            'core/database_manager.py',
            'core/proxy_manager.py',
            'core/http_client.py',
            'core/browser_manager.py',
            'core/telegram_poster.py',
            'core/orchestrator.py'
        ]
        
        for file in core_files:
            assert os.path.exists(file), f"{file} missing"
        
        # Check scraper files
        scraper_files = [
            'scrapers/base_scraper.py',
            'scrapers/linkedin_scraper.py',
            'scrapers/indeed_scraper.py',
            'scrapers/naukri_scraper.py',
            'scrapers/superset_scraper.py'
        ]
        
        for file in scraper_files:
            assert os.path.exists(file), f"{file} missing"
        
        print("✅ Modular structure verified")
        return True
        
    except Exception as e:
        print(f"❌ Modular structure test failed: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with original structure"""
    print("🧪 Testing backward compatibility...")
    
    try:
        # Test that original job_scraper.py can be imported
        import job_scraper
        
        # Test that compatibility functions exist
        assert hasattr(job_scraper, 'initialize'), "initialize function missing"
        assert hasattr(job_scraper, 'run'), "run function missing"
        assert hasattr(job_scraper, 'run_continuous'), "run_continuous function missing"
        
        print("✅ Backward compatibility verified")
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running refactoring verification tests...\n")
    
    tests = [
        test_imports,
        test_telegram_async_fix,
        test_proxy_improvements,
        test_linkedin_selector_flexibility,
        test_superset_login_improvements,
        test_modular_structure,
        test_backward_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring successful!")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)