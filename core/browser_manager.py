# ============================================================================
# BROWSER MANAGER - Selenium WebDriver Management
# ============================================================================

import os
import time
import random
from typing import Optional, Dict, Any, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager

# Handle undetected_chromedriver import with fallback
try:
    import undetected_chromedriver as uc
except ImportError:
    # Create a mock uc module for basic functionality
    import sys
    from unittest.mock import MagicMock
    uc = MagicMock()
    uc.Chrome = webdriver.Chrome
    uc.ChromeOptions = Options
    sys.modules['undetected_chromedriver'] = uc

from .config import CONFIG
from .log_manager import LogManager
from .proxy_manager import ProxyManager


class BrowserManager:
    """Manage Selenium WebDriver instances with proxy support"""
    
    def __init__(self, proxy_manager: ProxyManager):
        self.logger = LogManager.get_logger('BrowserManager')
        self.proxy_manager = proxy_manager
        self.browser = None
        self._browser_count = 0
    
    def get_browser(self, use_proxy: bool = True, headless: bool = True) -> webdriver.Chrome:
        """Get a configured browser instance"""
        if self.browser:
            return self.browser
        
        self._browser_count += 1
        
        try:
            # Use undetected-chromedriver for stealth
            options = self._get_chrome_options(headless)
            
            # Configure proxy if needed
            if use_proxy and CONFIG['proxy']['enabled']:
                proxy = self.proxy_manager.get_proxy()
                if proxy:
                    options.add_argument(f'--proxy-server={proxy}')
            
            # Initialize browser
            self.browser = uc.Chrome(
                options=options,
                driver_executable_path=ChromeDriverManager().install()
            )
            
            # Additional stealth settings
            self._apply_stealth_settings()
            
            self.logger.info(f"Browser initialized (Browser #{self._browser_count})")
            return self.browser
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _get_chrome_options(self, headless: bool = True) -> Options:
        """Get Chrome options with stealth configuration"""
        options = uc.ChromeOptions()
        
        # Basic options
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-features=NetworkService')
        options.add_argument('--disable-features=NetworkServiceInProcess')
        
        # User agent rotation
        user_agent = self._get_random_user_agent()
        options.add_argument(f'--user-agent={user_agent}')
        
        # Window size
        options.add_argument('--window-size=1366,768')
        
        # Additional stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Performance optimizations
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-component-update')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-web-resources')
        options.add_argument('--enable-automation')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--metrics-recording-only')
        options.add_argument('--password-store=basic')
        options.add_argument('--use-mock-keychain')
        
        # Experimental features
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        return options
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent"""
        from utils.helpers import get_random_user_agent
        return get_random_user_agent()
    
    def _apply_stealth_settings(self) -> None:
        """Apply additional stealth settings to browser"""
        if not self.browser:
            return
        
        try:
            # Remove automation flags
            self.browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    delete window.navigator.webdriver;
                    delete window.navigator.__driver_evaluate;
                    delete window.navigator.__webdriver_evaluate;
                    delete window.navigator.__selenium_evaluate;
                    delete window.navigator.__fxdriver_evaluate;
                    delete window.navigator.__driver_unwrapped;
                    delete window.navigator.__webdriver_unwrapped;
                    delete window.navigator.__selenium_unwrapped;
                    delete window.navigator.__fxdriver_unwrapped;
                '''
            })
            
            # Override plugins to appear more realistic
            self.browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'plugins', {
                        get: function() {
                            return [
                                {name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer'},
                                {name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                                {name: 'Native Client', description: '', filename: 'internal-nacl-plugin'}
                            ];
                        }
                    });
                    Object.defineProperty(navigator, 'mimeTypes', {
                        get: function() {
                            return [
                                {type: 'application/pdf', description: 'Portable Document Format', suffixes: 'pdf'},
                                {type: 'text/pdf', description: 'Portable Document Format', suffixes: 'pdf'}
                            ];
                        }
                    });
                '''
            })
            
        except Exception as e:
            self.logger.debug(f"Could not apply stealth settings: {e}")
    
    def wait_for_element(self, browser: webdriver.Chrome, selector: str, timeout: int = 10) -> Any:
        """Wait for element to be present"""
        try:
            return WebDriverWait(browser, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            self.logger.warning(f"Element not found: {selector}")
            return None
    
    def wait_for_elements(self, browser: webdriver.Chrome, selector: str, timeout: int = 10) -> List[Any]:
        """Wait for multiple elements to be present"""
        try:
            return WebDriverWait(browser, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            self.logger.warning(f"Elements not found: {selector}")
            return []
    
    def safe_find_element(self, browser: webdriver.Chrome, selector: str) -> Optional[Any]:
        """Safely find element (returns None if not found)"""
        try:
            return browser.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            return None
    
    def safe_find_elements(self, browser: webdriver.Chrome, selector: str) -> List[Any]:
        """Safely find elements (returns empty list if not found)"""
        try:
            return browser.find_elements(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            return []
    
    def close_browser(self) -> None:
        """Close browser instance"""
        if self.browser:
            try:
                self.browser.quit()
                self.browser = None
                self.logger.info("Browser closed")
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")
    
    def restart_browser(self) -> webdriver.Chrome:
        """Restart browser with new instance"""
        self.close_browser()
        return self.get_browser()
    
    def random_delay(self) -> None:
        """Add random delay to mimic human behavior"""
        delay = random.uniform(
            CONFIG['scraping']['request_delay_min'],
            CONFIG['scraping']['request_delay_max']
        )
        time.sleep(delay)
    
    def human_like_click(self, element: Any) -> None:
        """Perform human-like click with random delay"""
        if not element:
            return
        
        # Move to element first
        try:
            webdriver.ActionChains(self.browser).move_to_element(element).perform()
            time.sleep(random.uniform(0.1, 0.5))
            element.click()
            time.sleep(random.uniform(0.2, 0.8))
        except Exception as e:
            self.logger.debug(f"Human-like click failed, using regular click: {e}")
            try:
                element.click()
            except Exception:
                pass
    
    def human_like_type(self, element: Any, text: str) -> None:
        """Type text in human-like manner"""
        if not element:
            return
        
        try:
            element.clear()
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
        except Exception as e:
            self.logger.debug(f"Human-like typing failed, using regular typing: {e}")
            try:
                element.send_keys(text)
            except Exception:
                pass