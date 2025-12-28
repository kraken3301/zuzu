# ============================================================================
# PROXY MANAGER - Advanced Proxy Rotation and Management
# ============================================================================

import re
import random
import requests
import threading
from typing import List, Set, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse
import ssl

from bs4 import BeautifulSoup
from .config import CONFIG
from .log_manager import LogManager
from .models import ProxyError


class ProxyManager:
    """Advanced proxy management with rotation, SSL handling, and health tracking"""
    
    FREE_PROXY_SOURCES = [
        'https://free-proxy-list.net/',
        'https://www.sslproxies.org/',
        'https://www.us-proxy.org/',
        'https://www.vpngate.net/api/iphone/',
    ]
    
    # Test URLs for different protocols
    TEST_URLS = {
        'http': 'http://httpbin.org/ip',
        'https': 'https://httpbin.org/ip',
    }
    
    def __init__(self):
        self.logger = LogManager.get_logger('ProxyManager')
        self._proxies: List[str] = []
        self._working_proxies: Set[str] = set()
        self._blacklist: Set[str] = set()
        self._temp_blacklist: Dict[str, float] = {}  # proxy -> unblock time
        self._failures: Dict[str, int] = {}
        self._successes: Dict[str, int] = {}
        self._domain_blacklist: Dict[str, Set[str]] = {}  # domain -> set of proxies
        self._recovery_attempts: Dict[str, int] = {}
        self._ssl_failures: Set[str] = set()  # proxies that fail SSL
        self._lock = threading.Lock()
        self._current_index = 0
        self._last_test_time: Optional[datetime] = None
        self._test_interval_hours = 6  # Re-test proxies every 6 hours
    
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
            headers = {'User-Agent': self._get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=15)
            
            if 'vpngate.net' in url:
                # Specialized parser for VPNGate format
                self.logger.debug(f"Using specialized parser for VPNGate: {url}")
                
                # Extract IP:Port combinations from response text
                ip_port_matches = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', response.text)
                for ip, port in ip_port_matches:
                    proxies.append(f"http://{ip}:{port}")
                
                # If no IP:Port found, try to find just IPs and use default ports
                if not proxies:
                    ip_matches = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', response.text)
                    for ip in ip_matches:
                        # Skip if it's the header or a common non-proxy IP
                        if ip.endswith('.0') or ip.startswith('127.'):
                            continue
                        # Common proxy ports used by VPNGate and others
                        for port in ['8080', '80', '443', '3128']:
                            proxies.append(f"http://{ip}:{port}")
                
                self.logger.info(f"Extracted {len(proxies)} proxies from VPNGate")
            else:
                # Original HTML parser
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table = soup.find('table')
                if table:
                    for row in table.find_all('tr')[1:]:  # Skip header
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            protocol = 'https' if 'yes' in cols[6].text.lower() else 'http'
                            
                            if self._is_valid_proxy_format(ip, port):
                                proxy_url = f"{protocol}://{ip}:{port}"
                                proxies.append(proxy_url)
        
        except Exception as e:
            self.logger.warning(f"Error fetching proxies from {url}: {e}")
        
        return proxies
    
    def _is_valid_proxy_format(self, ip: str, port: str) -> bool:
        """Validate proxy IP and port format"""
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        port_pattern = r'^\d+$'
        
        return (re.match(ip_pattern, ip) and 
                re.match(port_pattern, port) and
                1 <= int(port) <= 65535)
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent"""
        # Import here to avoid circular imports
        from utils.helpers import get_random_user_agent
        return get_random_user_agent()
    
    def _test_all_proxies(self) -> None:
        """Test all proxies and update working list"""
        self.logger.info(f"Testing {len(self._proxies)} proxies...")
        
        working_proxies = []
        
        for proxy in self._proxies:
            if self._test_proxy(proxy):
                working_proxies.append(proxy)
        
        self._working_proxies = set(working_proxies)
        self.logger.info(f"Proxy testing complete: {len(working_proxies)} working out of {len(self._proxies)}")
    
    def _test_proxy(self, proxy: str) -> bool:
        """Test a single proxy"""
        try:
            # Skip if blacklisted
            if proxy in self._blacklist:
                return False
            
            # Check temporary blacklist
            if proxy in self._temp_blacklist:
                if self._temp_blacklist[proxy] > datetime.now().timestamp():
                    return False
                else:
                    del self._temp_blacklist[proxy]
            
            # Determine test URL based on proxy protocol
            proxy_parsed = urlparse(proxy)
            protocol = proxy_parsed.scheme
            test_url = self.TEST_URLS.get(protocol, self.TEST_URLS['http'])
            
            # Test the proxy
            proxies = {protocol: proxy}
            
            # Handle SSL verification based on config
            verify_ssl = not CONFIG['proxy']['allow_unverified_ssl']
            
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=CONFIG['proxy']['test_timeout'],
                verify=verify_ssl
            )
            
            # Check if response contains our IP (meaning proxy worked)
            if response.status_code == 200:
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Proxy {proxy} failed test: {e}")
            return False
    
    def get_proxy(self) -> Optional[str]:
        """Get a working proxy (with rotation)"""
        if not CONFIG['proxy']['enabled'] or not self._working_proxies:
            return None
        
        with self._lock:
            if not self._working_proxies:
                return None
            
            # Rotate proxies
            if CONFIG['proxy']['rotate_per_request']:
                proxies_list = list(self._working_proxies)
                proxy = proxies_list[self._current_index % len(proxies_list)]
                self._current_index += 1
                return proxy
            else:
                # Return random proxy
                return random.choice(list(self._working_proxies))
    
    def report_success(self, proxy: str) -> None:
        """Report successful proxy usage"""
        if not proxy:
            return
        
        with self._lock:
            self._successes[proxy] = self._successes.get(proxy, 0) + 1
            self._failures[proxy] = self._failures.get(proxy, 0)  # Reset failures
    
    def report_failure(self, proxy: str, domain: str = "", error: Exception = None) -> None:
        """Report failed proxy usage"""
        if not proxy:
            return
        
        with self._lock:
            self._failures[proxy] = self._failures.get(proxy, 0) + 1
            
            # Check if proxy should be blacklisted
            if self._failures[proxy] >= CONFIG['proxy']['max_failures_before_blacklist']:
                self._blacklist.add(proxy)
                if proxy in self._working_proxies:
                    self._working_proxies.remove(proxy)
                self.logger.warning(f"Blacklisted proxy {proxy} after {self._failures[proxy]} failures")
            
            # Domain-specific blacklisting
            if domain:
                if domain not in self._domain_blacklist:
                    self._domain_blacklist[domain] = set()
                self._domain_blacklist[domain].add(proxy)
    
    def get_working_proxies_count(self) -> int:
        """Get count of working proxies"""
        return len(self._working_proxies)
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        return {
            'total_proxies': len(self._proxies),
            'working_proxies': len(self._working_proxies),
            'blacklisted_proxies': len(self._blacklist),
            'temp_blacklisted_proxies': len(self._temp_blacklist),
            'total_failures': sum(self._failures.values()),
            'total_successes': sum(self._successes.values())
        }
    
    def should_retry_without_proxy(self, domain: str) -> bool:
        """Determine if we should retry without proxy for this domain"""
        if not CONFIG['proxy']['enabled']:
            return False
        
        # If all proxies are blacklisted for this domain, retry without proxy
        domain_proxies = self._domain_blacklist.get(domain, set())
        if len(domain_proxies) >= len(self._working_proxies) * 0.8:  # 80%+ failed
            return True
        
        return False
    
    def get_proxy_for_domain(self, domain: str) -> Optional[str]:
        """Get proxy for specific domain, avoiding blacklisted ones"""
        if not CONFIG['proxy']['enabled']:
            return None
        
        # Check if we should retry without proxy for this domain
        if self.should_retry_without_proxy(domain):
            return None
        
        # Get domain-specific blacklist
        domain_blacklist = self._domain_blacklist.get(domain, set())
        
        # Find proxies not blacklisted for this domain
        available_proxies = [p for p in self._working_proxies if p not in domain_blacklist]
        
        if not available_proxies:
            return None
        
        # Rotate or random selection
        if CONFIG['proxy']['rotate_per_request']:
            with self._lock:
                if not available_proxies:
                    return None
                proxy = available_proxies[self._current_index % len(available_proxies)]
                self._current_index += 1
                return proxy
        else:
            return random.choice(available_proxies)