# ============================================================================
# LINKEDIN SCRAPER - Scrape LinkedIn Job Listings
# ============================================================================

import re
import time
import random
import json
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup

from core.models import Job, ScraperError, RateLimitError, BlockedError
from core.config import CONFIG
from core.log_manager import LogManager
from core.database_manager import DatabaseManager
from core.proxy_manager import ProxyManager
from core.http_client import HTTPClient
from core.browser_manager import BrowserManager
from .base_scraper import BaseScraper


class LinkedInScraper(BaseScraper):
    """Scrape job listings from LinkedIn"""
    
    BASE_URL = "https://www.linkedin.com"
    SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings"
    
    # Flexible selectors using regex patterns
    CARD_SELECTORS = [
        'div.base-card',
        'div.job-card',
        'li.job-result-card',
        'div[class*="job"]',
        'div[class*="card"]'
    ]
    
    TITLE_SELECTORS = [
        'h3.base-card__title',
        'h3.job-card__title',
        'h3[class*="title"]',
        'a.job-card-list__title'
    ]
    
    COMPANY_SELECTORS = [
        'h4.base-card__subtitle',
        'span.job-card__subtitle',
        'span[class*="company"]',
        'a.job-card__company'
    ]
    
    LOCATION_SELECTORS = [
        'span.job-card__location',
        'span[class*="location"]',
        'li.job-card__location'
    ]
    
    DATE_SELECTORS = [
        'time.job-card__listdate',
        'time[class*="date"]',
        'span.job-card__listdate'
    ]
    
    def __init__(self, db: DatabaseManager, proxy_manager: ProxyManager, 
                 http_client: HTTPClient, browser_manager: BrowserManager):
        super().__init__(db, proxy_manager, http_client, browser_manager)
        self._circuit_breaker_triggered = False
        self._circuit_breaker_until = 0
    
    def scrape(self) -> List[Job]:
        """Main scraping method"""
        jobs = []
        
        if not CONFIG['linkedin']['enabled']:
            self.logger.info("LinkedIn scraper disabled")
            return jobs
        
        self.logger.info(f"Starting LinkedIn scraping...")
        
        try:
            # Check circuit breaker
            if self._circuit_breaker_triggered:
                if time.time() < self._circuit_breaker_until:
                    self.logger.warning(f"Circuit breaker active, skipping LinkedIn until {self._circuit_breaker_until}")
                    return jobs
                else:
                    self._circuit_breaker_triggered = False
                    self.logger.info("Circuit breaker reset, resuming LinkedIn scraping")
            
            # Scrape using guest API
            jobs = self._scrape_guest_api()
            
            # If guest API fails or returns few results, try browser-based scraping
            if len(jobs) < 10:
                self.logger.info("Guest API returned few results, trying browser-based scraping")
                browser_jobs = self._scrape_with_browser()
                jobs.extend(browser_jobs)
            
            self.logger.info(f"LinkedIn scraping completed: {len(jobs)} jobs found")
            return jobs
            
        except Exception as e:
            self.logger.error(f"LinkedIn scraping failed: {e}")
            self._trigger_circuit_breaker()
            return []
    
    def _scrape_guest_api(self) -> List[Job]:
        """Scrape using LinkedIn guest API"""
        jobs = []
        
        for keyword in CONFIG['linkedin']['keywords']:
            for location in CONFIG['linkedin']['locations']:
                try:
                    params = {
                        'keywords': keyword,
                        'location': location,
                        'f_TPR': ','.join(map(str, CONFIG['linkedin']['experience_levels'])),
                        'f_WT': CONFIG['linkedin']['time_posted'],
                        'start': 0
                    }
                    
                    url = f"{self.SEARCH_URL}?{urlencode(params)}"
                    
                    self.logger.debug(f"Fetching LinkedIn jobs: {keyword} in {location}")
                    
                    response = self.http_client.get(url)
                    
                    if response.status_code != 200:
                        self.logger.warning(f"LinkedIn API request failed: {response.status_code}")
                        continue
                    
                    data = response.json()
                    
                    # Check for empty results (potential blocking)
                    if not data.get('elements') or len(data['elements']) == 0:
                        self.logger.warning(f"Empty results for {keyword} in {location} - potential blocking")
                        continue
                    
                    # Parse jobs
                    for job_data in data['elements']:
                        job = self._parse_api_job(job_data)
                        if job and self._filter_job(job):
                            jobs.append(job)
                    
                    # Random delay between searches
                    self._random_delay()
                    
                except Exception as e:
                    self.logger.error(f"Error scraping LinkedIn for {keyword} in {location}: {e}")
                    self._handle_rate_limit(e, url)
        
        return jobs
    
    def _parse_api_job(self, job_data: Dict[str, Any]) -> Optional[Job]:
        """Parse job from LinkedIn API response"""
        try:
            # Extract basic info
            title = job_data.get('title', '')
            company = job_data.get('companyName', '')
            location = job_data.get('formattedLocation', '')
            url = job_data.get('jobUrl', '')
            
            if not title or not company or not url:
                return None
            
            # Clean URL
            if not url.startswith('http'):
                url = f"https://www.linkedin.com{url}"
            
            # Extract additional info
            posted_date = job_data.get('listedAt', '')
            experience = job_data.get('formattedExperience', '')
            
            # Create job object
            job = Job(
                title=self._clean_text(title),
                company=self._clean_text(company),
                location=self._clean_text(location) or "Remote",
                url=url,
                source='linkedin',
                posted_date=self._format_posted_date(posted_date),
                experience=self._clean_text(experience),
                is_remote='remote' in (location or '').lower()
            )
            
            # Get full description (requires separate request)
            try:
                job.description = self._get_job_description(url)
            except Exception as e:
                self.logger.debug(f"Could not get description for {url}: {e}")
                job.description = ""
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to parse LinkedIn API job: {e}")
            return None
    
    def _get_job_description(self, url: str) -> str:
        """Get full job description from job page"""
        try:
            response = self.http_client.get(url)
            
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try flexible description selectors
            description = ""
            for selector in [
                'div.description',
                'div.job-description',
                'div[class*="description"]',
                'div[class*="job"] p',
                'div[class*="content"]'
            ]:
                elements = soup.select(selector)
                if elements:
                    description = ' '.join([el.get_text(strip=True) for el in elements])
                    break
            
            return self._clean_text(description)
            
        except Exception as e:
            self.logger.debug(f"Error getting job description: {e}")
            return ""
    
    def _scrape_with_browser(self) -> List[Job]:
        """Scrape using browser automation (fallback method)"""
        jobs = []
        
        try:
            browser = self.browser_manager.get_browser()
            
            for keyword in random.sample(CONFIG['linkedin']['keywords'], min(3, len(CONFIG['linkedin']['keywords']))):
                for location in random.sample(CONFIG['linkedin']['locations'], min(2, len(CONFIG['linkedin']['locations']))):
                    try:
                        # Search URL
                        search_url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}&location={quote_plus(location)}"
                        
                        browser.get(search_url)
                        time.sleep(random.uniform(3, 5))
                        
                        # Accept cookies if needed
                        self._accept_cookies(browser)
                        
                        # Scroll to load more jobs
                        self._scroll_page(browser)
                        
                        # Parse job cards
                        soup = BeautifulSoup(browser.page_source, 'html.parser')
                        job_cards = self._find_job_cards(soup)
                        
                        for card in job_cards:
                            job = self._parse_job_card(card)
                            if job and self._filter_job(job):
                                jobs.append(job)
                        
                        # Random delay
                        self._random_delay()
                        
                    except Exception as e:
                        self.logger.error(f"Browser scraping failed for {keyword} in {location}: {e}")
                        continue
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Browser scraping failed: {e}")
            return []
        finally:
            self.browser_manager.close_browser()
    
    def _find_job_cards(self, soup: BeautifulSoup) -> List[Any]:
        """Find job cards using flexible selectors"""
        for selector in self.CARD_SELECTORS:
            cards = soup.select(selector)
            if cards:
                return cards
        return []
    
    def _parse_job_card(self, card: Any) -> Optional[Job]:
        """Parse job from card element"""
        try:
            # Extract title
            title = self._extract_title_from_card(card)
            if not title:
                return None
            
            # Extract company
            company = self._extract_company_from_card(card)
            if not company:
                return None
            
            # Extract location
            location = self._extract_location_from_card(card) or "Remote"
            
            # Extract URL
            url = self._extract_url_from_card(card)
            if not url:
                return None
            
            # Create job object
            job = Job(
                title=self._clean_text(title),
                company=self._clean_text(company),
                location=self._clean_text(location),
                url=url,
                source='linkedin',
                is_remote='remote' in location.lower()
            )
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to parse job card: {e}")
            return None
    
    def _extract_title_from_card(self, card: Any) -> Optional[str]:
        """Extract title from job card using flexible selectors"""
        for selector in self.TITLE_SELECTORS:
            element = card.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None
    
    def _extract_company_from_card(self, card: Any) -> Optional[str]:
        """Extract company from job card using flexible selectors"""
        for selector in self.COMPANY_SELECTORS:
            element = card.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None
    
    def _extract_location_from_card(self, card: Any) -> Optional[str]:
        """Extract location from job card using flexible selectors"""
        for selector in self.LOCATION_SELECTORS:
            element = card.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None
    
    def _extract_url_from_card(self, card: Any) -> Optional[str]:
        """Extract URL from job card"""
        # Try to find link in card
        link = card.select_one('a[href]')
        if link and link['href']:
            url = link['href']
            if not url.startswith('http'):
                url = f"https://www.linkedin.com{url}"
            return url
        return None
    
    def _accept_cookies(self, browser: Any) -> None:
        """Accept cookies if cookie banner is present"""
        try:
            # Try different cookie button selectors
            selectors = [
                'button[class*="cookie"]',
                'button[class*="accept"]',
                'button[class*="agree"]',
                'button[aria-label*="cookie"]',
                'button[aria-label*="accept"]'
            ]
            
            for selector in selectors:
                button = self.browser_manager.safe_find_element(browser, selector)
                if button:
                    self.browser_manager.human_like_click(button)
                    time.sleep(1)
                    return
        except Exception:
            pass
    
    def _scroll_page(self, browser: Any) -> None:
        """Scroll page to load more jobs"""
        try:
            # Scroll multiple times
            for _ in range(3):
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 2))
        except Exception:
            pass
    
    def _format_posted_date(self, posted_date: str) -> str:
        """Format posted date for display"""
        if not posted_date:
            return ""
        
        # Convert LinkedIn timestamp to readable format
        try:
            timestamp = int(posted_date)
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except:
            return posted_date
    
    def _trigger_circuit_breaker(self) -> None:
        """Trigger circuit breaker to prevent excessive requests"""
        self._circuit_breaker_triggered = True
        self._circuit_breaker_until = time.time() + 3600  # 1 hour
        self.logger.warning("Circuit breaker triggered - pausing LinkedIn scraping for 1 hour")