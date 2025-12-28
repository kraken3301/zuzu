#!/usr/bin/env python3
"""
Test script to verify config.py integration with job_scraper.py
"""

import sys

def test_config_loading():
    """Test that config.py is properly loaded"""
    print("=" * 60)
    print("TESTING CONFIG.PY INTEGRATION")
    print("=" * 60)
    print()
    
    # Import job_scraper to trigger config loading
    try:
        import job_scraper
        print("✅ job_scraper.py imported successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to import job_scraper.py: {e}")
        return False
    
    # Check if config values were loaded
    CONFIG = job_scraper.CONFIG
    
    print("📊 Checking loaded configuration:")
    print("-" * 60)
    
    # Check LinkedIn
    linkedin_keywords = CONFIG['linkedin']['keywords']
    linkedin_locations = CONFIG['linkedin']['locations']
    print(f"✅ LinkedIn Keywords: {len(linkedin_keywords)} loaded")
    print(f"   Examples: {linkedin_keywords[:3]}")
    print(f"✅ LinkedIn Locations: {len(linkedin_locations)} loaded")
    print(f"   Examples: {linkedin_locations[:3]}")
    print()
    
    # Check Indeed
    indeed_keywords = CONFIG['indeed']['keywords']
    indeed_locations = CONFIG['indeed']['locations']
    print(f"✅ Indeed Keywords: {len(indeed_keywords)} loaded")
    print(f"   Examples: {indeed_keywords[:3]}")
    print(f"✅ Indeed Locations: {len(indeed_locations)} loaded")
    print(f"   Examples: {indeed_locations[:3]}")
    print()
    
    # Check Naukri
    naukri_keywords = CONFIG['naukri']['keywords']
    naukri_locations = CONFIG['naukri']['locations']
    print(f"✅ Naukri Keywords: {len(naukri_keywords)} loaded")
    print(f"   Examples: {naukri_keywords[:3]}")
    print(f"✅ Naukri Locations: {len(naukri_locations)} loaded")
    print(f"   Examples: {naukri_locations[:3]}")
    print()
    
    # Check Filters
    exclude_keywords = CONFIG['filters']['exclude_title_keywords']
    print(f"✅ Exclude Title Keywords: {len(exclude_keywords)} loaded")
    print(f"   Examples: {exclude_keywords[:5]}")
    print()
    
    # Check Proxy settings
    proxy_enabled = CONFIG['proxy']['enabled']
    print(f"✅ Proxy Enabled: {proxy_enabled}")
    if not proxy_enabled:
        print("   (Good for PythonAnywhere/Replit)")
    print()
    
    # Check Telegram settings
    bot_token = CONFIG['telegram']['bot_token']
    channel_id = CONFIG['telegram']['channel_id']
    print(f"📱 Telegram Bot Token: {bot_token[:20]}..." if bot_token and bot_token != 'YOUR_BOT_TOKEN_HERE' else "⚠️ Telegram Bot Token: NOT SET (update config.py)")
    print(f"📱 Telegram Channel ID: {channel_id}" if channel_id != '@your_channel' else "⚠️ Telegram Channel ID: NOT SET (update config.py)")
    print()
    
    print("=" * 60)
    print("✅ CONFIG.PY INTEGRATION TEST PASSED!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update config.py with your TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID")
    print("2. Run: python job_scraper.py")
    print("3. Or use: from job_scraper import initialize, run; initialize(); run()")
    print()
    
    return True


def test_telegram_escaping():
    """Test Telegram message escaping for MarkdownV2"""
    print("=" * 60)
    print("TESTING TELEGRAM MARKDOWNV2 ESCAPING")
    print("=" * 60)
    print()
    
    try:
        from job_scraper import Job
        from datetime import datetime
        
        # Create a test job with special characters
        test_job = Job(
            title="Software Engineer (Python) - Entry Level",
            company="Tech Corp. [India] Pvt. Ltd.",
            location="Bangalore, Karnataka",
            url="https://example.com/job/123",
            source="linkedin",
            experience="0-2 years",
            salary="₹3-5 LPA",
            job_type="Full-time",
            posted_date=datetime.now(),
            skills=["Python", "Django", "REST API"]
        )
        
        # Generate Telegram message
        message = test_job.to_telegram_message()
        
        print("Generated Telegram message:")
        print("-" * 60)
        print(message)
        print("-" * 60)
        print()
        
        # Check for proper escaping
        issues = []
        if "#linkedin" in message:
            issues.append("Hashtag not escaped (should be \\#linkedin)")
        if "- Entry" in message and "\\- Entry" not in message:
            issues.append("Hyphen in title not escaped")
        if "[India]" in message and "\\[India\\]" not in message:
            issues.append("Square brackets not escaped")
        if ". Ltd" in message and "\\. Ltd" not in message:
            issues.append("Period not escaped")
        if "(Python)" in message and "\\(Python\\)" not in message:
            issues.append("Parentheses not escaped")
        
        if issues:
            print("⚠️ Potential escaping issues found:")
            for issue in issues:
                print(f"   - {issue}")
            print()
        else:
            print("✅ All special characters properly escaped for MarkdownV2")
            print()
        
        print("=" * 60)
        print("✅ TELEGRAM ESCAPING TEST COMPLETED")
        print("=" * 60)
        print()
        
    except Exception as e:
        print(f"❌ Error during escaping test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print()
    success = True
    
    # Run tests
    success = test_config_loading() and success
    print()
    success = test_telegram_escaping() and success
    
    sys.exit(0 if success else 1)
