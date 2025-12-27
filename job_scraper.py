# ============================================================================
# MULTI-PLATFORM JOB SCRAPER BOT
# LinkedIn + Indeed + Naukri + Superset → Telegram
# ============================================================================

# ============================================================================
# CELL 1: INSTALLATION & IMPORTS
# ============================================================================
# Description: Install all required packages and import libraries
# Run this cell first! May take 2-3 minutes on fresh Colab runtime.
# ============================================================================

# Install commands (uncomment for Colab)
# !pip install -q beautifulsoup4 lxml fake-useragent requests
# !pip install -q selenium webdriver-manager undetected-chromedriver
# !pip install -q playwright && playwright install chromium
# !pip install -q python-telegram-bot==13.15
# !pip install -q pandas openpyxl tenacity aiohttp
# !pip install -q feedparser  # For Indeed RSS
# !apt-get update && apt-get install -y chromium-chromedriver

import os
import re
import json
import time
import random
import hashlib
import logging
import sqlite3
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple, Set
from urllib.parse import urlencode, quote_plus
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

try:
    from fake_useragent import UserAgent  # type: ignore
except ImportError:  # pragma: no cover
    UserAgent = None  # type: ignore

import feedparser
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager

# Telegram imports
import telegram
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter

# Google Colab specific
try:
    from google.colab import drive
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

FALLBACK_USER_AGENTS: List[str] = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def get_random_user_agent() -> str:
    if UserAgent is not None:
        try:
            return UserAgent().random
        except Exception:
            pass

    return random.choice(FALLBACK_USER_AGENTS)

# ============================================================================
# CELL 2: GOOGLE DRIVE MOUNT & DIRECTORY SETUP
# ============================================================================
# Description: Mount Google Drive and create required directory structure
# This ensures all data persists between Colab sessions
# ============================================================================

def setup_environment():
    """Mount Drive and create directories"""
    if IN_COLAB:
        drive.mount('/content/drive', force_remount=False)
    
    # Create directory structure
    dirs = [
        CONFIG['paths']['base_dir'],
        CONFIG['paths']['database_dir'],
        CONFIG['paths']['logs_dir'],
        CONFIG['paths']['exports_dir'],
        CONFIG['paths']['cookies_dir'],
        CONFIG['paths']['backups_dir'],
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Directory ready: {dir_path}")
    
    return True

# ============================================================================
# CELL 3: CONFIGURATION
# ============================================================================
# Description: Master configuration dictionary
# ⚠️ UPDATE THESE VALUES BEFORE RUNNING:
#    - telegram.bot_token (required)
#    - telegram.channel_id (required)
#    - superset credentials (if using Superset)
#    - Adjust keywords/locations for your job search
# ============================================================================

CONFIG = {
    # =========================================================================
    # TELEGRAM SETTINGS
    # =========================================================================
    'telegram': {
        'enabled': True,
        'bot_token': 'YOUR_BOT_TOKEN_HERE',  # Get from @BotFather
        'channel_id': '@your_channel',        # Channel username or chat ID
        'post_delay_min': 2,                  # Min seconds between posts
        'post_delay_max': 5,                  # Max seconds between posts
        'batch_size': 20,                     # Max jobs per batch
        'send_summary': True,                 # Send run summary
        'error_notifications': True,          # Send error alerts
        'admin_chat_id': None,                # Admin chat for errors (optional)
    },
    
    # =========================================================================
    # LINKEDIN SETTINGS
    # =========================================================================
    'linkedin': {
        'enabled': True,
        'use_login': False,                   # ⚠️ Risk of account ban
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
            'India',
            'Bangalore',
            'Mumbai',
            'Delhi NCR',
            'Hyderabad',
            'Pune',
            'Chennai',
            'Remote',
        ],
        'experience_levels': [1, 2],          # 1=Internship, 2=Entry
        'time_posted': 'r86400',              # Past 24 hours (r604800 = week)
        'max_results_per_search': 100,
        'max_retries': 3,
    },
    
    # =========================================================================
    # INDEED SETTINGS
    # =========================================================================
    'indeed': {
        'enabled': True,
        'use_rss': True,                      # RSS is more reliable
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
            'Bangalore, Karnataka',
            'Mumbai, Maharashtra',
            'Delhi',
            'Hyderabad, Telangana',
            'Pune, Maharashtra',
            'Chennai, Tamil Nadu',
            'Gurgaon, Haryana',
            'Noida, Uttar Pradesh',
        ],
        'posted_days': 3,                     # Jobs from last N days
        'experience': '0-2',                  # Experience filter
        'max_results_per_search': 50,
        'max_retries': 3,
    },
    
    # =========================================================================
    # NAUKRI SETTINGS
    # =========================================================================
    'naukri': {
        'enabled': True,
        'use_api': True,                      # Mobile API (preferred)
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
            'bangalore',
            'mumbai',
            'delhi-ncr',
            'hyderabad',
            'pune',
            'chennai',
            'gurgaon',
            'noida',
        ],
        'experience_min': 0,
        'experience_max': 2,
        'freshness': 1,                       # Days (1, 3, 7, 15)
        'max_pages_per_search': 5,
        'results_per_page': 50,
        'max_retries': 3,
    },
    
    # =========================================================================
    # SUPERSET SETTINGS
    # =========================================================================
    'superset': {
        'enabled': False,                     # Disabled by default (needs creds)
        'login_url': 'https://superset.com/login',
        'dashboard_url': 'https://superset.com/opportunities',
        'email': '',
        'password': '',
        'college_code': '',                   # Some colleges need this
        'use_saved_cookies': True,
        'cookie_file': 'superset_cookies.json',
        'max_pages': 10,
        'job_types': ['Full Time', 'Internship'],
        'min_ctc': 0,                         # Minimum CTC filter (LPA)
        'require_manual_login': False,        # If CAPTCHA/OTP needed
    },
    
    # =========================================================================
    # PROXY SETTINGS
    # =========================================================================
    'proxy': {
        'enabled': True,
        'use_free_proxies': True,
        'free_proxy_count': 50,               # Max free proxies to fetch
        'test_before_use': True,
        'test_url': 'https://httpbin.org/ip',
        'test_timeout': 10,
        'custom_proxies': [
            # Add your paid proxies here
            # 'http://user:pass@ip:port',
            # 'socks5://user:pass@ip:port',
        ],
        'rotate_per_request': True,
        'max_failures_before_blacklist': 3,
        'prefer_https': True,
        'geo_filter': None,                   # e.g., 'IN' for Indian proxies
    },
    
    # =========================================================================
    # SCRAPING BEHAVIOR
    # =========================================================================
    'scraping': {
        'delay_min': 2.0,                     # Minimum delay between requests
        'delay_max': 6.0,                     # Maximum delay
        'page_load_timeout': 30,
        'request_timeout': 20,
        'max_retries': 3,
        'retry_delay': 5,
        'scroll_pause': 1.5,                  # For infinite scroll pages
        'max_scroll_count': 10,
        'concurrent_scrapers': 1,             # Keep 1 to avoid blocks
        'randomize_order': True,              # Randomize keyword/location order
    },
    
    # =========================================================================
    # DATA & STORAGE
    # =========================================================================
    'data': {
        'database_name': 'job_scraper.db',
        'export_csv': True,
        'export_json': True,
        'export_after_each_run': True,
        'max_job_age_days': 30,               # Auto-cleanup older jobs
        'dedupe_window_days': 7,              # Don't re-scrape recent jobs
        'backup_enabled': True,
        'backup_interval_hours': 24,
    },
    
    # =========================================================================
    # SCHEDULING
    # =========================================================================
    'schedule': {
        'run_interval_hours': 6,              # Run every N hours
        'max_runtime_hours': 2,               # Max time per run
        'quiet_hours_start': 23,              # Don't post after 11 PM
        'quiet_hours_end': 7,                 # Don't post before 7 AM
        'timezone': 'Asia/Kolkata',
    },
    
    # =========================================================================
    # PATHS (Auto-configured for Colab and local)
    # =========================================================================
    'paths': {
        'base_dir': '/content/drive/MyDrive/JobScraper' if IN_COLAB else './data',
        'database_dir': '/content/drive/MyDrive/JobScraper/data' if IN_COLAB else './data',
        'logs_dir': '/content/drive/MyDrive/JobScraper/logs' if IN_COLAB else './data/logs',
        'exports_dir': '/content/drive/MyDrive/JobScraper/exports' if IN_COLAB else './data/exports',
        'cookies_dir': '/content/drive/MyDrive/JobScraper/cookies' if IN_COLAB else './data/cookies',
        'backups_dir': '/content/drive/MyDrive/JobScraper/backups' if IN_COLAB else './data/backups',
    },
    
    # =========================================================================
    # LOGGING
    # =========================================================================
    'logging': {
        'console_level': 'INFO',
        'file_level': 'DEBUG',
        'log_file_prefix': 'scraper',
        'max_log_files': 10,
        'log_format': '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
    },
    
    # =========================================================================
    # FILTERS (Applied to all platforms)
    # =========================================================================
    'filters': {
        'exclude_companies': [
            # Add companies to exclude
        ],
        'exclude_title_keywords': [
            'senior', 'lead', 'manager', 'director', 'principal',
            'staff', 'architect', '5+ years', '7+ years', '10+ years',
        ],
        'require_title_keywords': [],         # Job must contain one of these
        'min_salary': None,                   # Minimum salary (if parseable)
        'max_experience_years': 2,            # Skip jobs requiring more exp
    },
}

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
        CONFIG['superset']['enabled'],
    ])
    if not scrapers_enabled:
        errors.append("At least one scraper must be enabled")
    
    # Check Superset credentials if enabled
    if CONFIG['superset']['enabled']:
        if not CONFIG['superset']['email'] or not CONFIG['superset']['password']:
            errors.append("Superset credentials required when Superset is enabled")
    
    return len(errors) == 0, errors

