# Fresher-Only & India-Only Mode - Feature Documentation

## Overview
New filtering features added to ensure only India-focused fresher/entry-level jobs (0-2 years experience) are scraped and posted to Telegram.

## What's New

### 1. FRESHER_ONLY_MODE (config.py)
When enabled, applies strict filtering to ensure only fresher/entry-level jobs are returned.

**Location:** `config.py` line 134

```python
FRESHER_ONLY_MODE = True  # Set to True to enable strict fresher-only filtering
```

**Filtering Logic:**
- ✅ Filters out jobs requiring 3+ years of experience
- ✅ Excludes job titles containing: 'experienced', 'expert', 'professional', 'specialist'
- ✅ Blocks experience patterns: "3+ years", "4-5 years", "5 years", etc.
- ✅ Uses regex pattern matching for robust detection
- ✅ Applies to both experience field AND job title

**Example Patterns Blocked:**
- "3-5 years experience"
- "4+ years in software development"
- "Experienced Software Engineer"
- "Expert Python Developer"

### 2. INDIA_ONLY_MODE (config.py)
When enabled, filters out all non-India location jobs.

**Location:** `config.py` line 135

```python
INDIA_ONLY_MODE = True  # Set to True to filter out non-India locations
```

**Filtering Logic:**
- ✅ Includes 50+ Indian cities (metros + Tier-2)
- ✅ Includes all major Indian states
- ✅ Supports "Remote India" and "Work from Home India"
- ✅ Excludes international locations: USA, UK, Canada, Singapore, Dubai, Germany, France, etc.

**Supported Indian Locations:**
- **Metros:** Delhi, Mumbai, Bangalore/Bengaluru, Hyderabad, Pune, Chennai, Kolkata
- **NCR:** Gurgaon/Gurugram, Noida, Ghaziabad, Faridabad
- **Tier-2:** Chandigarh, Jaipur, Kochi, Coimbatore, Lucknow, Indore, Nagpur, Surat, Visakhapatnam, Bhubaneswar, Mysore, Vadodara, and many more
- **States:** Maharashtra, Karnataka, Tamil Nadu, Telangana, Kerala, Gujarat, Rajasthan, Uttar Pradesh, West Bengal, Haryana, etc.

### 3. Experience Field Always Shown in Telegram Messages
All job alerts now prominently display the experience requirement.

**Before:**
```
🚨 NEW JOB ALERT 🔗
💼 Software Engineer - Fresher
🏢 TCS
📍 Bangalore, Karnataka
💰 ₹3-5 LPA
```

**After:**
```
🚨 NEW JOB ALERT 🔗
💼 Software Engineer - Fresher
🏢 TCS
📍 Bangalore, Karnataka
⭐ Experience: Fresher / 0-2 Years  ← ALWAYS SHOWN
💰 ₹3-5 LPA
```

**Display Logic:**
- If job has experience field: Shows actual value (e.g., "0-2 years", "1 year")
- If job has NO experience field: Shows default "Fresher / 0-2 Years"
- Field is ALWAYS displayed with ⭐ icon for prominence
- Formatted in bold: `⭐ *Experience*: ...`

### 4. Updated Telegram Hashtags
Job alerts now include #india hashtag:

```
#linkedin #jobs #fresher #india
```

## Configuration

### config.py Settings

```python
# --- FRESHER ONLY MODE (India-focused) ---
# When enabled, applies stricter filtering for fresher/entry-level jobs only
FRESHER_ONLY_MODE = True  # Set to True to enable strict fresher-only filtering
INDIA_ONLY_MODE = True     # Set to True to filter out non-India locations

# Maximum experience threshold (used alongside FRESHER_ONLY_MODE)
MAX_EXPERIENCE_YEARS = 2  # Maximum years of experience for "fresher" jobs
```

### How Settings Are Loaded

1. Settings defined in `config.py`
2. Imported into `job_scraper.py` via config import
3. Stored in `CONFIG['filters']` dictionary:
   - `CONFIG['filters']['fresher_only_mode']`
   - `CONFIG['filters']['india_only_mode']`
4. Applied in `BaseScraper.apply_filters()` method

### Startup Display

When the scraper starts, it displays the mode status:

```
✅ Configuration loaded from config.py
   LinkedIn keywords: 41
   Indeed keywords: 29
   Naukri keywords: 39
   Proxy enabled: False
   🎯 FRESHER ONLY MODE: True
   🇮🇳 INDIA ONLY MODE: True
```

## Implementation Details

### Files Modified

1. **config.py**
   - Added `FRESHER_ONLY_MODE` setting (line 134)
   - Added `INDIA_ONLY_MODE` setting (line 135)
   - Added feature description in header comments

2. **job_scraper.py**
   - Added default values in `CONFIG['filters']` (lines 409-410)
   - Import settings from config.py (lines 495-500)
   - Display mode status at startup (lines 555-556)
   - Enhanced `Job.to_telegram_message()` to always show experience (line 656)
   - Updated hashtags to include #india (line 673)
   - Enhanced `BaseScraper.apply_filters()` with fresher and India logic (lines 1877-1951)

