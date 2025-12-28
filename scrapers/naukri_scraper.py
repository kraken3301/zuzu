# ============================================================================
# NAUKRI SCRAPER - Scrape Naukri Job Listings
# ============================================================================

import re
import time
import random
import json
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


class NaukriScraper(BaseScraper):
    """Scrape job listings from Naukri"""
    
    BASE_URL = "https://www.naukri.com"
    SEARCH_URL = "https://www.naukri.com/jobapi/v3/search"
    MOBILE_SEARCH_URL = "https://www.naukri.com/mobileList"
    
    def __init__(self, db: DatabaseManager, proxy_manager: ProxyManager, 
                 http_client: HTTPClient, browser_manager: BrowserManager):
        super().__init__(db, proxy_manager, http_client, browser_manager)
    
    def scrape(self) -> List[Job]:
        """Main scraping method"""
        jobs = []
        
        if not CONFIG['naukri']['enabled']:
            self.logger.info("Naukri scraper disabled")
            return jobs
        
        self.logger.info("Starting Naukri scraping...")
        
        try:
            # Try mobile API first (more reliable)
            if CONFIG['naukri']['use_api']:
                jobs = self._scrape_mobile_api()
            
            # If API fails or returns few results, try HTML scraping
            if len(jobs) < 10:
                self.logger.info("Mobile API returned few results, trying HTML scraping")
                html_jobs = self._scrape_html()
                jobs.extend(html_jobs)
            
            self.logger.info(f"Naukri scraping completed: {len(jobs)} jobs found")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Naukri scraping failed: {e}")
            return []
    
    def _scrape_mobile_api(self) -> List[Job]:
        """Scrape jobs using Naukri mobile API"""
        jobs = []
        
        for keyword in CONFIG['naukri']['keywords']:
            for location in CONFIG['naukri']['locations']:
                try:
                    # Build API URL
                    params = {
                        'keyword': keyword,
                        'location': location,
                        'experience': f"{CONFIG['naukri']['experience_min']}-{CONFIG['naukri']['experience_max']}",
                        'freshness': CONFIG['naukri']['freshness'],
                        'pageNo': 1,
                        'noOfRecords': CONFIG['naukri']['results_per_page']
                    }
                    
                    api_url = f"{self.MOBILE_SEARCH_URL}?{urlencode(params)}"
                    
                    self.logger.debug(f"Fetching Naukri API: {keyword} in {location}")
                    
                    # Set headers for mobile API
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                        'Accept': 'application/json',
                        'Referer': 'https://www.naukri.com/',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    
                    response = self.http_client.get(api_url, headers=headers)
                    
                    if response.status_code != 200:
                        self.logger.warning(f"Naukri API request failed: {response.status_code}")
                        continue
                    
                    data = response.json()
                    
                    # Check for valid response
                    if not data.get('jobDetails') or len(data['jobDetails']) == 0:
                        self.logger.warning(f"Empty API response for {keyword} in {location}")
                        continue
                    
                    # Parse jobs
                    for job_data in data['jobDetails']:
                        job = self._parse_api_job(job_data)
                        if job and self._filter_job(job):
                            jobs.append(job)
                    
                    # Random delay
                    self._random_delay()
                    
                except Exception as e:
                    self.logger.error(f"Error scraping Naukri API for {keyword} in {location}: {e}")
                    continue
        
        return jobs
    
    def _parse_api_job(self, job_data: Dict[str, Any]) -> Optional[Job]:
        """Parse job from Naukri API response"""
        try:
            # Extract basic info
            title = job_data.get('title', '')
            company = job_data.get('companyName', '')
            location = job_data.get('location', '')
            url = job_data.get('jdURL', '')
            
            if not title or not company or not url:
                return None
            
            # Clean URL
            if not url.startswith('http'):
                url = f"https://www.naukri.com{url}"
            
            # Extract additional info
            experience = job_data.get('experience', '')
            salary = job_data.get('salary', '')
            posted_date = job_data.get('postedDate', '')
            
            # Create job object
            job = Job(
                title=self._clean_text(title),
                company=self._clean_text(company),
                location=self._clean_text(location) or "Remote",
                url=url,
                source='naukri',
                posted_date=self._format_posted_date(posted_date),
                experience=self._clean_text(experience),
                salary=self._clean_text(salary),
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
            self.logger.error(f"Failed to parse Naukri API job: {e}")
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
                'div.dang-in-desc',
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
    
    def _scrape_html(self) -> List[Job]:
        """Scrape jobs using HTML parsing"""
        jobs = []
        
        try:
            browser = self.browser_manager.get_browser()
            
            for keyword in random.sample(CONFIG['naukri']['keywords'], min(3, len(CONFIG['naukri']['keywords']))):
                for location in random.sample(CONFIG['naukri']['locations'], min(2, len(CONFIG['naukri']['locations']))):
                    try:
                        # Search URL
                        search_url = f"https://www.naukri.com/{keyword}-jobs-in-{location}"
                        
                        browser.get(search_url)
                        time.sleep(random.uniform(3, 5))
                        
                        # Scroll to load more jobs
                        self._scroll_page(browser)
                        
                        # Parse job cards
                        soup = BeautifulSoup(browser.page_source, 'html.parser')
                        job_cards = soup.select('article.jobTuple') or soup.select('div.jobTuple')
                        
                        for card in job_cards:
                            job = self._parse_html_job_card(card)
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
    
    def _parse_html_job_card(self, card: Any) -> Optional[Job]:
        """Parse job from HTML job card"""
        try:
            # Extract title
            title_element = card.select_one('a.title') or card.select_one('h2.title')
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
            
            # Extract experience
            experience = self._extract_experience_from_card(card)
            
            # Extract salary
            salary = self._extract_salary_from_card(card)
            
            # Create job object
            job = Job(
                title=self._clean_text(title),
                company=self._clean_text(company),
                location=self._clean_text(location),
                url=url,
                source='naukri',
                experience=self._clean_text(experience),
                salary=self._clean_text(salary),
                is_remote='remote' in location.lower()
            )
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to parse Naukri HTML job card: {e}")
            return None
    
    def _extract_url_from_card(self, card: Any) -> Optional[str]:
        """Extract URL from job card"""
        # Try to find link in title
        title_link = card.select_one('a.title') or card.select_one('a[href]')
        if title_link and title_link.get('href'):
            url = title_link['href']
            if not url.startswith('http'):
                url = f"https://www.naukri.com{url}"
            return url
        
        return None
    
    def _extract_company_from_card(self, card: Any) -> str:
        """Extract company from job card"""
        # Try company element
        company_element = card.select_one('a.subTitle') or card.select_one('div.company')
        if company_element:
            return company_element.get_text(strip=True)
        
        return "Unknown Company"
    
    def _extract_location_from_card(self, card: Any) -> str:
        """Extract location from job card"""
        # Try location element
        location_element = card.select_one('li.location') or card.select_one('span.location')
        if location_element:
            return location_element.get_text(strip=True)
        
        return ""
    
    def _extract_experience_from_card(self, card: Any) -> str:
        """Extract experience from job card"""
        # Try experience element
        exp_element = card.select_one('li.experience') or card.select_one('span.experience')
        if exp_element:
            return exp_element.get_text(strip=True)
        
        return ""
    
    def _extract_salary_from_card(self, card: Any) -> str:
        """Extract salary from job card"""
        # Try salary element
        salary_element = card.select_one('li.salary') or card.select_one('span.salary')
        if salary_element:
            return salary_element.get_text(strip=True)
        
        return ""
    
    def _scroll_page(self, browser: Any) -> None:
        """Scroll page to load more jobs"""
        try:
            # Scroll multiple times
            for _ in range(2):
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 2))
        except Exception:
            pass
    
    def _format_posted_date(self, posted_date: str) -> str:
        """Format posted date for display"""
        if not posted_date:
            return ""
        
        # Convert Naukri date format to readable format
        try:
            # Naukri often uses formats like "2 days ago", "1 week ago", etc.
            if "day" in posted_date:
                days = int(re.search(r'\d+', posted_date).group())
                return f"{days} days ago"
            elif "week" in posted_date:
                weeks = int(re.search(r'\d+', posted_date).group())
                return f"{weeks * 7} days ago"
            else:
                return posted_date
        except:
            return posted_date