# ============================================================================
# CELL 4: DATA MODELS & EXCEPTIONS
# ============================================================================
# Description: Core data structures used throughout the application
# ============================================================================

@dataclass
class Job:
    """Unified job representation across all platforms"""
    id: str
    title: str
    company: str
    location: str
    source: str
    url: str
    salary: Optional[str] = None
    experience: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    job_type: Optional[str] = None
    source_id: Optional[str] = None
    posted_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    keyword_matched: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)
    posted_to_telegram: bool = False
    telegram_message_id: Optional[int] = None
    
    @staticmethod
    def generate_id(title: str, company: str, source: str) -> str:
        """Generate unique ID from job attributes"""
        raw = f"{title.lower().strip()}|{company.lower().strip()}|{source}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime objects to strings
        if self.posted_date:
            data['posted_date'] = self.posted_date.isoformat()
        if self.deadline:
            data['deadline'] = self.deadline.isoformat()
        data['scraped_at'] = self.scraped_at.isoformat()
        # Convert skills list to JSON string
        if self.skills:
            data['skills'] = json.dumps(self.skills)
        return data
    
    def to_telegram_message(self) -> str:
        """Format job for Telegram posting"""
        source_emoji = {
            'linkedin': '🔗', 'indeed': '📋',
            'naukri': '🇮🇳', 'superset': '🎓'
        }
        
        lines = [
            f"🚨 NEW JOB ALERT {source_emoji.get(self.source, '💼')}",
            "",
            f"💼 {self._escape_md(self.title)}",
            f"🏢 {self._escape_md(self.company)}",
            f"📍 {self._escape_md(self.location or 'Not specified')}",
        ]
        
        if self.experience:
            lines.append(f"📊 Exp: {self._escape_md(self.experience)}")
        if self.salary:
            lines.append(f"💰 {self._escape_md(self.salary)}")
        if self.job_type:
            lines.append(f"📝 {self._escape_md(self.job_type)}")
        if self.deadline:
            lines.append(f"⏰ Deadline: {self.deadline.strftime('%d %b %Y')}")
        if self.skills and len(self.skills) > 0:
            skills_str = ', '.join(self.skills[:5])
            lines.append(f"🛠 Skills: {self._escape_md(skills_str)}")
        
        lines.extend([
            "",
            f"🔗 [Apply Now",
            "",
            f"#{self.source} #jobs #fresher",
        ])
        
        return '\n'.join(lines)
    
    @staticmethod
    def _escape_md(text: str) -> str:
        """Escape Markdown special characters"""
        if not text:
            return ""
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text

@dataclass
class ScrapingStats:
    """Track scraping run statistics"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    linkedin_jobs: int = 0
    linkedin_new: int = 0
    linkedin_errors: int = 0
    
    indeed_jobs: int = 0
    indeed_new: int = 0
    indeed_errors: int = 0
    
    naukri_jobs: int = 0
    naukri_new: int = 0
    naukri_errors: int = 0
    
    superset_jobs: int = 0
    superset_new: int = 0
    superset_errors: int = 0
    
    total_requests: int = 0
    failed_requests: int = 0
    proxies_used: int = 0
    proxies_failed: int = 0
    
    jobs_posted: int = 0
    posting_errors: int = 0
    
    @property
    def total_jobs(self) -> int:
        return self.linkedin_jobs + self.indeed_jobs + self.naukri_jobs + self.superset_jobs
    
    @property
    def total_new(self) -> int:
        return self.linkedin_new + self.indeed_new + self.naukri_new + self.superset_new
    
    def get_runtime(self) -> str:
        end = self.end_time or datetime.now()
        delta = end - self.start_time
        minutes, seconds = divmod(int(delta.total_seconds()), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def get_summary(self) -> str:
        return f"""
📊 SCRAPING RUN SUMMARY

⏱ Runtime: {self.get_runtime()}

Jobs Found:
🔗 LinkedIn: {self.linkedin_jobs} ({self.linkedin_new} new)
📋 Indeed: {self.indeed_jobs} ({self.indeed_new} new)
🇮🇳 Naukri: {self.naukri_jobs} ({self.naukri_new} new)
🎓 Superset: {self.superset_jobs} ({self.superset_new} new)

Totals:
📥 Total Found: {self.total_jobs}
✨ New Jobs: {self.total_new}
📤 Posted: {self.jobs_posted}

