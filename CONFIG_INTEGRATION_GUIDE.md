# Config.py Integration & Telegram Async Fix Guide

## Overview

This guide documents the recent updates to the job scraper that integrate `config.py` for easier configuration management and fix Telegram async issues with python-telegram-bot v20+.

## Changes Made

### 1. Enhanced config.py

The `config.py` file now includes comprehensive India-focused job search configuration:

#### LinkedIn Configuration
- **30 keywords** covering:
  - IT & Tech (software engineer, python, java, data analyst, devops, cloud, etc.)
  - Management & Business (business analyst, management trainee, digital marketing, etc.)
  - Core Engineering (mechanical, civil, electrical, electronics, etc.)
  - Finance & Creative (accountant, content writer, graphic designer, UI/UX, etc.)
- **20 locations** including all metro cities and major tier-2 cities

#### Indeed Configuration
- **62 keywords** covering:
  - IT & Software roles
  - Business & Operations
  - Content & Creative
  - Finance & Accounts
  - Operations & Logistics
- **23 locations** with state names for better search accuracy

#### Naukri Configuration
- **30+ keywords** including:
  - IT & Technology
  - Business & Management
  - Core Engineering
  - Finance & Banking
  - Training programs (B.Tech, MBA, MCA, etc.)
  - Other sectors (pharma, biotech, chemical, etc.)
- **30 locations** in lowercase format for Naukri API compatibility

#### Enhanced Filters
- Expanded EXCLUDE_TITLE_KEYWORDS with 21 patterns to filter out senior/experienced roles
- Includes year ranges like "5+ years", "7-10 years", etc.
- Filters roles like "team lead", "tech lead", "engineering manager"

### 2. Job_scraper.py Integration

Added automatic config.py import and override logic (lines 382-484):

```python
try:
    import config
    # Override all CONFIG dictionary values with config.py values
    # Telegram, LinkedIn, Indeed, Naukri, Superset, Proxy, Filters, Schedule, Data
    print("✅ Configuration loaded from config.py")
except ImportError:
    print("⚠️ config.py not found, using default CONFIG values")
```

The system now:
- Attempts to import config.py automatically
- Overrides CONFIG dictionary values with config.py values
- Falls back to default values if config.py is not found
- Displays what was loaded on startup

### 3. Telegram Async Fixes

Fixed all Telegram bot method calls to work with python-telegram-bot v20+ (async):

#### Fixed Methods:
1. **post_job()** (line 2709):
   - Wrapped `bot.send_message()` with `self._run_async()`
   - Changed parse mode from `MARKDOWN` to `MARKDOWN_V2` for proper escaping
   - Fixed fallback to also use `_run_async()`

2. **send_summary()** (line 2769):
   - Wrapped `bot.send_message()` with `self._run_async()`

3. **send_error()** (line 2784):
   - Wrapped `bot.send_message()` with `self._run_async()`

4. **Job.to_telegram_message()** (line 562):
   - Fixed URL formatting in Apply link: `[Apply Now]({self.url})`
   - Properly escaped hashtags: `\\#{self.source} \\#jobs \\#fresher`
   - All special characters already properly escaped for MarkdownV2

## Configuration Setup

### Quick Start

1. **Edit config.py** with your credentials:

```python
# In config.py
TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # From @BotFather
TELEGRAM_CHANNEL_ID = "@YourChannelUsername"  # Your channel

# Optional: Adjust proxy settings for your environment
PROXY_ENABLED = False  # Set to False for PythonAnywhere/Replit
```

2. **Run the scraper:**

```python
from job_scraper import initialize, run
initialize()
run()
```

### Customizing Keywords

You can easily customize job search keywords in `config.py`:

```python
# Add your own keywords
LINKEDIN_KEYWORDS = [
    'your custom keyword',
    'another keyword',
] + LINKEDIN_KEYWORDS  # Keep existing ones

# Or completely replace
LINKEDIN_KEYWORDS = [
    'only these keywords',
    'will be used',
]
```

### Customizing Locations

```python
# Focus on specific cities
LINKEDIN_LOCATIONS = [
    'Bangalore',
    'Mumbai',
    'Remote',
]

# Or keep all locations (recommended for maximum coverage)
```

## Testing Your Configuration

Run the test script to verify everything is working:

```bash
python test_config_integration.py
```

This will check:
- config.py is properly loaded
- All keywords and locations are imported
- Telegram message escaping works correctly
- Configuration values are properly set

## Proxy Configuration

### For PythonAnywhere / Replit / Cloud Platforms

Set in `config.py`:

```python
PROXY_ENABLED = False
PROXY_USE_FREE = False
```

### For Local Machine

You can enable proxies:

```python
PROXY_ENABLED = True
PROXY_USE_FREE = True  # Use free proxies
# Or add custom proxies
PROXY_CUSTOM = [
    'http://user:pass@ip:port',
    'socks5://user:pass@ip:port',
]
```

## Troubleshooting

### Issue: "coroutine was never awaited" error

**Cause:** Using python-telegram-bot v20+ without async wrappers

**Solution:** Already fixed! All `bot.send_message()` calls are now wrapped with `self._run_async()`

### Issue: "Can't parse entities" or formatting errors

**Cause:** Special characters not properly escaped for MarkdownV2

**Solution:** Already fixed! The `Job._escape_md()` method escapes all special characters and hashtags are properly escaped with `\\#`

### Issue: Config.py not loading

**Cause:** ImportError or syntax error in config.py

**Solution:**
1. Check config.py for syntax errors
2. Make sure config.py is in the same directory as job_scraper.py
3. Check the console output - it will show if config.py loaded

### Issue: No jobs found

**Possible causes:**
1. Proxy issues (disable if on cloud platform)
2. LinkedIn/Indeed blocking your IP (use proxy or VPN)
3. Keywords too specific (broaden your search)
4. Filters too restrictive (check EXCLUDE_TITLE_KEYWORDS)

**Solutions:**
```python
# In config.py, temporarily disable strict filtering
EXCLUDE_TITLE_KEYWORDS = ['senior', 'lead', 'manager']  # Keep only essential ones
MAX_EXPERIENCE_YEARS = 5  # Increase from 2 to 5
```

## Benefits of This Integration

1. **Easy Configuration**: Edit one file (config.py) instead of searching through 3000+ lines of job_scraper.py
2. **Comprehensive Coverage**: 100+ keywords across all job categories
3. **India-Focused**: Optimized for Indian job market with proper location formatting
4. **No Async Errors**: All Telegram methods properly wrapped for v20+
5. **Proper Formatting**: Messages display correctly with MarkdownV2
6. **Flexible**: Falls back to defaults if config.py is missing

## Files Modified

1. **config.py**: Expanded with comprehensive Indian job search configuration
2. **job_scraper.py**: 
   - Added config.py import and override logic (after line 380)
   - Fixed TelegramPoster methods for async (lines 2709, 2769, 2784)
   - Fixed Job message formatting (line 591-593)
3. **test_config_integration.py**: New test script to verify integration

## Next Steps

1. Update `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` in config.py
2. Adjust keywords and locations if needed
3. Set `PROXY_ENABLED = False` if running on cloud platform
4. Run `python test_config_integration.py` to verify setup
5. Run your scraper: `python -c "from job_scraper import initialize, run; initialize(); run()"`

## Support

If you encounter any issues:
1. Check the console output for error messages
2. Run the test script to diagnose configuration issues
3. Verify your Telegram credentials are correct
4. Check that all required packages are installed (see requirements.txt)

---

**Note**: This integration maintains backward compatibility. If config.py is not present, the scraper will use the default values hardcoded in job_scraper.py.
