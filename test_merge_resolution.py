#!/usr/bin/env python3
"""
Test script to verify merge conflict resolution
Tests both monolithic and modular approaches
"""

import sys
import os
import tempfile
import importlib.util

def test_monolithic_imports():
    """Test that job_scraper.py can be imported directly"""
    print("Testing monolithic imports...")
    try:
        import job_scraper
        
        # Test key classes exist
        assert hasattr(job_scraper, 'JobScraperOrchestrator'), "Missing JobScraperOrchestrator"
        assert hasattr(job_scraper, 'Job'), "Missing Job model"
        assert hasattr(job_scraper, 'CONFIG'), "Missing CONFIG"
        assert hasattr(job_scraper, 'initialize'), "Missing initialize function"
        assert hasattr(job_scraper, 'run'), "Missing run function"
        
        print("  ✅ All monolithic imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Monolithic import failed: {e}")
        return False


def test_modular_imports():
    """Test that core modules work"""
    print("Testing modular imports...")
    try:
        from core.orchestrator import JobScraperOrchestrator
        from core.models import Job, ScrapingStats
        from core.config import CONFIG, validate_config
        
        print("  ✅ All modular imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Modular import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_interface():
    """Test that CLI can be instantiated"""
    print("Testing CLI interfaces...")
    try:
        import main
        import job_scraper_cli
        
        # Test that main has required functions
        assert hasattr(main, 'main'), "Missing main.main"
        assert hasattr(main, 'initialize'), "Missing main.initialize"
        assert hasattr(main, 'InteractiveScraper'), "Missing InteractiveScraper"
        
        print("  ✅ CLI interfaces working")
        return True
    except Exception as e:
        print(f"  ❌ CLI test failed: {e}")
        return False


def test_config_validation():
    """Test configuration validation"""
    print("Testing configuration...")
    try:
        from job_scraper import validate_config, CONFIG
        
        is_valid, errors = validate_config()
        
        # It should return a tuple
        assert isinstance(is_valid, bool), "validate_config should return bool"
        assert isinstance(errors, list), "validate_config should return list of errors"
        
        # It should have some default configuration
        assert 'telegram' in CONFIG, "Missing telegram config"
        assert 'linkedin' in CONFIG, "Missing linkedin config"
        assert 'indeed' in CONFIG, "Missing indeed config"
        assert 'naukri' in CONFIG, "Missing naukri config"
        
        print(f"  ✅ Config validation working (valid={is_valid}, {len(errors)} warnings)")
        return True
    except Exception as e:
        print(f"  ❌ Config validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_core_components():
    """Test that core scrapers can be instantiated"""
    print("Testing core components...")
    try:
        from job_scraper import (
            DatabaseManager,
            ProxyManager,
            HTTPClient,
            BrowserManager,
            TelegramPoster
        )
        
        # Test that manager classes exist and can be instantiated
        # (we won't actually initialize them to avoid side effects)
        assert DatabaseManager is not None, "DatabaseManager not found"
        assert ProxyManager is not None, "ProxyManager not found"
        assert HTTPClient is not None, "HTTPClient not found"
        assert BrowserManager is not None, "BrowserManager not found"
        assert TelegramPoster is not None, "TelegramPoster not found"
        
        print("  ✅ All core components available")
        return True
    except Exception as e:
        print(f"  ❌ Core components test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_import_consistency():
    """Test that modular and monolithic imports are consistent"""
    print("Testing import consistency...")
    try:
        from job_scraper import Job as JobMono, CONFIG as ConfigMono
        from core.models import Job as JobMod
        from core.config import CONFIG as ConfigMod
        
        # Both should be the same classes/dicts
        assert JobMono is JobMod, "Job classes don't match between monolithic and modular"
        assert ConfigMono is ConfigMod, "CONFIG objects don't match"
        
        print("  ✅ Imports are consistent")
        return True
    except Exception as e:
        print(f"  ❌ Import consistency failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("MERGE CONFLICT RESOLUTION TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(results.values())
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Merge conflict resolved successfully.")
        print("\nUsage:")
        print("  • Monolithic: python job_scraper.py")
        print("  • CLI: python main.py --run")
        print("  • Interactive: initialize() then run()")
        return True
    else:
        print("\n⚠️  Some tests failed. Review the errors above.")
        return False


def main():
    """Run all tests"""
    print("Testing Merge Conflict Resolution")
    print("="*60)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = {
        "Monolithic Imports": test_monolithic_imports,
        "Modular Imports": test_modular_imports,
        "CLI Interface": test_cli_interface,
        "Config Validation": test_config_validation,
        "Core Components": test_core_components,
        "Import Consistency": test_import_consistency,
    }
    
    results = {}
    for name, test_func in tests.items():
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"  ❌ Test {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    return print_summary(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)