Performance:
🌐 Requests: {self.total_requests} ({self.failed_requests} failed)
🔄 Proxies: {self.proxies_used} used, {self.proxies_failed} failed
"""


# Custom Exceptions
class ScraperError(Exception):
    """Base scraper exception"""
    pass

class ProxyError(ScraperError):
    """Proxy-related errors"""
    pass

class RateLimitError(ScraperError):
    """Rate limit hit"""
    pass

class AuthenticationError(ScraperError):
    """Login/authentication failed"""
    pass

class CaptchaError(ScraperError):
    """CAPTCHA encountered"""
    pass

class BlockedError(ScraperError):
    """IP or account blocked"""
    pass


# ============================================================================
# CELL 5: LOGGING MANAGER
# ============================================================================
# Description: Dual logging to console and file
# Logs are saved to Google Drive for persistence
# ============================================================================

class LogManager:
    """Centralized logging configuration"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def setup(self):
        """Initialize logging system"""
        if self._initialized:
            return
        
        log_format = CONFIG['logging']['log_format']
        
        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, CONFIG['logging']['console_level']))
        console_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(console_handler)
        
        # File handler
        log_filename = f"{CONFIG['logging']['log_file_prefix']}_{datetime.now().strftime('%Y%m%d')}.log"
        log_filepath = os.path.join(CONFIG['paths']['logs_dir'], log_filename)
        
        file_handler = logging.FileHandler(log_filepath)
        file_handler.setLevel(getattr(logging, CONFIG['logging']['file_level']))
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
        
        self._initialized = True
        logging.info(f"Logging initialized. Log file: {log_filepath}")
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get named logger"""
        return logging.getLogger(name)
    
    def cleanup_old_logs(self, keep_count: int = None):
        """Remove old log files"""
        keep_count = keep_count or CONFIG['logging']['max_log_files']
        logs_dir = CONFIG['paths']['logs_dir']
        
        log_files = sorted([
            f for f in os.listdir(logs_dir) 
            if f.startswith(CONFIG['logging']['log_file_prefix']) and f.endswith('.log')
        ], reverse=True)
        
        for old_log in log_files[keep_count:]:
            os.remove(os.path.join(logs_dir, old_log))
            logging.debug(f"Removed old log: {old_log}")


# ============================================================================
# CELL 6: DATABASE MANAGER
# ============================================================================
# Description: SQLite database operations
# Database is stored on Google Drive for persistence
# ============================================================================

class DatabaseManager:
    """SQLite database management"""
    
    def __init__(self):
        self.db_path = os.path.join(
            CONFIG['paths']['database_dir'],
            CONFIG['data']['database_name']
        )
        self.logger = LogManager.get_logger('DatabaseManager')
        self._lock = threading.Lock()
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    salary TEXT,
                    experience TEXT,
                    description TEXT,
                    skills TEXT,
                    job_type TEXT,
                    source TEXT NOT NULL,
                    source_id TEXT,
                    url TEXT,
                    posted_date TEXT,
                    deadline TEXT,
                    keyword_matched TEXT,
                    scraped_at TEXT NOT NULL,
                    posted_to_telegram INTEGER DEFAULT 0,
                    telegram_message_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_posted ON jobs(posted_to_telegram)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_scraped ON jobs(scraped_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)')
            
            # Scraping logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    stats_json TEXT,
                    status TEXT,
                    error_message TEXT
                )
            ''')
            
            # Proxy stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proxy_stats (
                    proxy TEXT PRIMARY KEY,
                    total_requests INTEGER DEFAULT 0,
                    successful_requests INTEGER DEFAULT 0,
                    failed_requests INTEGER DEFAULT 0,
                    last_used TEXT,
                    last_success TEXT,
                    blacklisted INTEGER DEFAULT 0,
                    blacklisted_at TEXT
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    platform TEXT PRIMARY KEY,
                    cookies_json TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    is_valid INTEGER DEFAULT 1
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized at {self.db_path}")
    
    def job_exists(self, job_id: str) -> bool:
        """Check if job already exists"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM jobs WHERE id = ?', (job_id,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
    
    def save_job(self, job: Job) -> bool:
        """Save single job, returns True if new"""
        if self.job_exists(job.id):
            return False
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            data = job.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            
            try:
                cursor.execute(
                    f'INSERT INTO jobs ({columns}) VALUES ({placeholders})',
                    list(data.values())
                )
                conn.commit()
                self.logger.debug(f"Saved job: {job.title} at {job.company}")
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()
    
    def save_jobs(self, jobs: List[Job]) -> int:
        """Save multiple jobs, returns count of new jobs"""
        new_count = 0
        for job in jobs:
            if self.save_job(job):
                new_count += 1
        self.logger.info(f"Saved {new_count} new jobs out of {len(jobs)}")
        return new_count
    
    def get_unposted_jobs(self, limit: int = 50) -> List[Job]:
        """Get jobs not yet posted to Telegram"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE posted_to_telegram = 0 
                ORDER BY scraped_at DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_job(row) for row in rows]
    
    def mark_as_posted(self, job_id: str, message_id: int = None):
        """Mark job as posted to Telegram"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE jobs 
                SET posted_to_telegram = 1, telegram_message_id = ?, updated_at = ?
                WHERE id = ?
            ''', (message_id, datetime.now().isoformat(), job_id))
            conn.commit()
            conn.close()
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Total jobs
            cursor.execute('SELECT COUNT(*) FROM jobs')
            stats['total_jobs'] = cursor.fetchone()[0]
            
            # Jobs by source
            cursor.execute('''
                SELECT source, COUNT(*) as count 
                FROM jobs GROUP BY source
            ''')
            stats['by_source'] = {row['source']: row['count'] for row in cursor.fetchall()}
            
            # Unposted jobs
            cursor.execute('SELECT COUNT(*) FROM jobs WHERE posted_to_telegram = 0')
            stats['unposted'] = cursor.fetchone()[0]
            
            # Jobs today
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM jobs 
                WHERE scraped_at LIKE ?
            ''', (f'{today}%',))
            stats['today'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
    
    def cleanup_old_jobs(self, days: int = None):
        """Remove jobs older than specified days"""
        days = days or CONFIG['data']['max_job_age_days']
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM jobs WHERE scraped_at < ?', (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted > 0:
                self.logger.info(f"Cleaned up {deleted} jobs older than {days} days")
            return deleted
    
    def export_to_csv(self, filepath: str = None) -> str:
        """Export all jobs to CSV"""
        if filepath is None:
            filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(CONFIG['paths']['exports_dir'], filename)
        
        with self._lock:
            conn = self._get_connection()
            df = pd.read_sql_query('SELECT * FROM jobs ORDER BY scraped_at DESC', conn)
            conn.close()
        
        df.to_csv(filepath, index=False)
        self.logger.info(f"Exported {len(df)} jobs to {filepath}")
        return filepath
    
    def export_to_json(self, filepath: str = None) -> str:
        """Export all jobs to JSON"""
        if filepath is None:
            filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(CONFIG['paths']['exports_dir'], filename)
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jobs ORDER BY scraped_at DESC')
            rows = cursor.fetchall()
            conn.close()
        
        jobs = [dict(row) for row in rows]
        
        with open(filepath, 'w') as f:
            json.dump(jobs, f, indent=2, default=str)
        
        self.logger.info(f"Exported {len(jobs)} jobs to {filepath}")
        return filepath
    
    def _row_to_job(self, row) -> Job:
        """Convert database row to Job object"""
        skills = None
        if row['skills']:
            try:
                skills = json.loads(row['skills'])
            except:
                skills = None
        
        posted_date = None
        if row['posted_date']:
            try:
                posted_date = datetime.fromisoformat(row['posted_date'])
            except:
                pass
        
        deadline = None
        if row['deadline']:
            try:
                deadline = datetime.fromisoformat(row['deadline'])
            except:
                pass
        
        return Job(
            id=row['id'],
            title=row['title'],
            company=row['company'],
            location=row['location'],
            salary=row['salary'],
            experience=row['experience'],
            description=row['description'],
            skills=skills,
            job_type=row['job_type'],
            source=row['source'],
            source_id=row['source_id'],
            url=row['url'],
            posted_date=posted_date,
            deadline=deadline,
            keyword_matched=row['keyword_matched'],
            scraped_at=datetime.fromisoformat(row['scraped_at']),
            posted_to_telegram=bool(row['posted_to_telegram']),
            telegram_message_id=row['telegram_message_id'],
        )


# ============================================================================
# CELL 7: PROXY MANAGER
# ============================================================================
# Description: Proxy fetching, testing, and rotation
# Uses free proxies by default, supports paid proxies
# ============================================================================

class ProxyManager:
    """Advanced proxy management with rotation and health tracking"""
    
    FREE_PROXY_SOURCES = [
        'https://free-proxy-list.net/',
        'https://www.sslproxies.org/',
        'https://www.us-proxy.org/',
    ]
    
    def __init__(self):
        self.logger = LogManager.get_logger('ProxyManager')
        self._proxies: List[str] = []
        self._working_proxies: Set[str] = set()
        self._blacklist: Set[str] = set()
        self._failures: Dict[str, int] = {}
        self._lock = threading.Lock()
        self._current_index = 0
    
    def initialize(self) -> int:
        """Initialize proxy pool"""
        self.logger.info("Initializing proxy pool...")
        
        # Add custom proxies first
        if CONFIG['proxy']['custom_proxies']:
            self._proxies.extend(CONFIG['proxy']['custom_proxies'])
            self.logger.info(f"Added {len(CONFIG['proxy']['custom_proxies'])} custom proxies")
        
        # Fetch free proxies
        if CONFIG['proxy']['use_free_proxies']:
            for source in self.FREE_PROXY_SOURCES:
                try:
                    proxies = self._fetch_from_source(source)
                    self._proxies.extend(proxies)
                    self.logger.debug(f"Fetched {len(proxies)} proxies from {source}")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch from {source}: {e}")
        
        # Remove duplicates
        self._proxies = list(set(self._proxies))
        
        # Test proxies if enabled
        if CONFIG['proxy']['test_before_use'] and self._proxies:
            self._test_all_proxies()
        else:
            self._working_proxies = set(self._proxies)
        
        working_count = len(self._working_proxies)
        self.logger.info(f"Proxy pool ready: {working_count} working proxies")
        return working_count
    
    def _fetch_from_source(self, url: str) -> List[str]:
        """Fetch proxies from a source URL"""
        proxies = []
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table')
            if table:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        if ip and port:
                            proxies.append(f"http://{ip}:{port}")
        except Exception as e:
            self.logger.debug(f"Error fetching proxies: {e}")
        
        return proxies[:CONFIG['proxy']['free_proxy_count']]
    
    def _test_all_proxies(self):
        """Test all proxies in parallel"""
        self.logger.info(f"Testing {len(self._proxies)} proxies...")
        
        test_url = CONFIG['proxy']['test_url']
        timeout = CONFIG['proxy']['test_timeout']
        
        def test_one(proxy: str) -> Optional[str]:
            try:
                response = requests.get(
                    test_url,
                    proxies={'http': proxy, 'https': proxy},
                    timeout=timeout
                )
                if response.status_code == 200:
                    return proxy
            except:
                pass
            return None
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(test_one, self._proxies))
        
        self._working_proxies = set(p for p in results if p)
        self.logger.info(f"Found {len(self._working_proxies)} working proxies")
    
    def get_proxy(self, domain: str = None) -> Optional[str]:
        """Get next working proxy"""
        if not CONFIG['proxy']['enabled']:
            return None
        
        with self._lock:
            available = self._working_proxies - self._blacklist
            if not available:
                self.logger.warning("No working proxies available!")
                return None
            
            proxy = random.choice(list(available))
            return proxy
    
    def report_success(self, proxy: str, domain: str = None):
        """Report successful proxy use"""
        with self._lock:
            self._failures[proxy] = 0
            self._working_proxies.add(proxy)
    
    def report_failure(self, proxy: str, domain: str = None, error: str = None):
        """Report proxy failure"""
        with self._lock:
            self._failures[proxy] = self._failures.get(proxy, 0) + 1
            
            max_failures = CONFIG['proxy']['max_failures_before_blacklist']
            if self._failures[proxy] >= max_failures:
                self._blacklist.add(proxy)
                self._working_proxies.discard(proxy)
                self.logger.debug(f"Blacklisted proxy: {proxy}")
    
    def get_working_count(self) -> int:
        """Get count of working proxies"""
        return len(self._working_proxies - self._blacklist)
    
    def get_stats(self) -> dict:
        """Get proxy statistics"""
        return {
            'total': len(self._proxies),
            'working': len(self._working_proxies),
            'blacklisted': len(self._blacklist),
            'available': self.get_working_count(),
        }


# ============================================================================
# CELL 8: FINGERPRINT GENERATOR
# ============================================================================
# Description: Generate realistic browser fingerprints
# Helps avoid detection by varying request headers
# ============================================================================

