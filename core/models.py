# ============================================================================
# CORE MODELS - Data Classes and Exceptions
# ============================================================================

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import datetime
import hashlib


@dataclass
class Job:
    """Represents a job posting"""
    title: str
    company: str
    location: str
    url: str
    source: str  # linkedin, indeed, naukri, superset
    id: str = ""
    description: str = ""
    posted_date: str = ""
    experience: str = ""
    salary: str = ""
    job_id: str = ""
    skills: List[str] = field(default_factory=list)
    keyword_matched: str = ""
    is_remote: bool = False
    is_fresh: bool = True
    scrape_timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return asdict(self)
    
    def generate_unique_id(self) -> str:
        """Generate unique ID for deduplication"""
        unique_str = f"{self.title}|{self.company}|{self.source}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    @staticmethod
    def generate_id(title: str, company: str, source: str) -> str:
        """Generate ID from title, company, and source"""
        unique_str = f"{title}|{company}|{source}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
    
    def to_telegram_message(self) -> str:
        """Format job for Telegram (MarkdownV2 compatible)"""
        # Escape special characters for MarkdownV2
        title = self._escape_markdown(self.title)
        company = self._escape_markdown(self.company)
        location = self._escape_markdown(self.location)
        
        # Build message
        message = f"🚨 NEW JOB ALERT\n\n📢 *{title}*\n"
        message += f"🏢 *{company}*\n"
        message += f"📍 *{location}*\n"
        
        if self.experience:
            message += f"💼 *Experience: {self._escape_markdown(self.experience)}*\n"
        
        if self.salary:
            message += f"💰 *Salary: {self._escape_markdown(self.salary)}*\n"
        
        if self.posted_date:
            message += f"📅 *Posted: {self._escape_markdown(self.posted_date)}*\n"
        
        if self.is_remote:
            message += "🌍 *Remote*\n"
        
        if self.description:
            # Truncate description and escape
            desc = self.description.strip()[:500]
            desc = self._escape_markdown(desc)
            message += f"\n{desc}"
        
        # Add source hashtags
        source_hashtags = {
            'linkedin': '\\#linkedin',
            'indeed': '\\#indeed',
            'naukri': '\\#naukri',
            'superset': '\\#superset'
        }
        
        hashtags = f"\n\n{source_hashtags.get(self.source, '')} \\#jobs \\#fresher \\#hiring"
        
        # Add URL at the end
        message += f"\n\n🔗 [Apply Now]({self.url}){hashtags}"
        
        return message
    
    def _escape_markdown(self, text: str) -> str:
        """Escape MarkdownV2 special characters"""
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text


@dataclass
class ScrapingStats:
    """Statistics for a scraping run"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Scraper counts
    linkedin_jobs: int = 0
    indeed_jobs: int = 0
    naukri_jobs: int = 0
    superset_jobs: int = 0
    
    # New job counts
    linkedin_new: int = 0
    indeed_new: int = 0
    naukri_new: int = 0
    superset_new: int = 0
    
    # Error counts
    linkedin_errors: int = 0
    indeed_errors: int = 0
    naukri_errors: int = 0
    superset_errors: int = 0
    
    # Database stats
    new_jobs: int = 0
    duplicate_jobs: int = 0
    total_jobs_in_db: int = 0
    
    # Telegram stats
    telegram_posts: int = 0
    telegram_errors: int = 0
    
    def duration_seconds(self) -> float:
        """Calculate duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def total_jobs(self) -> int:
        """Total jobs scraped"""
        return self.linkedin_jobs + self.indeed_jobs + self.naukri_jobs + self.superset_jobs
    
    def total_new(self) -> int:
        """Total new jobs"""
        return self.linkedin_new + self.indeed_new + self.naukri_new + self.superset_new
    
    def total_errors(self) -> int:
        """Total errors encountered"""
        return self.linkedin_errors + self.indeed_errors + self.naukri_errors + self.superset_errors
    
    def get_runtime(self) -> str:
        """Get formatted runtime"""
        seconds = int(self.duration_seconds())
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def get_summary(self) -> str:
        """Get summary string"""
        summary = []
        
        if self.linkedin_jobs > 0:
            summary.append(f"LinkedIn: {self.linkedin_jobs} ({self.linkedin_new} new)")
        if self.indeed_jobs > 0:
            summary.append(f"Indeed: {self.indeed_jobs} ({self.indeed_new} new)")
        if self.naukri_jobs > 0:
            summary.append(f"Naukri: {self.naukri_jobs} ({self.naukri_new} new)")
        if self.superset_jobs > 0:
            summary.append(f"Superset: {self.superset_jobs} ({self.superset_new} new)")
        
        return ", ".join(summary)


# Custom Exceptions
class ScraperError(Exception):
    """Base exception for scraper errors"""
    pass


class ProxyError(ScraperError):
    """Proxy-related errors"""
    pass


class RateLimitError(ScraperError):
    """Rate limiting errors"""
    pass


class AuthenticationError(ScraperError):
    """Authentication failures"""
    pass


class CaptchaError(ScraperError):
    """CAPTCHA challenges"""
    pass


class BlockedError(ScraperError):
    """IP/Account blocked"""
    pass