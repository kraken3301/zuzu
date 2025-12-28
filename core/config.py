# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

import os
import importlib
from typing import Dict, Any, Tuple, List
from .models import Job, ScrapingStats

# Default Configuration
CONFIG = {
    # Telegram Settings
    'telegram': {
        'enabled': True,
        'bot_token': 'YOUR_BOT_TOKEN_HERE',
        'channel_id': '@your_channel',
        'post_delay_min': 2,
        'post_delay_max': 5,
        'batch_size': 20,
        'send_summary': True,
        'error_notifications': True,
        'admin_chat_id': None,
    },
    
    # LinkedIn Settings
    'linkedin': {
        'enabled': True,
        'use_login': False,
        'email': '',
        'password': '',
        'keywords': [
            'software engineer fresher',
            'python developer entry level',
            'frontend developer fresher',
            'backend developer junior',
            'data analyst fresher',
            'full stack developer entry level',
            'java developer fresher',
            'react developer junior',
            'devops engineer fresher',
            'machine learning fresher',
        ],
        'locations': [
            'India', 'Bangalore', 'Mumbai', 'Delhi NCR', 'Hyderabad', 
            'Pune', 'Chennai', 'Remote'
        ],
        'experience_levels': [1, 2],
        'time_posted': 'r86400',
        'max_results_per_search': 100,
        'max_retries': 5,
        'request_delay_min': 2,
        'request_delay_max': 5,
    },
    
    # Indeed Settings
    'indeed': {
        'enabled': True,
        'use_rss': True,
        'keywords': [
            'fresher software engineer',
            'entry level developer',
            'junior python developer',
            'graduate trainee IT',
            'fresher web developer',
            'trainee software developer',
            'junior data analyst',
            'fresher java developer',
        ],
        'locations': [
            'Bangalore, Karnataka', 'Mumbai, Maharashtra', 'Delhi',
            'Hyderabad, Telangana', 'Pune, Maharashtra', 'Chennai, Tamil Nadu',
            'Gurgaon, Haryana', 'Noida, Uttar Pradesh'
        ],
        'posted_days': 3,
        'experience': '0-2',
        'max_results_per_search': 50,
        'max_retries': 3,
    },
    
    # Naukri Settings
    'naukri': {
        'enabled': True,
        'use_api': True,
        'keywords': [
            'fresher software',
            'entry level developer',
            'trainee engineer',
            'graduate engineer trainee',
            'junior developer',
            'fresher python',
            'fresher java',
            'fresher web developer',
            'fresher data analyst',
            'campus placement',
        ],
        'locations': [
            'bangalore', 'mumbai', 'delhi-ncr', 'hyderabad',
            'pune', 'chennai', 'gurgaon', 'noida'
        ],
        'experience_min': 0,
        'experience_max': 2,
        'freshness': 1,
        'max_pages_per_search': 5,
        'results_per_page': 50,
        'max_retries': 3,
    },
    
    # Superset Settings
    'superset': {
        'enabled': False,
        'login_url': 'https://superset.com/login',
        'dashboard_url': 'https://superset.com/opportunities',
        'email': '',
        'password': '',
        'college_code': '',
        'use_saved_cookies': True,
        'cookie_file': 'superset_cookies.json',
        'max_pages': 10,
        'job_types': ['Full Time', 'Internship'],
        'min_ctc': 0,
        'require_manual_login': False,
    },
    
    # Proxy Settings
    'proxy': {
        'enabled': True,
        'use_free_proxies': True,
        'free_proxy_count': 100,
        'test_before_use': True,
        'test_url': 'https://httpbin.org/ip',
        'test_timeout': 20,
        'request_timeout': 15,
        'connect_timeout': 10,
        'read_timeout': 10,
        'adaptive_timeout': True,
        'timeout_escalation': [15, 20, 30],
        'allow_unverified_ssl': True,
        'custom_proxies': [],
        'rotate_per_request': True,
        'max_failures_before_blacklist': 3,
        'prefer_https': True,
        'geo_filter': None,
        'recovery_time': 300,
        'max_recovery_attempts': 3,
        'min_success_rate': 0.5,
    },
    
    # Filter Settings
    'filters': {
        'exclude_title_keywords': [
            'senior', 'lead', 'manager', 'director', 'principal', 'head', 'vp',
            'architect', 'staff', 'chief', 'partner', 'executive director',
            '5+ years', '7+ years', '10+ years', '12+ years', '15+ years',
            'sr.', 'sr ', 'sr-', 'experienced', 'seasoned',
            'team lead', 'tech lead', 'engineering manager',
            '3-5 years', '5-7 years', '7-10 years', '10+ yrs'
        ],
        'exclude_companies': [],
        'max_experience_years': 2,
    },
    
    # Scraping Behavior
    'scraping': {
        'request_delay_min': 2.0,
        'request_delay_max': 6.0,
        'randomize_order': True,
    },
    
    # Scheduling
    'schedule': {
        'run_interval_hours': 6,
        'quiet_hours_start': 23,
        'quiet_hours_end': 7,
    },
    
    # Data & Storage
    'data': {
        'export_csv': True,
        'export_json': True,
        'export_after_each_run': True,
        'max_age_days': 30,
    },
    
    # Filter Settings
    'filters': {
        'exclude_title_keywords': [
            'senior', 'lead', 'manager', 'director', 'principal', 'head', 'vp',
            'architect', 'staff', 'chief', 'partner', 'executive director',
            '5+ years', '7+ years', '10+ years', '12+ years', '15+ years',
            'sr.', 'sr ', 'sr-', 'experienced', 'seasoned',
            'team lead', 'tech lead', 'engineering manager',
            '3-5 years', '5-7 years', '7-10 years', '10+ yrs'
        ],
        'exclude_companies': [],
        'max_experience_years': 2,
    },
    
    # Logging Configuration
    'logging': {
        'level': 'INFO',
        'file_level': 'DEBUG',
        'console_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'max_log_size': 10485760,  # 10MB
        'backup_count': 5
    },
    
    # Paths
    'paths': {
        'base_dir': 'job_scraper_data',
        'database_dir': 'job_scraper_data/database',
        'logs_dir': 'job_scraper_data/logs',
        'exports_dir': 'job_scraper_data/exports',
        'cookies_dir': 'job_scraper_data/cookies',
        'backups_dir': 'job_scraper_data/backups',
    }
}