class FingerprintGenerator:
    """Generate realistic browser fingerprints"""
    
    CHROME_VERSIONS = ['120.0.0.0', '121.0.0.0', '122.0.0.0', '123.0.0.0']
    FIREFOX_VERSIONS = ['121.0', '122.0', '123.0']
    
    ACCEPT_LANGUAGE = [
        'en-US,en;q=0.9',
        'en-GB,en;q=0.9',
        'en-IN,en;q=0.9,hi;q=0.8',
    ]
    
    @classmethod
    def generate_chrome_fingerprint(cls) -> dict:
        """Generate Chrome-like headers"""
        version = random.choice(cls.CHROME_VERSIONS)
        return {
            'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(cls.ACCEPT_LANGUAGE),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Ch-Ua': f'"Chromium";v="{version.split(".")[0]}", "Google Chrome";v="{version.split(".")[0]}"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
    
    @classmethod
    def generate_mobile_fingerprint(cls) -> dict:
        """Generate mobile-like headers"""
        return {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    @classmethod
    def get_random(cls) -> dict:
        """Get random fingerprint"""
        return random.choice([
            cls.generate_chrome_fingerprint,
            cls.generate_mobile_fingerprint,
        ])()


# ============================================================================
# CELL 9: HTTP CLIENT
# ============================================================================
# Description: HTTP client with retry logic and proxy support
# Handles all HTTP requests with automatic retries
# ============================================================================

class HTTPClient:
    """HTTP client with retry, proxy rotation, and fingerprint spoofing"""
    
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.logger = LogManager.get_logger('HTTPClient')
        self.session = requests.Session()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True
    )
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request with retry"""
        # Add fingerprint headers
        headers = FingerprintGenerator.get_random()
        headers.update(kwargs.pop('headers', {}))
        
        # Add proxy
        proxy = self.proxy_manager.get_proxy()
        proxies = {'http': proxy, 'https': proxy} if proxy else None
        
        # Add delay
        time.sleep(random.uniform(
            CONFIG['scraping']['delay_min'],
            CONFIG['scraping']['delay_max']
        ))
        
        try:
            response = self.session.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=CONFIG['scraping']['request_timeout'],
                **kwargs
            )
            
            if proxy:
                self.proxy_manager.report_success(proxy)
            
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            if proxy:
                self.proxy_manager.report_failure(proxy, error=str(e))
            self.logger.warning(f"Request failed: {url} - {e}")
            raise
    
    def get_soup(self, url: str, **kwargs) -> BeautifulSoup:
        """Get BeautifulSoup object from URL"""
        response = self.get(url, **kwargs)
        return BeautifulSoup(response.text, 'lxml')
    
    def get_json(self, url: str, **kwargs) -> dict:
        """Get JSON response from URL"""
        response = self.get(url, **kwargs)
        return response.json()


# ============================================================================
# CELL 10: BROWSER MANAGER
# ============================================================================
# Description: Selenium/Playwright browser management with stealth
# Used for JavaScript-heavy pages and login flows
# ============================================================================

class BrowserManager:
    """Browser automation with anti-detection"""
    
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.logger = LogManager.get_logger('BrowserManager')
        self._drivers: List[webdriver.Chrome] = []
    
    def get_selenium_driver(
        self, 
        proxy: str = None, 
        headless: bool = True
    ) -> webdriver.Chrome:
        """Get Selenium Chrome driver with stealth settings"""
        
        options = Options()
        
        if headless:
            options.add_argument('--headless=new')
        
        # Anti-detection settings
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={UserAgent().random}')
        
        # Disable automation flags
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add proxy if provided
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        
        # Create driver
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except:
            # Fallback for Colab
            driver = webdriver.Chrome(options=options)
        
        # Apply stealth patches
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            '''
        })
        
        driver.set_page_load_timeout(CONFIG['scraping']['page_load_timeout'])
        
        self._drivers.append(driver)
        self.logger.debug("Created new Selenium driver")
        return driver
    
    def human_scroll(self, driver, times: int = 5, pause: float = None):
        """Scroll page like a human"""
        pause = pause or CONFIG['scraping']['scroll_pause']
        
        for i in range(times):
            scroll_amount = random.randint(300, 700)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(pause + random.uniform(0, 0.5))
    
    def human_type(self, element, text: str, min_delay: float = 0.05, max_delay: float = 0.15):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))
    
    def wait_for_element(
        self, 
        driver, 
        selector: str, 
        by: By = By.CSS_SELECTOR, 
        timeout: int = 10
    ):
        """Wait for element to be present"""
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, selector)))
    
    def safe_click(self, driver, selector: str, by: By = By.CSS_SELECTOR):
        """Safely click an element"""
        try:
            element = self.wait_for_element(driver, selector, by)
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            self.logger.debug(f"Click failed for {selector}: {e}")
            return False
    
    def take_screenshot(self, driver, name: str):
        """Take screenshot for debugging"""
        filepath = os.path.join(
            CONFIG['paths']['logs_dir'],
            f"screenshot_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        driver.save_screenshot(filepath)
        self.logger.debug(f"Screenshot saved: {filepath}")
        return filepath
    
    def quit_all(self):
        """Quit all managed drivers"""
        for driver in self._drivers:
            try:
                driver.quit()
            except:
                pass
        self._drivers = []
        self.logger.debug("All browser drivers closed")


# ============================================================================
# CELL 11: BASE SCRAPER
# ============================================================================
# Description: Abstract base class for all scrapers
# Provides common functionality for filtering and validation
# ============================================================================

class BaseScraper(ABC):
    """Abstract base class for job scrapers"""
    
    def __init__(
        self,
        db: DatabaseManager,
        proxy_manager: ProxyManager,
        http_client: HTTPClient,
        browser_manager: BrowserManager
    ):
        self.db = db
        self.proxy_manager = proxy_manager
        self.http = http_client
        self.browser = browser_manager
        self.logger = LogManager.get_logger(self.__class__.__name__)
        self.stats = {'found': 0, 'new': 0, 'errors': 0}
    
    @abstractmethod
    def scrape_all(self) -> List[Job]:
        """Main scraping method - must be implemented"""
        pass
    
    def validate_job(self, job: Job) -> bool:
        """Validate job has required fields"""
        if not job.title or not job.company:
            return False
        if not job.url:
            return False
        return True
    
    def apply_filters(self, job: Job) -> bool:
        """Apply configured filters"""
        filters = CONFIG['filters']
        
        # Exclude companies
        if filters['exclude_companies']:
            if any(exc.lower() in job.company.lower() for exc in filters['exclude_companies']):
                self.logger.debug(f"Filtered out (company): {job.company}")
                return False
        
        # Exclude title keywords
        if filters['exclude_title_keywords']:
            title_lower = job.title.lower()
            if any(kw.lower() in title_lower for kw in filters['exclude_title_keywords']):
                self.logger.debug(f"Filtered out (title): {job.title}")
                return False
        
        return True
    
    def get_stats(self) -> dict:
        """Get scraper statistics"""
        return self.stats.copy()


# ============================================================================
# CELL 12: LINKEDIN SCRAPER
# ============================================================================
# Description: LinkedIn job scraper
# Uses public guest API (safer) or logged-in scraping (higher risk)
# ============================================================================

class LinkedInScraper(BaseScraper):
    """LinkedIn job scraper"""
    
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    
    def scrape_all(self) -> List[Job]:
        """Scrape all configured LinkedIn searches"""
        if not CONFIG['linkedin']['enabled']:
            self.logger.info("LinkedIn scraper disabled")
            return []
        
        all_jobs = []
        keywords = CONFIG['linkedin']['keywords']
        locations = CONFIG['linkedin']['locations']
        
        # Randomize order to avoid patterns
        if CONFIG['scraping']['randomize_order']:
            random.shuffle(keywords)
            random.shuffle(locations)
        
        for keyword in keywords:
            for location in locations:
                try:
                    self.logger.info(f"Scraping LinkedIn: '{keyword}' in '{location}'")
                    jobs = self._scrape_public_api(keyword, location)
                    all_jobs.extend(jobs)
                    self.stats['found'] += len(jobs)
                except Exception as e:
                    self.logger.error(f"LinkedIn scrape error: {e}")
                    self.stats['errors'] += 1
        
        return all_jobs
    
    def _scrape_public_api(self, keyword: str, location: str) -> List[Job]:
        """Scrape using public guest API"""
        jobs = []
        start = 0
        max_results = CONFIG['linkedin']['max_results_per_search']
        
        while start < max_results:
            params = {
                'keywords': keyword,
                'location': location,
                'f_E': ','.join(map(str, CONFIG['linkedin']['experience_levels'])),
                'f_TPR': CONFIG['linkedin']['time_posted'],
                'start': start,
            }
            
            url = f"{self.BASE_URL}?{urlencode(params)}"
            
            try:
                soup = self.http.get_soup(url)
                cards = soup.find_all('div', class_='base-card')
                
                if not cards:
                    break
                
                for card in cards:
                    try:
                        job = self._parse_public_card(card, keyword)
                        if job and self.validate_job(job) and self.apply_filters(job):
                            jobs.append(job)
                    except Exception as e:
                        self.logger.debug(f"Failed to parse card: {e}")
                
                start += 25
                
            except Exception as e:
                self.logger.warning(f"LinkedIn API request failed: {e}")
                break
        
        self.logger.info(f"Found {len(jobs)} LinkedIn jobs for '{keyword}'")
        return jobs
    
    def _parse_public_card(self, card, keyword: str) -> Optional[Job]:
        """Parse job card from public API response"""
        try:
            title_elem = card.find('h3', class_='base-search-card__title')
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            location_elem = card.find('span', class_='job-search-card__location')
            link_elem = card.find('a', class_='base-card__full-link')
            
            if not all([title_elem, company_elem, link_elem]):
                return None
            
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True)
            location = location_elem.get_text(strip=True) if location_elem else ""
            url = link_elem.get('href', '').split('?')[0]
            
            # Get job ID from URL
            source_id = url.split('-')[-1] if url else None
            
            return Job(
                id=Job.generate_id(title, company, 'linkedin'),
                title=title,
                company=company,
                location=location,
                source='linkedin',
                source_id=source_id,
                url=url,
                keyword_matched=keyword,
            )
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None


# ============================================================================
# CELL 13: INDEED SCRAPER
# ============================================================================
# Description: Indeed job scraper
# Uses RSS feed (most reliable) or web scraping
# ============================================================================

class IndeedScraper(BaseScraper):
    """Indeed job scraper"""
    
    RSS_URL = "https://www.indeed.com/rss"
    
    def scrape_all(self) -> List[Job]:
        """Scrape all configured Indeed searches"""
        if not CONFIG['indeed']['enabled']:
            self.logger.info("Indeed scraper disabled")
            return []
        
        all_jobs = []
        keywords = CONFIG['indeed']['keywords']
        locations = CONFIG['indeed']['locations']
        
        if CONFIG['scraping']['randomize_order']:
            random.shuffle(keywords)
            random.shuffle(locations)
        
        for keyword in keywords:
            for location in locations:
                try:
                    self.logger.info(f"Scraping Indeed: '{keyword}' in '{location}'")
                    
                    if CONFIG['indeed']['use_rss']:
                        jobs = self._scrape_via_rss(keyword, location)
                    else:
                        jobs = self._scrape_via_web(keyword, location)
                    
                    all_jobs.extend(jobs)
                    self.stats['found'] += len(jobs)
                except Exception as e:
                    self.logger.error(f"Indeed scrape error: {e}")
                    self.stats['errors'] += 1
        
        return all_jobs
    
    def _scrape_via_rss(self, keyword: str, location: str) -> List[Job]:
        """Scrape using RSS feed"""
        jobs = []
        
        params = {
            'q': keyword,
            'l': location,
            'fromage': CONFIG['indeed']['posted_days'],
            'sort': 'date',
        }
        
        url = f"{self.RSS_URL}?{urlencode(params)}"
        
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:CONFIG['indeed']['max_results_per_search']]:
                try:
                    job = self._parse_rss_item(entry, keyword)
                    if job and self.validate_job(job) and self.apply_filters(job):
                        jobs.append(job)
                except Exception as e:
                    self.logger.debug(f"Failed to parse RSS item: {e}")
        
        except Exception as e:
            self.logger.warning(f"Indeed RSS request failed: {e}")
        
        self.logger.info(f"Found {len(jobs)} Indeed jobs for '{keyword}'")
        return jobs
    
    def _parse_rss_item(self, entry, keyword: str) -> Optional[Job]:
        """Parse RSS feed entry"""
        try:
            title = entry.get('title', '')
            
            # Indeed RSS format: "Job Title - Company - Location"
            parts = title.rsplit(' - ', 2)
            
            if len(parts) >= 2:
                job_title = parts[0].strip()
                company = parts[1].strip()
                location = parts[2].strip() if len(parts) > 2 else ""
            else:
                job_title = title
                company = "Unknown"
                location = ""
            
            url = entry.get('link', '')
            
            # Extract description snippet
            description = ""
            if 'summary' in entry:
                soup = BeautifulSoup(entry.summary, 'html.parser')
                description = soup.get_text(strip=True)[:500]
            
            return Job(
                id=Job.generate_id(job_title, company, 'indeed'),
                title=job_title,
                company=company,
                location=location,
                source='indeed',
                url=url,
                description=description,
                keyword_matched=keyword,
            )
        except Exception as e:
            self.logger.debug(f"RSS parse error: {e}")
            return None
    
    def _scrape_via_web(self, keyword: str, location: str) -> List[Job]:
        """Scrape via web pages (fallback)"""
        jobs = []
        base_url = "https://www.indeed.com/jobs"
        
        params = {
            'q': keyword,
            'l': location,
            'fromage': CONFIG['indeed']['posted_days'],
        }
        
        try:
            soup = self.http.get_soup(f"{base_url}?{urlencode(params)}")
            cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in cards[:CONFIG['indeed']['max_results_per_search']]:
                try:
                    job = self._parse_web_card(card, keyword)
                    if job and self.validate_job(job) and self.apply_filters(job):
                        jobs.append(job)
                except Exception as e:
                    self.logger.debug(f"Failed to parse web card: {e}")
        
        except Exception as e:
            self.logger.warning(f"Indeed web request failed: {e}")
        
        return jobs
    
    def _parse_web_card(self, card, keyword: str) -> Optional[Job]:
        """Parse web page job card"""
        try:
            title_elem = card.find('h2', class_='jobTitle')
            company_elem = card.find('span', {'data-testid': 'company-name'})
            location_elem = card.find('div', {'data-testid': 'text-location'})
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            link = title_elem.find('a')
            url = f"https://www.indeed.com{link.get('href', '')}" if link else ""
            
            return Job(
                id=Job.generate_id(title, company, 'indeed'),
                title=title,
                company=company,
                location=location,
                source='indeed',
                url=url,
                keyword_matched=keyword,
            )
        except Exception as e:
            self.logger.debug(f"Web card parse error: {e}")
            return None


# ============================================================================
# CELL 14: NAUKRI SCRAPER
# ============================================================================
# Description: Naukri.com job scraper
# Uses mobile API (preferred) or Selenium fallback
# ============================================================================

class NaukriScraper(BaseScraper):
    """Naukri.com job scraper"""
    
    API_URL = "https://www.naukri.com/jobapi/v3/search"
    
    def scrape_all(self) -> List[Job]:
        """Scrape all configured Naukri searches"""
        if not CONFIG['naukri']['enabled']:
            self.logger.info("Naukri scraper disabled")
            return []
        
        all_jobs = []
        keywords = CONFIG['naukri']['keywords']
        locations = CONFIG['naukri']['locations']
        
        if CONFIG['scraping']['randomize_order']:
            random.shuffle(keywords)
            random.shuffle(locations)
        
        for keyword in keywords:
            for location in locations:
                try:
                    self.logger.info(f"Scraping Naukri: '{keyword}' in '{location}'")
                    
                    if CONFIG['naukri']['use_api']:
                        jobs = self._scrape_via_api(keyword, location)
                    else:
                        jobs = self._scrape_via_selenium(keyword, location)
                    
                    all_jobs.extend(jobs)
                    self.stats['found'] += len(jobs)
                except Exception as e:
                    self.logger.error(f"Naukri scrape error: {e}")
                    self.stats['errors'] += 1
        
        return all_jobs
    
    def _get_api_headers(self) -> dict:
        """Get headers for Naukri API"""
        return {
            'appid': '109',
            'systemid': 'Naukri',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
        }
    
    def _scrape_via_api(self, keyword: str, location: str) -> List[Job]:
        """Scrape using mobile API"""
        jobs = []
        
        for page in range(1, CONFIG['naukri']['max_pages_per_search'] + 1):
            try:
                params = {
                    'noOfResults': CONFIG['naukri']['results_per_page'],
                    'urlType': 'search_by_keyword',
                    'searchType': 'adv',
                    'keyword': keyword,
                    'location': location,
                    'experience': f"{CONFIG['naukri']['experience_min']}-{CONFIG['naukri']['experience_max']}",
                    'freshness': CONFIG['naukri']['freshness'],
                    'pageNo': page,
                }
                
                response = requests.get(
                    self.API_URL,
                    params=params,
                    headers=self._get_api_headers(),
                    timeout=CONFIG['scraping']['request_timeout']
                )
                
                if response.status_code != 200:
                    self.logger.warning(f"Naukri API returned {response.status_code}")
                    break
                
                data = response.json()
                job_list = data.get('jobDetails', [])
                
                if not job_list:
                    break
                
                for job_data in job_list:
                    try:
                        job = self._parse_api_response(job_data, keyword)
                        if job and self.validate_job(job) and self.apply_filters(job):
                            jobs.append(job)
                    except Exception as e:
                        self.logger.debug(f"Failed to parse API response: {e}")
                
                # Delay between pages
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.warning(f"Naukri API request failed: {e}")
                break
        
        self.logger.info(f"Found {len(jobs)} Naukri jobs for '{keyword}'")
        return jobs
    
    def _parse_api_response(self, data: dict, keyword: str) -> Optional[Job]:
        """Parse job from API response"""
        try:
            title = data.get('title', '')
            company = data.get('companyName', '')
            location = data.get('placeholders', [{}])[0].get('label', '')
            
            experience = data.get('experienceText', '')
            salary = data.get('salaryText', '')
            
            # Skills
            skills = data.get('tagsAndSkills', '').split(',')
            skills = [s.strip() for s in skills if s.strip()]
            
            # URL
            job_id = data.get('jobId', '')
            url = f"https://www.naukri.com/job-listings-{job_id}" if job_id else ""
            
            return Job(
                id=Job.generate_id(title, company, 'naukri'),
                title=title,
                company=company,
                location=location,
                experience=experience,
                salary=salary,
                skills=skills[:10],
                source='naukri',
                source_id=job_id,
                url=url,
                keyword_matched=keyword,
            )
        except Exception as e:
            self.logger.debug(f"API parse error: {e}")
            return None
    
    def _scrape_via_selenium(self, keyword: str, location: str) -> List[Job]:
        """Scrape using Selenium (fallback)"""
        jobs = []
        driver = None
        
        try:
            driver = self.browser.get_selenium_driver()
            
            search_url = f"https://www.naukri.com/{keyword.replace(' ', '-')}-jobs-in-{location}"
            driver.get(search_url)
            
            time.sleep(3)
            
            # Scroll to load more jobs
            self.browser.human_scroll(driver, times=5)
            
            # Parse job cards
            soup = BeautifulSoup(driver.page_source, 'lxml')
            cards = soup.find_all('article', class_='jobTuple')
            
            for card in cards:
                try:
                    job = self._parse_selenium_card(card, keyword)
                    if job and self.validate_job(job) and self.apply_filters(job):
                        jobs.append(job)
                except Exception as e:
                    self.logger.debug(f"Failed to parse Selenium card: {e}")
            
        except Exception as e:
            self.logger.error(f"Naukri Selenium error: {e}")
        finally:
            if driver:
                driver.quit()
        
        return jobs
    
    def _parse_selenium_card(self, card, keyword: str) -> Optional[Job]:
        """Parse job card from Selenium page"""
        try:
            title_elem = card.find('a', class_='title')
            company_elem = card.find('a', class_='subTitle')
            location_elem = card.find('li', class_='location')
            exp_elem = card.find('li', class_='experience')
            salary_elem = card.find('li', class_='salary')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            location = location_elem.get_text(strip=True) if location_elem else ""
            experience = exp_elem.get_text(strip=True) if exp_elem else ""
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            url = title_elem.get('href', '')
            
            return Job(
                id=Job.generate_id(title, company, 'naukri'),
                title=title,
                company=company,
                location=location,
                experience=experience,
                salary=salary,
                source='naukri',
                url=url,
                keyword_matched=keyword,
            )
        except Exception as e:
            self.logger.debug(f"Selenium card parse error: {e}")
            return None


# ============================================================================
# CELL 15: SUPERSET SCRAPER
# ============================================================================
# Description: Superset (college placement) scraper
# ⚠️ Requires authentication - disabled by default
# Set credentials in CONFIG to enable
# ============================================================================

class SupersetScraper(BaseScraper):
    """Superset college placement platform scraper"""
    
    def scrape_all(self) -> List[Job]:
        """Scrape Superset opportunities"""
        if not CONFIG['superset']['enabled']:
            self.logger.info("Superset scraper disabled")
            return []
        
        jobs = []
        driver = None
        
        try:
            driver = self.browser.get_selenium_driver(headless=True)
            
            # Attempt to load saved cookies
            if CONFIG['superset']['use_saved_cookies']:
                if self._load_cookies(driver):
                    self.logger.info("Loaded saved Superset session")
                else:
                    if not self._login(driver):
                        self.logger.error("Superset login failed")
                        return []
            else:
                if not self._login(driver):
                    self.logger.error("Superset login failed")
                    return []
            
            # Navigate to opportunities
            self._navigate_to_jobs(driver)
            
            # Scrape job cards
            jobs = self._scrape_job_cards(driver)
            self.stats['found'] = len(jobs)
            
            # Save cookies for next time
            self._save_cookies(driver)
            
        except Exception as e:
            self.logger.error(f"Superset scrape error: {e}")
            self.stats['errors'] += 1
        finally:
            if driver:
                driver.quit()
        
        return jobs
    
    def _login(self, driver) -> bool:
        """Login to Superset"""
        try:
            driver.get(CONFIG['superset']['login_url'])
            time.sleep(3)
            
            # Find and fill email
            email_input = self.browser.wait_for_element(driver, 'input[type="email"]')
            self.browser.human_type(email_input, CONFIG['superset']['email'])
            
            # Find and fill password
            password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            self.browser.human_type(password_input, CONFIG['superset']['password'])
            
            # Click login button
            time.sleep(1)
            self.browser.safe_click(driver, 'button[type="submit"]')
            
            # Wait for redirect
            time.sleep(5)
            
            # Check if login successful
            if 'login' not in driver.current_url.lower():
                self.logger.info("Superset login successful")
                return True
            else:
                self.logger.warning("Superset login may have failed")
                
                if CONFIG['superset']['require_manual_login']:
                    self._wait_for_manual_login(driver)
                    return True
                
                return False
            
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False
    
    def _wait_for_manual_login(self, driver, timeout: int = 120):
        """Wait for manual login (for CAPTCHA cases)"""
        self.logger.info(f"Please complete login manually within {timeout} seconds...")
        self.browser.take_screenshot(driver, "manual_login_required")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if 'login' not in driver.current_url.lower():
                self.logger.info("Manual login completed")
                return True
            time.sleep(2)
        
        return False
    
    def _load_cookies(self, driver) -> bool:
        """Load saved cookies"""
        cookie_file = os.path.join(
            CONFIG['paths']['cookies_dir'],
            CONFIG['superset']['cookie_file']
        )
        
        if not os.path.exists(cookie_file):
            return False
        
        try:
            driver.get(CONFIG['superset']['login_url'])
            
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass
            
            driver.refresh()
            time.sleep(3)
            
            return 'login' not in driver.current_url.lower()
            
        except Exception as e:
            self.logger.debug(f"Failed to load cookies: {e}")
            return False
    
    def _save_cookies(self, driver):
        """Save cookies for future use"""
        cookie_file = os.path.join(
            CONFIG['paths']['cookies_dir'],
            CONFIG['superset']['cookie_file']
        )
        
        try:
            cookies = driver.get_cookies()
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f)
            self.logger.debug("Saved Superset cookies")
        except Exception as e:
            self.logger.debug(f"Failed to save cookies: {e}")
    
    def _navigate_to_jobs(self, driver):
        """Navigate to jobs/opportunities page"""
        driver.get(CONFIG['superset']['dashboard_url'])
        time.sleep(3)
    
    def _scrape_job_cards(self, driver) -> List[Job]:
        """Scrape job cards from dashboard"""
        jobs = []
        
        # Scroll to load more
        self.browser.human_scroll(driver, times=CONFIG['superset']['max_pages'])
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        # Find job cards (adjust selector based on actual page structure)
        cards = soup.find_all('div', class_='opportunity-card')
        
        for card in cards:
            try:
                job = self._parse_job_card(card)
                if job and self.validate_job(job) and self.apply_filters(job):
                    jobs.append(job)
            except Exception as e:
                self.logger.debug(f"Failed to parse Superset card: {e}")
        
        self.logger.info(f"Found {len(jobs)} Superset opportunities")
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Job]:
        """Parse Superset opportunity card"""
        try:
            title_elem = card.find('h3') or card.find('div', class_='title')
            company_elem = card.find('div', class_='company')
            ctc_elem = card.find('div', class_='ctc') or card.find('span', class_='salary')
            deadline_elem = card.find('div', class_='deadline')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            salary = ctc_elem.get_text(strip=True) if ctc_elem else ""
            
            deadline = None
            if deadline_elem:
                deadline_text = deadline_elem.get_text(strip=True)
                # Parse deadline (adjust format as needed)
            
            # Get URL
            link = card.find('a')
            url = link.get('href', '') if link else ""
            if url and not url.startswith('http'):
                url = f"https://superset.com{url}"
            
            return Job(
                id=Job.generate_id(title, company, 'superset'),
                title=title,
                company=company,
                location="India",
                salary=salary,
                deadline=deadline,
                job_type="Campus Placement",
                source='superset',
                url=url,
            )
        except Exception as e:
            self.logger.debug(f"Superset card parse error: {e}")
            return None


# ============================================================================
# CELL 16: TELEGRAM POSTER
# ============================================================================
# Description: Post jobs to Telegram channel
# Handles rate limiting and error recovery
# ============================================================================

class TelegramPoster:
    """Post jobs to Telegram channel"""
    
    def __init__(self):
        self.logger = LogManager.get_logger('TelegramPoster')
        self.bot = None
        
        if CONFIG['telegram']['enabled']:
            self.bot = Bot(token=CONFIG['telegram']['bot_token'])
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.bot:
            return False
        
        try:
            bot_info = self.bot.get_me()
            self.logger.info(f"Connected to Telegram bot: @{bot_info.username}")
            return True
        except Exception as e:
            self.logger.error(f"Telegram connection failed: {e}")
            return False
    
    def post_job(self, job: Job) -> Optional[int]:
        """Post single job, returns message_id"""
        if not CONFIG['telegram']['enabled'] or not self.bot:
            return None
        
        if self._is_quiet_hours():
            self.logger.debug("Quiet hours - skipping post")
            return None
        
        try:
            message = job.to_telegram_message()
            
            # Try Markdown first
            try:
                result = self.bot.send_message(
                    chat_id=CONFIG['telegram']['channel_id'],
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            except:
                # Fallback to plain text
                plain_message = self._strip_formatting(message)
                result = self.bot.send_message(
                    chat_id=CONFIG['telegram']['channel_id'],
                    text=plain_message,
                    disable_web_page_preview=True
                )
            
            self.logger.debug(f"Posted job: {job.title}")
            return result.message_id
            
        except RetryAfter as e:
            self.logger.warning(f"Rate limited, waiting {e.retry_after}s")
            time.sleep(e.retry_after)
            return self.post_job(job)
        except Exception as e:
            self.logger.error(f"Failed to post job: {e}")
            return None
    
    def post_jobs(self, jobs: List[Job]) -> List[int]:
        """Post multiple jobs with rate limiting"""
        message_ids = []
        
        for job in jobs:
            msg_id = self.post_job(job)
            if msg_id:
                message_ids.append(msg_id)
            
            # Delay between posts
            delay = random.uniform(
                CONFIG['telegram']['post_delay_min'],
                CONFIG['telegram']['post_delay_max']
            )
            time.sleep(delay)
        
        return message_ids
    
    def send_summary(self, stats: ScrapingStats):
        """Send run summary"""
        if not CONFIG['telegram']['enabled'] or not CONFIG['telegram']['send_summary']:
            return
        
        try:
            self.bot.send_message(
                chat_id=CONFIG['telegram']['channel_id'],
                text=stats.get_summary(),
                parse_mode=ParseMode.MARKDOWN
            )
            self.logger.info("Posted run summary to Telegram")
        except Exception as e:
            self.logger.error(f"Failed to send summary: {e}")
    
    def send_error(self, message: str):
        """Send error notification"""
        if not CONFIG['telegram']['error_notifications']:
            return
        
        chat_id = CONFIG['telegram'].get('admin_chat_id') or CONFIG['telegram']['channel_id']
        
        try:
            self.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Scraper Error\n\n{message}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    
    def _is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours"""
        now = datetime.now()
        hour = now.hour
        
        start = CONFIG['schedule']['quiet_hours_start']
        end = CONFIG['schedule']['quiet_hours_end']
        
        if start > end:
            return hour >= start or hour < end
        else:
            return start <= hour < end
    
    @staticmethod
    def _strip_formatting(text: str) -> str:
        """Remove Markdown formatting"""
        # Remove markdown characters
        for char in ['*', '_', '`', '~']:
            text = text.replace(char, '')
        # Fix escaped characters
        text = text.replace('\\', '')
        return text


# ============================================================================
# CELL 17: ORCHESTRATOR
# ============================================================================
# Description: Main orchestration class that coordinates all scrapers
# Controls the entire scraping pipeline
# ============================================================================

class JobScraperOrchestrator:
    """Main orchestrator for job scraping"""
    
    def __init__(self):
        self.logger = LogManager.get_logger('Orchestrator')
        
        # Initialize components
        self.db = DatabaseManager()
        self.proxy_manager = ProxyManager()
        self.http_client = HTTPClient(self.proxy_manager)
        self.browser_manager = BrowserManager(self.proxy_manager)
        self.telegram = TelegramPoster()
        
        # Initialize scrapers
        self.linkedin_scraper = LinkedInScraper(
            self.db, self.proxy_manager, self.http_client, self.browser_manager
        )
        self.indeed_scraper = IndeedScraper(
            self.db, self.proxy_manager, self.http_client, self.browser_manager
        )
        self.naukri_scraper = NaukriScraper(
            self.db, self.proxy_manager, self.http_client, self.browser_manager
        )
        self.superset_scraper = SupersetScraper(
            self.db, self.proxy_manager, self.http_client, self.browser_manager
        )
        
        self._running = False
    
    def initialize(self) -> bool:
        """Initialize all components"""
        self.logger.info("=" * 60)
        self.logger.info("INITIALIZING JOB SCRAPER BOT")
        self.logger.info("=" * 60)

        # Validate config (warn but don't fail if Telegram not configured)
        is_valid, errors = validate_config()
        if not is_valid:
            for error in errors:
                self.logger.warning(f"Config warning: {error}")
            self.logger.info("Initializing with warnings (some features may not work)")

        # Note: Environment is already setup in global initialize() function

        # Initialize proxies
        if CONFIG['proxy']['enabled']:
            proxy_count = self.proxy_manager.initialize()
            self.logger.info(f"Proxy pool: {proxy_count} working proxies")
        
        # Test Telegram
        if CONFIG['telegram']['enabled']:
            if self.telegram.test_connection():
                self.logger.info("Telegram connection OK")
            else:
                self.logger.warning("Telegram connection failed")
        
        self.logger.info("Initialization complete!")
        return True
    
    def run_once(self) -> ScrapingStats:
        """Run single scraping cycle"""
        stats = ScrapingStats()
        self._running = True
        
        self.logger.info("=" * 60)
        self.logger.info("STARTING SCRAPING RUN")
        self.logger.info("=" * 60)
        
        all_jobs = []
        
        try:
            # Scrape LinkedIn
            if CONFIG['linkedin']['enabled']:
                linkedin_jobs = self.linkedin_scraper.scrape_all()
                all_jobs.extend(linkedin_jobs)
                linkedin_stats = self.linkedin_scraper.get_stats()
                stats.linkedin_jobs = linkedin_stats['found']
                stats.linkedin_errors = linkedin_stats['errors']
            
            # Scrape Indeed
            if CONFIG['indeed']['enabled']:
                indeed_jobs = self.indeed_scraper.scrape_all()
                all_jobs.extend(indeed_jobs)
                indeed_stats = self.indeed_scraper.get_stats()
                stats.indeed_jobs = indeed_stats['found']
                stats.indeed_errors = indeed_stats['errors']
            
            # Scrape Naukri
            if CONFIG['naukri']['enabled']:
                naukri_jobs = self.naukri_scraper.scrape_all()
                all_jobs.extend(naukri_jobs)
                naukri_stats = self.naukri_scraper.get_stats()
                stats.naukri_jobs = naukri_stats['found']
                stats.naukri_errors = naukri_stats['errors']
            
            # Scrape Superset
            if CONFIG['superset']['enabled']:
                superset_jobs = self.superset_scraper.scrape_all()
                all_jobs.extend(superset_jobs)
                superset_stats = self.superset_scraper.get_stats()
                stats.superset_jobs = superset_stats['found']
                stats.superset_errors = superset_stats['errors']
            
            # Save all jobs
            self.logger.info(f"Total jobs found: {len(all_jobs)}")
            for job in all_jobs:
                if self.db.save_job(job):
                    if job.source == 'linkedin':
                        stats.linkedin_new += 1
                    elif job.source == 'indeed':
                        stats.indeed_new += 1
                    elif job.source == 'naukri':
                        stats.naukri_new += 1
                    elif job.source == 'superset':
                        stats.superset_new += 1
            
            self.logger.info(f"New jobs saved: {stats.total_new}")
            
            # Post to Telegram
            if CONFIG['telegram']['enabled']:
                unposted = self.db.get_unposted_jobs(CONFIG['telegram']['batch_size'])
                for job in unposted:
                    msg_id = self.telegram.post_job(job)
                    if msg_id:
                        self.db.mark_as_posted(job.id, msg_id)
                        stats.jobs_posted += 1
                    else:
                        stats.posting_errors += 1
            
            # Export data
            if CONFIG['data']['export_after_each_run']:
                if CONFIG['data']['export_csv']:
                    self.db.export_to_csv()
                if CONFIG['data']['export_json']:
                    self.db.export_to_json()
            
            # Cleanup old jobs
            self.db.cleanup_old_jobs()
            
            # Send summary
            stats.end_time = datetime.now()
            self.telegram.send_summary(stats)
            
        except Exception as e:
            self.logger.error(f"Run failed with error: {e}")
            self.telegram.send_error(str(e))
        finally:
            self.browser_manager.quit_all()
            self._running = False
        
        self.logger.info("=" * 60)
        self.logger.info(f"SCRAPING RUN COMPLETE - {stats.total_new} new jobs")
        self.logger.info("=" * 60)
        
        return stats
    
    def run_continuous(self):
        """Run scraping continuously with intervals"""
        self.logger.info("Starting continuous scraping mode...")
        
        while True:
            try:
                self.run_once()
                
                interval_hours = CONFIG['schedule']['run_interval_hours']
                self.logger.info(f"Sleeping for {interval_hours} hours until next run...")
                time.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                self.logger.info("Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Continuous run error: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            'running': self._running,
            'proxy_stats': self.proxy_manager.get_stats(),
            'db_stats': self.db.get_stats(),
        }
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down...")
        self.browser_manager.quit_all()
        
        # Final export
        self.db.export_to_csv()
        self.db.export_to_json()
        
        self.logger.info("Shutdown complete")


# ============================================================================
# CELL 18: UTILITY FUNCTIONS
# ============================================================================
# Description: Helper functions for interactive use
# Use these to test, debug, and manage the scraper
# ============================================================================

# Global orchestrator instance
orchestrator = None

def initialize():
    """Initialize the scraper"""
    global orchestrator
    # Setup environment (create directories) before initializing anything else
    setup_environment()
    LogManager().setup()
    orchestrator = JobScraperOrchestrator()
    return orchestrator.initialize()

def run():
    """Run single scraping cycle"""
    if not orchestrator:
        initialize()
    return orchestrator.run_once()

def run_continuous():
    """Run continuously"""
    if not orchestrator:
        initialize()
    orchestrator.run_continuous()

def show_stats():
    """Display database statistics"""
    if not orchestrator:
        initialize()
    stats = orchestrator.db.get_stats()
    print("\n📊 DATABASE STATISTICS")
    print("=" * 40)
    print(f"Total Jobs: {stats['total_jobs']}")
    print(f"Unposted: {stats['unposted']}")
    print(f"Today: {stats['today']}")
    print("\nBy Source:")
    for source, count in stats.get('by_source', {}).items():
        print(f"  {source}: {count}")

def show_recent_jobs(limit: int = 20):
    """Display recent jobs"""
    if not orchestrator:
        initialize()
    
    jobs = orchestrator.db.get_unposted_jobs(limit)
    print(f"\n📋 RECENT JOBS ({len(jobs)})")
    print("=" * 60)
    for job in jobs:
        print(f"\n🔹 {job.title}")
        print(f"   🏢 {job.company} | 📍 {job.location}")
        print(f"   📎 Source: {job.source} | 🔗 {job.url[:50]}...")

def test_linkedin():
    """Test LinkedIn scraper"""
    if not orchestrator:
        initialize()
    jobs = orchestrator.linkedin_scraper.scrape_all()
    print(f"Found {len(jobs)} LinkedIn jobs")
    return jobs

def test_indeed():
    """Test Indeed scraper"""
    if not orchestrator:
        initialize()
    jobs = orchestrator.indeed_scraper.scrape_all()
    print(f"Found {len(jobs)} Indeed jobs")
    return jobs

def test_naukri():
    """Test Naukri scraper"""
    if not orchestrator:
        initialize()
    jobs = orchestrator.naukri_scraper.scrape_all()
    print(f"Found {len(jobs)} Naukri jobs")
    return jobs

def test_superset():
    """Test Superset scraper"""
    if not orchestrator:
        initialize()
    jobs = orchestrator.superset_scraper.scrape_all()
    print(f"Found {len(jobs)} Superset jobs")
    return jobs

def test_telegram():
    """Send test message to Telegram"""
    if not orchestrator:
        initialize()
    
    test_job = Job(
        id="test123",
        title="Software Engineer (Test)",
        company="Test Company",
        location="Bangalore",
        source="test",
        url="https://example.com",
        experience="0-2 years",
        salary="5-10 LPA",
    )
    
    msg_id = orchestrator.telegram.post_job(test_job)
    if msg_id:
        print(f"✅ Test message sent! Message ID: {msg_id}")
    else:
        print("❌ Failed to send test message")

def export_all():
    """Export all data"""
    if not orchestrator:
        initialize()
    csv_path = orchestrator.db.export_to_csv()
    json_path = orchestrator.db.export_to_json()
    print(f"✅ Exported to:\n  CSV: {csv_path}\n  JSON: {json_path}")

def force_post_all():
    """Force post all unposted jobs"""
    if not orchestrator:
        initialize()
    
    unposted = orchestrator.db.get_unposted_jobs(100)
    print(f"Posting {len(unposted)} jobs...")
    
    for job in unposted:
        msg_id = orchestrator.telegram.post_job(job)
        if msg_id:
            orchestrator.db.mark_as_posted(job.id, msg_id)
            print(f"✅ Posted: {job.title}")
        else:
            print(f"❌ Failed: {job.title}")

def cleanup(days: int = 30):
    """Cleanup old jobs"""
    if not orchestrator:
        initialize()
    deleted = orchestrator.db.cleanup_old_jobs(days)
    print(f"🗑️ Deleted {deleted} jobs older than {days} days")

def search_jobs(query: str) -> List[Job]:
    """Search jobs in database"""
    if not orchestrator:
        initialize()
    
    conn = orchestrator.db._get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM jobs 
        WHERE title LIKE ? OR company LIKE ? OR location LIKE ?
        ORDER BY scraped_at DESC LIMIT 50
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    rows = cursor.fetchall()
    conn.close()
    
    jobs = [orchestrator.db._row_to_job(row) for row in rows]
    print(f"Found {len(jobs)} jobs matching '{query}'")
    return jobs

def get_job_by_company(company: str) -> List[Job]:
    """Get all jobs from a specific company"""
    if not orchestrator:
        initialize()
    
    conn = orchestrator.db._get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM jobs 
        WHERE company LIKE ?
        ORDER BY scraped_at DESC
    ''', (f'%{company}%',))
    rows = cursor.fetchall()
    conn.close()
    
    jobs = [orchestrator.db._row_to_job(row) for row in rows]
    print(f"Found {len(jobs)} jobs from '{company}'")
    return jobs

def shutdown():
    """Graceful shutdown"""
    if orchestrator:
        orchestrator.shutdown()
    print("👋 Goodbye!")


# ============================================================================
# CELL 19: COLAB KEEP-ALIVE
# ============================================================================
# Description: Prevents Google Colab from disconnecting
# Run this cell if running long continuous scraping sessions
# ============================================================================

def keep_alive():
    """Keep Colab session alive"""
    try:
        from IPython.display import display, HTML
        
        display(HTML('''
            <script>
                function KeepAlive() {
                    console.log("Keeping alive at " + new Date());
                    google.colab.kernel.invokeFunction('shell', ['echo "alive"'], {});
                }
                setInterval(KeepAlive, 60000);
            </script>
            <p>✅ Keep-alive enabled! Session will stay active.</p>
        '''))
        print("Keep-alive script injected successfully!")
    except Exception as e:
        print(f"Keep-alive setup failed (not in Colab?): {e}")


def setup_colab_display():
    """Setup better display for Colab"""
    try:
        from IPython.display import display, HTML
        
        display(HTML('''
            <style>
                .output_text { font-family: 'Monaco', monospace; }
            </style>
        '''))
    except:
        pass


# ============================================================================
# CELL 20: MAIN EXECUTION BLOCK
# ============================================================================
# Description: Entry point for the scraper
# Uncomment the desired execution mode below
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║           MULTI-PLATFORM JOB SCRAPER BOT v1.0                 ║
    ║      LinkedIn | Indeed | Naukri | Superset → Telegram         ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                                ║
    ║  🚀 QUICK START:                                              ║
    ║     1. Update CONFIG with your Telegram bot token             ║
    ║     2. Run: initialize()                                      ║
    ║     3. Run: run() for single cycle                            ║
    ║                                                                ║
    ║  📋 COMMANDS:                                                  ║
    ║     initialize()      - Setup the scraper                     ║
    ║     run()             - Single scraping cycle                 ║
    ║     run_continuous()  - Run with intervals                    ║
    ║     show_stats()      - Database statistics                   ║
    ║     show_recent_jobs()- Display recent jobs                   ║
    ║     test_linkedin()   - Test LinkedIn only                    ║
    ║     test_indeed()     - Test Indeed only                      ║
    ║     test_naukri()     - Test Naukri only                      ║
    ║     test_telegram()   - Send test message                     ║
    ║     export_all()      - Export to CSV/JSON                    ║
    ║     search_jobs("...")- Search database                       ║
    ║     cleanup(30)       - Remove old jobs                       ║
    ║     shutdown()        - Graceful shutdown                     ║
    ║                                                                ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # ─────────────────────────────────────────────────────────────────
    # UNCOMMENT ONE OF THESE TO RUN:
    # ─────────────────────────────────────────────────────────────────
    
    # Option 1: Initialize only (for interactive use in Colab)
    # initialize()
    
    # Option 2: Single run
    # initialize()
    # run()
    
    # Option 3: Continuous mode (runs every X hours)
    # initialize()
    # keep_alive()  # Enable for Colab
    # run_continuous()
    
    # Option 4: Test individual scrapers
    # initialize()
    # test_linkedin()
    # test_indeed()
    # test_naukri()
