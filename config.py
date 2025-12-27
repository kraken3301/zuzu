# Configuration file for Multi-Platform Job Scraper
# Update these settings before running the scraper

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather
TELEGRAM_CHANNEL_ID = "@your_channel"      # Channel username or chat ID

# LinkedIn Configuration
LINKEDIN_ENABLED = True
LINKEDIN_USE_LOGIN = False  # ⚠️ Risk of account ban
LINKEDIN_EMAIL = ""
LINKEDIN_PASSWORD = ""

# Indeed Configuration
INDEED_ENABLED = True
INDEED_USE_RSS = True  # RSS is more reliable

# Naukri Configuration
NAUKRI_ENABLED = True
NAUKRI_USE_API = True  # Mobile API (preferred)

# Superset Configuration (requires authentication)
SUPERSET_ENABLED = False
SUPERSET_EMAIL = ""
SUPERSET_PASSWORD = ""
SUPERSET_COLLEGE_CODE = ""

# Proxy Configuration
PROXY_ENABLED = True
PROXY_USE_FREE = True
PROXY_CUSTOM = []  # Add your paid proxies here: ['http://user:pass@ip:port']

# Scraping Behavior
SCRAPING_DELAY_MIN = 2.0
SCRAPING_DELAY_MAX = 6.0
SCRAPING_RANDOMIZE_ORDER = True

# Scheduling
RUN_INTERVAL_HOURS = 6
QUIET_HOURS_START = 23  # Don't post after 11 PM
QUIET_HOURS_END = 7    # Don't post before 7 AM

# Data & Storage
EXPORT_CSV = True
EXPORT_JSON = True
EXPORT_AFTER_EACH_RUN = True
MAX_JOB_AGE_DAYS = 30

# Keywords and Locations
LINKEDIN_KEYWORDS = [
    'software engineer fresher',
    'python developer entry level',
    'frontend developer fresher',
    'backend developer junior',
    'data analyst fresher',
]

LINKEDIN_LOCATIONS = [
    'India',
    'Bangalore',
    'Mumbai',
    'Delhi NCR',
    'Hyderabad',
    'Remote',
]

INDEED_KEYWORDS = [
    'fresher software engineer',
    'entry level developer',
    'junior python developer',
]

INDEED_LOCATIONS = [
    'Bangalore, Karnataka',
    'Mumbai, Maharashtra',
    'Delhi',
    'Hyderabad, Telangana',
]

NAUKRI_KEYWORDS = [
    'fresher software',
    'entry level developer',
    'trainee engineer',
]

NAUKRI_LOCATIONS = [
    'bangalore',
    'mumbai',
    'delhi-ncr',
    'hyderabad',
]

# Filters
EXCLUDE_COMPANIES = []
EXCLUDE_TITLE_KEYWORDS = [
    'senior', 'lead', 'manager', 'director', 'principal',
    'staff', 'architect', '5+ years', '7+ years', '10+ years',
]
MAX_EXPERIENCE_YEARS = 2

# Note: For a complete configuration, you can also directly edit the CONFIG
# dictionary in job_scraper.py. This config.py file provides a simpler
# interface for common settings.