def load_config() -> None:
    """Load configuration from config.py if available"""
    try:
        config = importlib.import_module('config')
        
        # Override Telegram settings
        if hasattr(config, 'TELEGRAM_BOT_TOKEN'):
            CONFIG['telegram']['bot_token'] = config.TELEGRAM_BOT_TOKEN
        if hasattr(config, 'TELEGRAM_CHANNEL_ID'):
            CONFIG['telegram']['channel_id'] = config.TELEGRAM_CHANNEL_ID
        
        # Override LinkedIn settings
        if hasattr(config, 'LINKEDIN_KEYWORDS'):
            CONFIG['linkedin']['keywords'] = config.LINKEDIN_KEYWORDS
        if hasattr(config, 'LINKEDIN_LOCATIONS'):
            CONFIG['linkedin']['locations'] = config.LINKEDIN_LOCATIONS
        if hasattr(config, 'LINKEDIN_ENABLED'):
            CONFIG['linkedin']['enabled'] = config.LINKEDIN_ENABLED
        if hasattr(config, 'LINKEDIN_USE_LOGIN'):
            CONFIG['linkedin']['use_login'] = config.LINKEDIN_USE_LOGIN
        
        # Override Indeed settings
        if hasattr(config, 'INDEED_KEYWORDS'):
            CONFIG['indeed']['keywords'] = config.INDEED_KEYWORDS
        if hasattr(config, 'INDEED_LOCATIONS'):
            CONFIG['indeed']['locations'] = config.INDEED_LOCATIONS
        if hasattr(config, 'INDEED_ENABLED'):
            CONFIG['indeed']['enabled'] = config.INDEED_ENABLED
        if hasattr(config, 'INDEED_USE_RSS'):
            CONFIG['indeed']['use_rss'] = config.INDEED_USE_RSS
        
        # Override Naukri settings
        if hasattr(config, 'NAUKRI_KEYWORDS'):
            CONFIG['naukri']['keywords'] = config.NAUKRI_KEYWORDS
        if hasattr(config, 'NAUKRI_LOCATIONS'):
            CONFIG['naukri']['locations'] = config.NAUKRI_LOCATIONS
        if hasattr(config, 'NAUKRI_ENABLED'):
            CONFIG['naukri']['enabled'] = config.NAUKRI_ENABLED
        if hasattr(config, 'NAUKRI_USE_API'):
            CONFIG['naukri']['use_api'] = config.NAUKRI_USE_API
        
        # Override Superset settings
        if hasattr(config, 'SUPERSET_ENABLED'):
            CONFIG['superset']['enabled'] = config.SUPERSET_ENABLED
        if hasattr(config, 'SUPERSET_EMAIL'):
            CONFIG['superset']['email'] = config.SUPERSET_EMAIL
        if hasattr(config, 'SUPERSET_PASSWORD'):
            CONFIG['superset']['password'] = config.SUPERSET_PASSWORD
        if hasattr(config, 'SUPERSET_COLLEGE_CODE'):
            CONFIG['superset']['college_code'] = config.SUPERSET_COLLEGE_CODE
        
        # Override Proxy settings
        if hasattr(config, 'PROXY_ENABLED'):
            CONFIG['proxy']['enabled'] = config.PROXY_ENABLED
        if hasattr(config, 'PROXY_USE_FREE'):
            CONFIG['proxy']['use_free_proxies'] = config.PROXY_USE_FREE
        if hasattr(config, 'PROXY_CUSTOM'):
            CONFIG['proxy']['custom_proxies'] = config.PROXY_CUSTOM
        
        # Override Filter settings
        if hasattr(config, 'EXCLUDE_TITLE_KEYWORDS'):
            CONFIG['filters']['exclude_title_keywords'] = config.EXCLUDE_TITLE_KEYWORDS
        if hasattr(config, 'EXCLUDE_COMPANIES'):
            CONFIG['filters']['exclude_companies'] = config.EXCLUDE_COMPANIES
        if hasattr(config, 'MAX_EXPERIENCE_YEARS'):
            CONFIG['filters']['max_experience_years'] = config.MAX_EXPERIENCE_YEARS
        
        # Override Scraping behavior
        if hasattr(config, 'SCRAPING_DELAY_MIN'):
            CONFIG['scraping']['request_delay_min'] = config.SCRAPING_DELAY_MIN
        if hasattr(config, 'SCRAPING_DELAY_MAX'):
            CONFIG['scraping']['request_delay_max'] = config.SCRAPING_DELAY_MAX
        if hasattr(config, 'SCRAPING_RANDOMIZE_ORDER'):
            CONFIG['scraping']['randomize_order'] = config.SCRAPING_RANDOMIZE_ORDER
        
        # Override Schedule settings
        if hasattr(config, 'RUN_INTERVAL_HOURS'):
            CONFIG['schedule']['run_interval_hours'] = config.RUN_INTERVAL_HOURS
        if hasattr(config, 'QUIET_HOURS_START'):
            CONFIG['schedule']['quiet_hours_start'] = config.QUIET_HOURS_START
        if hasattr(config, 'QUIET_HOURS_END'):
            CONFIG['schedule']['quiet_hours_end'] = config.QUIET_HOURS_END
        
        # Override Data settings
        if hasattr(config, 'EXPORT_CSV'):
            CONFIG['data']['export_csv'] = config.EXPORT_CSV
        if hasattr(config, 'EXPORT_JSON'):
            CONFIG['data']['export_json'] = config.EXPORT_JSON
        if hasattr(config, 'MAX_JOB_AGE_DAYS'):
            CONFIG['data']['max_age_days'] = config.MAX_JOB_AGE_DAYS
        
        print("✅ Configuration loaded from config.py")
        print(f"   LinkedIn keywords: {len(CONFIG['linkedin']['keywords'])}")
        print(f"   Indeed keywords: {len(CONFIG['indeed']['keywords'])}")
        print(f"   Naukri keywords: {len(CONFIG['naukri']['keywords'])}")
        print(f"   Proxy enabled: {CONFIG['proxy']['enabled']}")
        
    except ImportError:
        print("⚠️ config.py not found, using default CONFIG values")
    except Exception as e:
        print(f"⚠️ Error loading config.py: {e}")
        print("   Using default CONFIG values")


def validate_config() -> Tuple[bool, List[str]]:
    """Validate configuration and return (is_valid, errors)"""
    errors = []
    
    # Check Telegram config
    if CONFIG['telegram']['enabled']:
        if not CONFIG['telegram']['bot_token'] or CONFIG['telegram']['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
            errors.append("Telegram bot_token is not set")
        if not CONFIG['telegram']['channel_id']:
            errors.append("Telegram channel_id is not set")
    
    # Check at least one scraper is enabled
    scrapers_enabled = any([
        CONFIG['linkedin']['enabled'],
        CONFIG['indeed']['enabled'],
        CONFIG['naukri']['enabled'],
        CONFIG['superset']['enabled']
    ])
    
    if not scrapers_enabled:
        errors.append("At least one scraper must be enabled")
    
    return (len(errors) == 0, errors)