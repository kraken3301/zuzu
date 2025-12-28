# ============================================================================
# BASE SCRAPER - Abstract Base Class for All Scrapers
# ============================================================================

import re
import time
import random
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

from core.models import Job, ScraperError, RateLimitError, BlockedError
from core.config import CONFIG
from core.log_manager import LogManager
from core.database_manager import DatabaseManager
from core.proxy_manager import ProxyManager
from core.http_client import HTTPClient
from core.browser_manager import BrowserManager


class BaseScraper(ABC):
    """Abstract base class for all job scrapers"""
    
    def __init__(self, db: DatabaseManager, proxy_manager: ProxyManager, 
                 http_client: HTTPClient, browser_manager: BrowserManager):
        self.db = db
        self.proxy_manager = proxy_manager
        self.http_client = http_client
        self.browser_manager = browser_manager
        self.logger = LogManager.get_logger(self.__class__.__name__)
        self.name = self.__class__.__name__.replace('Scraper', '').lower()
    
    @abstractmethod
    def scrape(self) -> List[Job]:
        """Main scraping method - to be implemented by each scraper"""
        pass
    
    def _filter_job(self, job: Job) -> bool:
        """Filter job based on configuration"""
        # Check title for excluded keywords
        title_lower = job.title.lower()
        for keyword in CONFIG['filters']['exclude_title_keywords']:
            if keyword.lower() in title_lower:
                self.logger.debug(f"Filtered out job with excluded keyword '{keyword}': {job.title}")
                return False
        
        # Check company exclusions
        if job.company and any(excluded in job.company for excluded in CONFIG['filters']['exclude_companies']):
            self.logger.debug(f"Filtered out job from excluded company: {job.company}")
            return False
        
        # Check experience requirements
        if self._extract_experience_years(job) > CONFIG['filters']['max_experience_years']:
            self.logger.debug(f"Filtered out job requiring too much experience: {job.title}")
            return False
        
        return True
    
    def _extract_experience_years(self, job: Job) -> float:
        """Extract experience requirement in years from job"""
        experience_text = (job.experience or "").lower()
        
        # Look for patterns like "1-2 years", "3+ years", etc.
        patterns = [
            r'(\d+)\s*-\s*(\d+)\s+years?',  # 1-2 years
            r'(\d+)\s*\+?\s+years?',         # 3 years, 3+ years
            r'(\d+)\s+year',                  # 1 year
            r'fresher|entry level|trainee|graduate',  # 0 years
        ]
        
        for pattern in patterns:
            match = re.search(pattern, experience_text)
            if match:
                if pattern == patterns[0]:  # Range pattern
                    min_years = float(match.group(1))
                    max_years = float(match.group(2))
                    return (min_years + max_years) / 2
                elif pattern == patterns[1]:  # Single number
                    return float(match.group(1))
                elif pattern == patterns[3]:  # Fresher keywords
                    return 0.0
        
        # Default to 0 if no experience specified
        return 0.0
    
    def _parse_job_from_html(self, html: str, source: str, url: str) -> Optional[Job]:
        """Parse job from HTML content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                return None
            
            # Extract company
            company = self._extract_company(soup)
            if not company:
                return None
            
            # Extract location
            location = self._extract_location(soup) or "Remote"
            
            # Extract description
            description = self._extract_description(soup) or ""
            
            # Create job object
            job = Job(
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                url=url,
                source=source,
                description=description.strip(),
                posted_date=self._extract_posted_date(soup) or "",
                experience=self._extract_experience(soup) or "",
                salary=self._extract_salary(soup) or "",
                is_remote='remote' in location.lower()
            )
            
            return job if self._filter_job(job) else None
            
        except Exception as e:
            self.logger.error(f"Failed to parse job from {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job title from HTML"""
        # Try common title selectors
        selectors = [
            'h1',
            'h2',
            'h3',
            '[class*="title"]',
            '[class*="job-title"]',
            '[itemprop="title"]',
            '[property="og:title"]',
            'meta[name="title"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_company(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from HTML"""
        selectors = [
            '[class*="company"]',
            '[class*="employer"]',
            '[itemprop="hiringOrganization"]',
            '[itemprop="name"]',
            'meta[property="og:company"]',
            'meta[name="company"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job location from HTML"""
        selectors = [
            '[class*="location"]',
            '[class*="where"]',
            '[itemprop="jobLocation"]',
            '[itemprop="address"]',
            'meta[property="og:location"]',
            'meta[name="location"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job description from HTML"""
        selectors = [
            '[class*="description"]',
            '[class*="job-description"]',
            '[itemprop="description"]',
            '[class*="content"]',
            'div[class*="job"] p'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator='\n', strip=True)
        
        return None
    
    def _extract_posted_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract posted date from HTML"""
        selectors = [
            '[class*="date"]',
            '[class*="posted"]',
            '[class*="time"]',
            'time',
            'meta[property="article:published_time"]',
            'meta[name="published"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True) or element.get('datetime', '')
        
        return None
    
    def _extract_experience(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract experience requirement from HTML"""
        selectors = [
            '[class*="experience"]',
            '[class*="exp"]',
            'li:contains("experience")',
            'li:contains("years")'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_salary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract salary from HTML"""
        selectors = [
            '[class*="salary"]',
            '[class*="pay"]',
            '[class*="compensation"]',
            '[itemprop="baseSalary"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _random_delay(self) -> None:
        """Add random delay between requests"""
        delay = random.uniform(
            CONFIG['scraping']['request_delay_min'],
            CONFIG['scraping']['request_delay_max']
        )
        time.sleep(delay)
    
    def _handle_rate_limit(self, e: Exception, url: str) -> None:
        """Handle rate limiting errors"""
        if isinstance(e, RateLimitError):
            self.logger.warning(f"Rate limited on {url}, waiting before retry")
            time.sleep(random.uniform(30, 60))
        elif "rate limit" in str(e).lower():
            self.logger.warning(f"Rate limit detected on {url}, waiting before retry")
            time.sleep(random.uniform(15, 30))
    
    def _handle_blocked(self, e: Exception, url: str) -> None:
        """Handle blocked errors"""
        if isinstance(e, BlockedError):
            self.logger.error(f"Blocked by {url}, trying without proxy")
            # Switch to no proxy for this domain
            self.proxy_manager.report_failure(None, urlparse(url).netloc, e)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        return text.strip()