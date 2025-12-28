"""
Core module for job scraper
Re-exports components from the monolithic job_scraper for backward compatibility
"""

# Re-export everything from job_scraper for seamless module integration
from job_scraper import (
    # Models
    Job,
    ScrapingStats,
    ScraperError,
    ProxyError,
    RateLimitError,
    AuthenticationError,
    CaptchaError,
    BlockedError,
    
    # Managers
    LogManager,
    DatabaseManager,
    ProxyManager,
    HTTPClient,
    BrowserManager,
    TelegramPoster,
    
    # Scrapers
    BaseScraper,
    LinkedInScraper,
    IndeedScraper,
    NaukriScraper,
    SupersetScraper,
    GovernmentJobsScraper,
    
    # Config
    CONFIG,
    validate_config,
    get_random_user_agent,
    setup_environment,
    
    # Orchestrator
    JobScraperOrchestrator,
    
    # Utilities
    initialize,
    run,
    run_continuous,
    show_stats,
    show_recent_jobs,
    test_linkedin,
    test_indeed,
    test_naukri,
    test_telegram,
    export_all,
    search_jobs,
    cleanup,
    shutdown,
    keep_alive,
    setup_colab_display,
)