3. **README.md**
   - Added feature descriptions in Features section
   - Added configuration examples
   - Added Telegram message example
   - Added detailed filtering documentation

### Filter Logic Implementation

**Location:** `job_scraper.py` lines 1877-1951

```python
def apply_filters(self, job: Job) -> bool:
    """Apply configured filters"""
    filters = CONFIG['filters']
    
    # ... existing filters ...
    
    # FRESHER ONLY MODE
    if filters.get('fresher_only_mode', False):
        # Check experience field for 3+ years patterns
        # Check title for non-fresher keywords
        # Return False if job doesn't meet criteria
    
    # INDIA ONLY MODE
    if filters.get('india_only_mode', False):
        # Check if location contains Indian city/state
        # Check for international location keywords
        # Return False if job is not in India
    
    return True
```

## Testing

### Test Results
All 7 test cases passed:

1. ✅ Fresher job with India location → PASS
2. ✅ 3+ years experience → FAIL (blocked by fresher mode)
3. ✅ USA location → FAIL (blocked by India mode)
4. ✅ UK location → FAIL (blocked by India mode)
5. ✅ India Tier-2 city → PASS
6. ✅ Remote India → PASS
7. ✅ "Experienced" in title → FAIL (blocked by fresher mode)

### Test Script
```python
from job_scraper import Job, BaseScraper, CONFIG

# Create test job
job = Job(
    id="test1",
    title="Software Engineer Fresher",
    company="TCS",
    location="Bangalore, India",
    source="linkedin",
    url="http://example.com",
    experience="0-2 years"
)

# Test filters
scraper = BaseScraper(...)
result = scraper.apply_filters(job)
print(f"Job passed filters: {result}")  # Should be True
```

## Usage Examples

### Example 1: Enable Both Modes (Recommended)
```python
# config.py
FRESHER_ONLY_MODE = True   # Only fresher jobs
INDIA_ONLY_MODE = True      # Only India locations
MAX_EXPERIENCE_YEARS = 2    # 0-2 years max
```

**Result:** Only fresher/entry-level jobs (0-2 years) from India

### Example 2: Fresher Mode Only
```python
# config.py
FRESHER_ONLY_MODE = True    # Only fresher jobs
INDIA_ONLY_MODE = False     # All locations (including international)
```

**Result:** Fresher jobs from all locations (India + international)

### Example 3: India Mode Only
```python
# config.py
FRESHER_ONLY_MODE = False   # All experience levels
INDIA_ONLY_MODE = True       # Only India locations
```

**Result:** All jobs from India (including senior positions)

### Example 4: Disable Both (Original Behavior)
```python
# config.py
FRESHER_ONLY_MODE = False
INDIA_ONLY_MODE = False
```

**Result:** All jobs from all locations (original behavior)

## Benefits

1. **Targeted Job Search:** Only see jobs relevant to Indian freshers
2. **Reduced Noise:** No senior positions or international jobs
3. **Better Experience Display:** Always know experience requirements upfront
4. **India-Focused:** Comprehensive coverage of Indian cities and states
5. **Easy Configuration:** Simple True/False settings in config.py
6. **Backward Compatible:** Can be disabled without breaking existing setup

## Migration Guide

### Upgrading from Previous Version

1. **Pull latest code:**
   ```bash
   git pull origin main
   ```

2. **Update config.py:**
   ```python
   # Add these two lines to your config.py
   FRESHER_ONLY_MODE = True
   INDIA_ONLY_MODE = True
   ```

3. **Test configuration:**
   ```bash
   python3 -c "import config; print(f'Fresher Mode: {config.FRESHER_ONLY_MODE}')"
   ```

4. **Run scraper:**
   ```python
   from job_scraper import initialize, run
   initialize()
   run()
   ```

### No Breaking Changes
- All existing configurations continue to work
- Modes are opt-in (default: False)
- If not set in config.py, defaults to False
- Telegram message format enhanced but backward compatible

## Troubleshooting

### Jobs not being filtered?
Check that modes are enabled:
```python
from job_scraper import CONFIG
print(CONFIG['filters']['fresher_only_mode'])  # Should be True
print(CONFIG['filters']['india_only_mode'])     # Should be True
```

### India location not recognized?
Check the india_keywords list in `job_scraper.py` line 1917-1933. You can add custom cities if needed.

### Experience filtering too strict?
Adjust MAX_EXPERIENCE_YEARS in config.py:
```python
MAX_EXPERIENCE_YEARS = 3  # Allow up to 3 years instead of 2
```

## Future Enhancements

Potential improvements for future versions:
- Configurable experience range (e.g., 0-3 years, 1-5 years)
- City-specific filtering (e.g., only Bangalore and Mumbai)
- Salary range filtering for India context (e.g., 3-8 LPA)
- Experience level in database for analytics
- Custom location lists in config.py

## Support

For issues or questions:
1. Check the test script above to verify filters are working
2. Review logs for filter debug messages
3. Check CONFIG dictionary values
4. Create an issue with job examples that aren't filtering correctly

---

**Version:** 1.0.0
**Date:** December 2024
**Author:** Job Scraper Bot Team
