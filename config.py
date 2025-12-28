# Configuration file for Multi-Platform Job Scraper
# Update these settings before running the scraper

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather
TELEGRAM_CHANNEL_ID = "@your_channel"      # Channel username or chat ID

# --- LINKEDIN CONFIGURATION ---
LINKEDIN_KEYWORDS = [
    # IT & Tech
    'software engineer fresher', 'python developer', 'java developer',
    'data analyst fresher', 'web developer entry level', 'qa engineer',
    'system administrator', 'devops fresher', 'android developer',
    'frontend developer fresher', 'backend developer junior',
    'full stack developer entry level', 'react developer fresher',
    'nodejs developer', 'cloud engineer fresher', 'data scientist fresher',
    # Management & Business
    'business analyst fresher', 'management trainee', 'hr executive',
    'digital marketing fresher', 'sales trainee', 'operations executive',
    'business development executive', 'product manager trainee',
    'project coordinator fresher', 'marketing analyst fresher',
    # Core Engineering
    'mechanical engineer fresher', 'civil engineer fresher', 'electrical engineer trainee',
    'electronics engineer fresher', 'automobile engineer trainee',
    'production engineer fresher', 'quality engineer fresher',
    # Finance & Creative
    'financial analyst fresher', 'accountant', 'content writer',
    'graphic designer', 'ui ux designer', 'video editor fresher',
    'copywriter fresher', 'seo specialist fresher'
]

LINKEDIN_LOCATIONS = [
    'India', 'Remote',
    # Metro Cities
    'Bangalore', 'Mumbai', 'Delhi NCR', 'Hyderabad', 'Pune', 'Chennai',
    # Major Tier 2 Cities
    'Gurgaon', 'Noida', 'Ahmedabad', 'Kolkata', 'Chandigarh', 'Jaipur',
    'Kochi', 'Coimbatore', 'Lucknow', 'Indore', 'Nagpur', 'Surat',
    'Visakhapatnam', 'Bhubaneswar', 'Mysore', 'Vadodara'
]

# --- INDEED CONFIGURATION ---
INDEED_KEYWORDS = [
    'fresher', 'trainee', 'entry level',
    # IT & Software
    'graduate engineer trainee', 'junior software developer',
    'fresher software engineer', 'java developer fresher',
    'python developer entry level', 'web developer trainee',
    # Business & Operations
    'data entry operator', 'back office executive',
    'customer support executive', 'bpo', 'telecaller',
    'hr recruiter', 'marketing executive', 'sales executive',
    # Content & Creative
    'content writing', 'content writer fresher',
    'graphic designer', 'digital marketing fresher',
    # Finance & Accounts
    'accountant fresher', 'accounts executive',
    'finance trainee', 'audit trainee',
    # Operations
    'operations executive', 'logistics coordinator',
    'supply chain trainee', 'warehouse executive'
]

INDEED_LOCATIONS = [
    # Metro Cities with State
    'Bangalore, Karnataka', 'Mumbai, Maharashtra', 'New Delhi, Delhi',
    'Hyderabad, Telangana', 'Pune, Maharashtra', 'Chennai, Tamil Nadu',
    # NCR Region
    'Gurgaon, Haryana', 'Noida, Uttar Pradesh', 'Faridabad, Haryana',
    'Ghaziabad, Uttar Pradesh',
    # Major Cities
    'Kolkata, West Bengal', 'Ahmedabad, Gujarat', 'Chandigarh',
    'Jaipur, Rajasthan', 'Lucknow, Uttar Pradesh', 'Indore, Madhya Pradesh',
    'Kochi, Kerala', 'Coimbatore, Tamil Nadu', 'Surat, Gujarat',
    'Nagpur, Maharashtra', 'Visakhapatnam, Andhra Pradesh',
    'Bhubaneswar, Odisha', 'Mysore, Karnataka', 'Vadodara, Gujarat',
    'Thiruvananthapuram, Kerala', 'Mangalore, Karnataka'
]

# --- NAUKRI CONFIGURATION ---
NAUKRI_KEYWORDS = [
    'fresher', 'entry level', 'graduate trainee',
    # IT & Technology
    'software engineer', 'java developer', 'python developer',
    'web developer', 'data analyst', 'software tester',
    'network engineer', 'system administrator',
    # Business & Management
    'business development', 'sales executive', 'marketing executive',
    'business analyst', 'operations executive', 'hr recruiter',
    # Engineering (Core)
    'mechanical engineer', 'electrical engineer', 'civil engineer',
    'electronics engineer', 'production engineer',
    # Finance & Banking
    'banking', 'finance', 'accountant', 'financial analyst',
    'audit associate', 'investment banking',
    # Training Programs
    'diploma engineer trainee', 'btech fresher', 'mba fresher',
    'mca fresher', 'bca fresher', 'bcom fresher',
    # Other Sectors
    'pharma fresher', 'biotechnology fresher', 'chemical engineer',
    'quality assurance', 'research associate'
]

NAUKRI_LOCATIONS = [
    # Lower case for Naukri API compatibility
    'bangalore', 'mumbai', 'delhi-ncr', 'hyderabad', 'pune', 'chennai',
    'gurgaon', 'noida', 'kolkata', 'ahmedabad', 'chandigarh', 'jaipur',
    'lucknow', 'indore', 'kochi', 'coimbatore', 'surat', 'nagpur',
    'visakhapatnam', 'bhubaneswar', 'mysore', 'vadodara', 'thiruvananthapuram',
    'mangalore', 'nashik', 'rajkot', 'ludhiana', 'agra', 'varanasi'
]

# --- FILTERS ---
# Expanded to exclude more senior roles
EXCLUDE_TITLE_KEYWORDS = [
    'senior', 'lead', 'manager', 'director', 'principal', 'head', 'vp',
    'architect', 'staff', 'chief', 'partner', 'executive director',
    '5+ years', '7+ years', '10+ years', '12+ years', '15+ years',
    'sr.', 'sr ', 'sr-', 'experienced', 'seasoned',
    'team lead', 'tech lead', 'engineering manager',
    '3-5 years', '5-7 years', '7-10 years', '10+ yrs'
]

# Exclude specific companies (if needed)
EXCLUDE_COMPANIES = [
    # Add company names here if you want to exclude them
    # Example: 'CompanyXYZ', 'ABC Corp'
]

MAX_EXPERIENCE_YEARS = 2  # Maximum years of experience for "fresher" jobs

# LinkedIn Configuration
LINKEDIN_ENABLED = True
LINKEDIN_USE_LOGIN = False  # ⚠️ Risk of account ban if set to True
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

# --- GOVERNMENT JOBS RSS CONFIGURATION ---
GOVT_RSS_FEEDS = [
    'https://www.freejobalert.com/feed',
    'https://www.sarkariresultadda.com/feed',
    'https://sarkariexamresult.com/feed',
    'https://www.govtjobsind.com/feed',
    'https://www.sarkariexams.com/feed',
    'https://www.jobhunts.in/feed',
]

# Government Jobs Scraping Settings
GOVT_SCRAPING_TIMEOUT = 10  # seconds per feed request
GOVT_SCRAPING_RETRIES = 3   # retry attempts per failed feed
GOVT_ENABLED = True         # Enable/disable government jobs scraping

# User Agent for HTTP requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Proxy Configuration
PROXY_ENABLED = False  # Set to False for PythonAnywhere/Replit
PROXY_USE_FREE = False
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

# Note: For a complete configuration, you can also directly edit the CONFIG
# dictionary in job_scraper.py. This config.py file provides a simpler
# interface for common settings and will override the defaults in job_scraper.py
# when the file is imported.
