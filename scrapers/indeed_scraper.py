# ============================================================================
# INDEED SCRAPER - Scrape Indeed Job Listings
# ============================================================================

import re
import time
import random
import feedparser
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup

from core.models import Job, ScraperError
from core.config import CONFIG
from core.log_manager import LogManager
from core.database_manager import DatabaseManager
from core.proxy_manager import ProxyManager
from core.http_client import HTTPClient
from core.browser_manager import BrowserManager
from .base_scraper import BaseScraper


class IndeedScraper(BaseScraper):
    """Scrape job listings from Indeed"""
    
    BASE_URL = "https://www.indeed.com"
    SEARCH_URL = "https://www.indeed.com/jobs"
    RSS_URL = "https://www.indeed.com/rss"
    
    def __init__(self, db: DatabaseManager, proxy_manager: ProxyManager, 
                 http_client: HTTPClient, browser_manager: BrowserManager):
        super().__init__(db, proxy_manager, http_client, browser_manager)
    
    def scrape(self) -> List[Job]:
        """Main scraping method"""
        jobs = []
        
        if not CONFIG['indeed']['enabled']:
            self.logger.info("Indeed scraper disabled")
            return jobs
        
        self.logger.info("Starting Indeed scraping...")
        
        try:
            # Try RSS first (more reliable)
            if CONFIG['indeed']['use_rss']:
                jobs = self._scrape_rss()
            
            # If RSS fails or returns few results, try HTML scraping
            if len(jobs) < 10:
                self.logger.info("RSS returned few results, trying HTML scraping")
                html_jobs = self._scrape_html()
                jobs.extend(html_jobs)
            
            self.logger.info(f"Indeed scraping completed: {len(jobs)} jobs found")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Indeed scraping failed: {e}")
            return []
    
    def _scrape_rss(self) -> List[Job]:
        """Scrape jobs using Indeed RSS feeds"""
        jobs = []
        
        for keyword in CONFIG['indeed']['keywords']:
            for location in CONFIG['indeed']['locations']:
                try:
                    # Build RSS URL
                    params = {
                        'q': keyword,
                        'l': location,
                        'sort': 'date',
                        'fromage': CONFIG['indeed']['posted_days'],
                        'radius': 25,
                        'limit': 50
                    }
                    
                    rss_url = f"{self.RSS_URL}?{urlencode(params)}"
                    
                    self.logger.debug(f"Fetching Indeed RSS: {keyword} in {location}")
                    
                    # Parse RSS feed
                    feed = feedparser.parse(rss_url)
                    
                    if not feed.entries:
                        self.logger.warning(f"No RSS entries found for {keyword} in {location}")
                        continue
                    
                    # Parse jobs from RSS
                    for entry in feed.entries:
                        job = self._parse_rss_entry(entry)
                        if job and self._filter_job(job):
                            jobs.append(job)
                    
                    # Random delay
                    self._random_delay()
                    
                except Exception as e:
                    self.logger.error(f"Error scraping Indeed RSS for {keyword} in {location}: {e}")
                    continue
        
        return jobs
    
    def _parse_rss_entry(self, entry: Dict[str, Any]) -> Optional[Job]:
        """Parse job from RSS entry"""
        try:
            # Extract basic info
            title = entry.get('title', '')
            company = entry.get('author', '')
            url = entry.get('link', '')
            
            if not title or not url:
                return None
            
            # Extract location from title (Indeed RSS includes location in title)
            location = self._extract_location_from_title(title)
            
            # Extract description
            description = entry.get('description', '') or entry.get('summary', '')
            
            # Create job object
            job = Job(
                title=self._clean_text(title),
                company=self._clean_text(company),
                location=self._clean_text(location) or "Remote",
                url=url,
                source='indeed',
                description=self._clean_text(description),
                is_remote='remote' in (location or '').lower()
            )
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to parse Indeed RSS entry: {e}")
            return None
    
    def _extract_location_from_title(self, title: str) -> str:
        """Extract location from Indeed job title"""
        # Indeed RSS format: "Job Title - Company - Location"
        parts = title.split(' - ')
        if len(parts) >= 3:
            return parts[2]
        
        # Try to find location in parentheses
        match = re.search(r'\(([^)]+)\)', title)
        if match:
            return match.group(1)
        
        return ""
    
    def _scrape_html(self) -> List[Job]:
        """Scrape jobs using HTML parsing"""
        jobs = []
        
        for keyword in random.sample(CONFIG['indeed']['keywords'], min(3, len(CONFIG['indeed']['keywords']))):
            for location in random.sample(CONFIG['indeed']['locations'], min(2, len(CONFIG['indeed']['locations']))):
                try:
                    # Build search URL
                    params = {
                        'q': keyword,
                        'l': location,
                        'sort': 'date',
                        'fromage': CONFIG['indeed']['posted_days'],
                        'radius': 25,
                        'limit': 50
                    }
                    
                    search_url = f"{self.SEARCH_URL}?{urlencode(params)}"
                    
                    self.logger.debug(f"Fetching Indeed HTML: {keyword} in {location}")
                    
                    response = self.http_client.get(search_url)
                    
                    if response.status_code != 200:
                        self.logger.warning(f"Indeed request failed: {response.status_code}")
                        continue
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find job cards
                    job_cards = soup.select('div.job_seen_beacon') or soup.select('div.jobresult')
                    
                    for card in job_cards:
                        job = self._parse_html_job_card(card)
                        if job and self._filter_job(job):
                            jobs.append(job)
                    
                    # Random delay
                    self._random_delay()
                    
                except Exception as e:
                    self.logger.error(f"Error scraping Indeed HTML for {keyword} in {location}: {e}")
                    continue
        
        return jobs
    
    def _parse_html_job_card(self, card: Any) -> Optional[Job]:
        """Parse job from HTML job card"""
        try:
            # Extract title
            title_element = card.select_one('h2.jobTitle') or card.select_one('h2.jobtitle')
            if not title_element:
                return None
            
            title = title_element.get_text(strip=True)
            
            # Extract URL
            url = self._extract_url_from_card(card)
            if not url:
                return None
            
            # Extract company
            company = self._extract_company_from_card(card)
            
            # Extract location
            location = self._extract_location_from_card(card) or "Remote"
            
            # Extract description (if available)
            description = self._extract_description_from_card(card)
            
            # Create job object
            job = Job(
                title=self._clean_text(title),
                company=self._clean_text(company),
                location=self._clean_text(location),
                url=url,
                source='indeed',
                description=self._clean_text(description),
                is_remote='remote' in location.lower()
            )
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to parse Indeed HTML job card: {e}")
            return None
    
    def _extract_url_from_card(self, card: Any) -> Optional[str]:
        """Extract URL from job card"""
        # Try to find link in title
        title_link = card.select_one('h2.jobTitle a') or card.select_one('h2.jobtitle a')
        if title_link and title_link.get('href'):
            url = title_link['href']
            if url.startswith('/'):
                url = f"https://www.indeed.com{url}"
            return url
        
        # Try to find link in card
        link = card.select_one('a[href]')
        if link and link.get('href'):
            url = link['href']
            if url.startswith('/'):
                url = f"https://www.indeed.com{url}"
            return url
        
        return None
    
    def _extract_company_from_card(self, card: Any) -> str:
        """Extract company from job card"""
        # Try company element
        company_element = card.select_one('span.companyName') or card.select_one('span.company')
        if company_element:
            return company_element.get_text(strip=True)
        
        # Try to extract from title
        title = card.select_one('h2.jobTitle') or card.select_one('h2.jobtitle')
        if title:
            title_text = title.get_text(strip=True)
            # Company is often after "- " in title
            if ' - ' in title_text:
                parts = title_text.split(' - ')
                if len(parts) > 1:
                    return parts[1].split(' - ')[0]  # Get company part
        
        return "Unknown Company"
    
    def _extract_location_from_card(self, card: Any) -> str:
        """Extract location from job card"""
        # Try location element
        location_element = card.select_one('div.companyLocation') or card.select_one('span.location')
        if location_element:
            return location_element.get_text(strip=True)
        
        # Try to extract from title
        title = card.select_one('h2.jobTitle') or card.select_one('h2.jobtitle')
        if title:
            title_text = title.get_text(strip=True)
            # Location is often the last part after "- "
            if ' - ' in title_text:
                parts = title_text.split(' - ')
                if len(parts) > 2:
                    return parts[2]
        
        return ""
    
    def _extract_description_from_card(self, card: Any) -> str:
        """Extract description from job card"""
        # Try summary element
        summary_element = card.select_one('div.job-snippet') or card.select_one('div.snippet')
        if summary_element:
            return summary_element.get_text(strip=True)
        
        return ""