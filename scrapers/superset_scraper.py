# ============================================================================
# SUPERSET SCRAPER - Scrape Superset Job Listings
# ============================================================================

import re
import time
import random
import json
import os
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup

from core.models import Job, ScraperError, AuthenticationError
from core.config import CONFIG
from core.log_manager import LogManager
from core.database_manager import DatabaseManager
from core.proxy_manager import ProxyManager
from core.http_client import HTTPClient
from core.browser_manager import BrowserManager
from .base_scraper import BaseScraper


class SupersetScraper(BaseScraper):
    """Scrape job listings from Superset"""
    
    def __init__(self, db: DatabaseManager, proxy_manager: ProxyManager, 
                 http_client: HTTPClient, browser_manager: BrowserManager):
        super().__init__(db, proxy_manager, http_client, browser_manager)
    
    def scrape(self) -> List[Job]:
        """Main scraping method"""
        jobs = []
        
        if not CONFIG['superset']['enabled']:
            self.logger.info("Superset scraper disabled")
            return jobs
        
        self.logger.info("Starting Superset scraping...")
        
        try:
            browser = self.browser_manager.get_browser(headless=False)  # Superset often requires visible browser
            
            # Login first
            if not self._login(browser):
                self.logger.error("Superset login failed")
                return jobs
            
            # Navigate to opportunities page
            browser.get(CONFIG['superset']['dashboard_url'])
            time.sleep(random.uniform(3, 5))
            
            # Scroll to load more jobs
            self._scroll_page(browser)
            
            # Parse job cards
            soup = BeautifulSoup(browser.page_source, 'html.parser')
            job_cards = self._find_job_cards(soup)
            
            for card in job_cards:
                job = self._parse_job_card(card)
                if job and self._filter_job(job):
                    jobs.append(job)
            
            self.logger.info(f"Superset scraping completed: {len(jobs)} jobs found")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Superset scraping failed: {e}")
            return []
        finally:
            self.browser_manager.close_browser()
    
    def _login(self, browser: Any) -> bool:
        """Login to Superset"""
        try:
            browser.get(CONFIG['superset']['login_url'])
            time.sleep(random.uniform(2, 4))
            
            # Check if already logged in
            if "dashboard" in browser.current_url.lower() or "opportunities" in browser.current_url.lower():
                self.logger.info("Already logged in to Superset")
                return True
            
            # Try to load saved cookies
            if CONFIG['superset']['use_saved_cookies']:
                if self._load_cookies(browser):
                    browser.refresh()
                    time.sleep(2)
                    if "dashboard" in browser.current_url.lower() or "opportunities" in browser.current_url.lower():
                        self.logger.info("Logged in using saved cookies")
                        return True
            
            # Manual login process
            self.logger.info("Performing manual login to Superset")
            
            # Find email input - use more specific selectors
            email_input = None
            for selector in [
                'input[type="email"][name="email"]',
                'input[type="email"][id="email"]',
                'input[type="email"][placeholder*="email"]',
                'input[type="email"][aria-label*="email"]'
            ]:
                email_input = self.browser_manager.safe_find_element(browser, selector)
                if email_input:
                    break
            
            if not email_input:
                self.logger.error("Could not find email input field")
                return False
            
            # Find password input
            password_input = None
            for selector in [
                'input[type="password"][name="password"]',
                'input[type="password"][id="password"]',
                'input[type="password"][placeholder*="password"]',
                'input[type="password"][aria-label*="password"]'
            ]:
                password_input = self.browser_manager.safe_find_element(browser, selector)
                if password_input:
                    break
            
            if not password_input:
                self.logger.error("Could not find password input field")
                return False
            
            # Enter credentials
            self.browser_manager.human_like_type(email_input, CONFIG['superset']['email'])
            time.sleep(random.uniform(0.5, 1.0))
            self.browser_manager.human_like_type(password_input, CONFIG['superset']['password'])
            time.sleep(random.uniform(0.5, 1.0))
            
            # Find and click login button
            login_button = None
            for selector in [
                'button[type="submit"]',
                'button[class*="login"]',
                'button[class*="submit"]',
                'button[id*="login"]',
                'button[aria-label*="login"]'
            ]:
                login_button = self.browser_manager.safe_find_element(browser, selector)
                if login_button:
                    break
            
            if not login_button:
                self.logger.error("Could not find login button")
                return False
            
            self.browser_manager.human_like_click(login_button)
            time.sleep(random.uniform(3, 5))
            
            # Check if login was successful
            if "dashboard" in browser.current_url.lower() or "opportunities" in browser.current_url.lower():
                self.logger.info("Successfully logged in to Superset")
                
                # Save cookies for future use
                if CONFIG['superset']['use_saved_cookies']:
                    self._save_cookies(browser)
                
                return True
            else:
                self.logger.error("Login failed - check credentials or CAPTCHA")
                return False
            
        except Exception as e:
            self.logger.error(f"Superset login failed: {e}")
            return False
    
    def _save_cookies(self, browser: Any) -> None:
        """Save browser cookies to file"""
        try:
            # Ensure cookies directory exists
            os.makedirs(CONFIG['paths']['cookies_dir'], exist_ok=True)
            
            # Get cookies
            cookies = browser.get_cookies()
            
            # Save to file
            cookie_file = os.path.join(CONFIG['paths']['cookies_dir'], CONFIG['superset']['cookie_file'])
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            self.logger.info(f"Saved {len(cookies)} cookies to {cookie_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save cookies: {e}")
    
    def _load_cookies(self, browser: Any) -> bool:
        """Load cookies from file"""
        try:
            cookie_file = os.path.join(CONFIG['paths']['cookies_dir'], CONFIG['superset']['cookie_file'])
            
            if not os.path.exists(cookie_file):
                return False
            
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            # Add cookies to browser
            for cookie in cookies:
                try:
                    browser.add_cookie(cookie)
                except Exception:
                    continue
            
            self.logger.info(f"Loaded {len(cookies)} cookies from {cookie_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load cookies: {e}")
            return False
    
    def _find_job_cards(self, soup: BeautifulSoup) -> List[Any]:
        """Find job cards using flexible selectors"""
        selectors = [
            'div.job-card',
            'div.card.job',
            'article.job',
            'div[class*="job"]',
            'div[class*="card"]'
        ]
        
        for selector in selectors:
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
            
            # Extract additional info
            experience = self._extract_experience_from_card(card)
            salary = self._extract_salary_from_card(card)
            
            # Create job object
            job = Job(
                title=self._clean_text(title),
                company=self._clean_text(company),
                location=self._clean_text(location),
                url=url,
                source='superset',
                experience=self._clean_text(experience),
                salary=self._clean_text(salary),
                is_remote='remote' in location.lower()
            )
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to parse Superset job card: {e}")
            return None
    
    def _extract_title_from_card(self, card: Any) -> Optional[str]:
        """Extract title from job card"""
        selectors = [
            'h3.title',
            'h2.title',
            'h3.job-title',
            'h2.job-title',
            'a.title',
            'a.job-title'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_company_from_card(self, card: Any) -> Optional[str]:
        """Extract company from job card"""
        selectors = [
            'div.company',
            'span.company',
            'div.employer',
            'span.employer',
            'div.company-name',
            'span.company-name'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "Unknown Company"
    
    def _extract_location_from_card(self, card: Any) -> Optional[str]:
        """Extract location from job card"""
        selectors = [
            'div.location',
            'span.location',
            'div.where',
            'span.where',
            'div.job-location',
            'span.job-location'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_url_from_card(self, card: Any) -> Optional[str]:
        """Extract URL from job card"""
        # Try to find link in card
        link = card.select_one('a[href]')
        if link and link.get('href'):
            url = link['href']
            if not url.startswith('http'):
                # Try to determine base URL
                if hasattr(self, 'BASE_URL'):
                    url = f"{self.BASE_URL}{url}"
                else:
                    url = f"https://{url}" if not url.startswith('//') else f"https:{url}"
            return url
        
        return None
    
    def _extract_experience_from_card(self, card: Any) -> str:
        """Extract experience from job card"""
        selectors = [
            'div.experience',
            'span.experience',
            'div.exp',
            'span.exp',
            'li:contains("experience")',
            'li:contains("years")'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_salary_from_card(self, card: Any) -> str:
        """Extract salary from job card"""
        selectors = [
            'div.salary',
            'span.salary',
            'div.pay',
            'span.pay',
            'div.compensation',
            'span.compensation'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _scroll_page(self, browser: Any) -> None:
        """Scroll page to load more jobs"""
        try:
            # Scroll multiple times
            for _ in range(3):
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 2))
        except Exception:
            pass