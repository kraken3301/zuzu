# ============================================================================
# UTILITY HELPERS - Common Helper Functions
# ============================================================================

import random
import re
from typing import List

# Fallback user agents
FALLBACK_USER_AGENTS: List[str] = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def get_random_user_agent() -> str:
    """Get random user agent"""
    try:
        from fake_useragent import UserAgent
        try:
            return UserAgent().random
        except Exception:
            pass
    except ImportError:
        pass
    
    return random.choice(FALLBACK_USER_AGENTS)


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    return text.strip()


def extract_experience_years(text: str) -> float:
    """Extract experience requirement in years from text"""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    # Look for patterns like "1-2 years", "3+ years", etc.
    patterns = [
        r'(\d+)\s*-\s*(\d+)\s+years?',  # 1-2 years
        r'(\d+)\s*\+?\s+years?',         # 3 years, 3+ years
        r'(\d+)\s+year',                  # 1 year
        r'fresher|entry level|trainee|graduate',  # 0 years
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
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


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    if not url:
        return False
    
    pattern = re.compile(
        r'^(https?|ftp)://'  # protocol
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ip
        r'(?::\d+)?'  # port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return re.match(pattern, url) is not None


def normalize_url(url: str) -> str:
    """Normalize URL"""
    if not url:
        return ""
    
    # Add https if missing
    if not url.startswith('http'):
        url = f"https://{url}" if not url.startswith('//') else f"https:{url}"
    
    return url.strip()


def escape_markdown(text: str) -> str:
    """Escape MarkdownV2 special characters"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text