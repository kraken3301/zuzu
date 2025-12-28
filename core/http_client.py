# ============================================================================
# HTTP CLIENT - Fingerprinted HTTP Requests
# ============================================================================

import re
import time
import random
import requests
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
import ssl

from .config import CONFIG
from .log_manager import LogManager
from .models import ScraperError, RateLimitError, BlockedError
from .proxy_manager import ProxyManager


class HTTPClient:
    """HTTP client with fingerprinting, proxy support, and error handling"""
    
    def __init__(self, proxy_manager: ProxyManager):
        self.logger = LogManager.get_logger('HTTPClient')
        self.proxy_manager = proxy_manager
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self) -> None:
        """Setup session with default headers and configurations"""
        # Set default headers
        self.session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        
        # Configure timeouts
        self.session_timeout = CONFIG['proxy']['request_timeout']
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent"""
        from utils.helpers import get_random_user_agent
        return get_random_user_agent()
    
    def _get_proxy_for_url(self, url: str) -> Optional[str]:
        """Get appropriate proxy for URL"""
        domain = urlparse(url).netloc
        return self.proxy_manager.get_proxy_for_domain(domain)
    
    def _should_use_proxy(self, url: str) -> bool:
        """Determine if proxy should be used for this request"""
        if not CONFIG['proxy']['enabled']:
            return False
        
        # Check if we should retry without proxy for this domain
        domain = urlparse(url).netloc
        if self.proxy_manager.should_retry_without_proxy(domain):
            return False
        
        return True
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic and proxy management"""
        max_retries = kwargs.pop('max_retries', 3)
        retry_delay = kwargs.pop('retry_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                # Get proxy for this request
                use_proxy = self._should_use_proxy(url)
                proxy = self._get_proxy_for_url(url) if use_proxy else None
                
                # Set proxy in kwargs
                if proxy:
                    kwargs['proxies'] = {'http': proxy, 'https': proxy}
                
                # Set timeout
                kwargs['timeout'] = self._get_timeout_for_attempt(attempt)
                
                # Set SSL verification
                kwargs['verify'] = not CONFIG['proxy']['allow_unverified_ssl']
                
                # Random delay to avoid rate limiting
                self._random_delay()
                
                # Make request
                response = self.session.request(method, url, **kwargs)
                
                # Check for rate limiting
                if response.status_code == 429:
                    raise RateLimitError(f"Rate limited on {url}")
                
                # Check for blocking
                if self._is_blocked_response(response):
                    raise BlockedError(f"Blocked by {url}")
                
                # Report proxy success/failure
                if proxy:
                    if response.status_code < 400:
                        self.proxy_manager.report_success(proxy)
                    else:
                        self.proxy_manager.report_failure(proxy, urlparse(url).netloc)
                
                return response
                
            except (RateLimitError, BlockedError) as e:
                # For rate limiting/blocking, try without proxy on next attempt
                if proxy and attempt < max_retries - 1:
                    self.logger.warning(f"{type(e).__name__} with proxy {proxy}, retrying without proxy")
                    self.proxy_manager.report_failure(proxy, urlparse(url).netloc, e)
                    continue
                else:
                    raise
                
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    if proxy:
                        self.proxy_manager.report_failure(proxy, urlparse(url).netloc, e)
                    raise ScraperError(f"Request failed after {max_retries} attempts: {e}")
                
                # Exponential backoff
                delay = retry_delay * (2 ** attempt)
                self.logger.debug(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """HTTP GET request"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """HTTP POST request"""
        return self.request('POST', url, **kwargs)
    
    def _get_timeout_for_attempt(self, attempt: int) -> Tuple[float, float]:
        """Get timeout based on attempt number"""
        if CONFIG['proxy']['adaptive_timeout'] and len(CONFIG['proxy']['timeout_escalation']) > attempt:
            timeout = CONFIG['proxy']['timeout_escalation'][attempt]
        else:
            timeout = CONFIG['proxy']['request_timeout']
        
        return (timeout, timeout)  # (connect, read)
    
    def _random_delay(self) -> None:
        """Add random delay to avoid rate limiting"""
        delay = random.uniform(
            CONFIG['scraping']['request_delay_min'],
            CONFIG['scraping']['request_delay_max']
        )
        time.sleep(delay)
    
    def _is_blocked_response(self, response: requests.Response) -> bool:
        """Check if response indicates blocking"""
        # Check for common blocking patterns
        content = response.text.lower()
        
        blocking_patterns = [
            'access denied',
            'bot detected',
            'please enable javascript',
            'cloudflare',
            'captcha',
            'verify you are human',
            'your ip has been temporarily blocked',
            'too many requests',
            'forbidden',
            'unauthorized'
        ]
        
        return (response.status_code in [403, 401] or 
                any(pattern in content for pattern in blocking_patterns))
    
    def rotate_user_agent(self) -> None:
        """Rotate user agent"""
        self.session.headers['User-Agent'] = self._get_random_user_agent()
    
    def close(self) -> None:
        """Close session"""
        self.session.close()