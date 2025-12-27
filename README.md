# Multi-Platform Job Scraper Bot

A production-grade job scraping bot that targets LinkedIn, Indeed, Naukri, and Superset platforms, with Telegram integration for posting new opportunities.

## Features

- **Multi-Platform Scraping**: LinkedIn, Indeed, Naukri, and Superset
- **Telegram Integration**: Automatic posting of new jobs to Telegram channels
- **Google Drive Persistence**: All data stored on Google Drive for persistence
- **Anti-Detection Measures**: Proxy rotation, browser fingerprinting, and human-like behavior
- **Comprehensive Filtering**: Filter jobs by experience, keywords, companies, and more
- **Production-Ready**: Error handling, logging, and graceful recovery

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Update Configuration

Edit the `CONFIG` dictionary in `job_scraper.py`:

```python
CONFIG = {
    'telegram': {
        'bot_token': 'YOUR_BOT_TOKEN_HERE',  # Get from @BotFather
        'channel_id': '@your_channel',        # Channel username or chat ID
    },
    # ... other settings
}
```

### 3. Run the Scraper

```python
from job_scraper import initialize, run

# Initialize the scraper
initialize()

# Run a single scraping cycle
run()
```

## Usage Examples

### Single Run
```python
from job_scraper import initialize, run

initialize()
stats = run()
print(f"Found {stats.total_new} new jobs!")
```

### Continuous Mode
```python
from job_scraper import initialize, run_continuous, keep_alive

initialize()
keep_alive()  # For Google Colab
run_continuous()  # Runs every 6 hours by default
```

### Test Individual Scrapers
```python
from job_scraper import initialize, test_linkedin, test_indeed, test_naukri

initialize()

# Test LinkedIn scraper
linkedin_jobs = test_linkedin()
print(f"Found {len(linkedin_jobs)} LinkedIn jobs")

# Test Indeed scraper
indeed_jobs = test_indeed()
print(f"Found {len(indeed_jobs)} Indeed jobs")

# Test Naukri scraper
naukri_jobs = test_naukri()
print(f"Found {len(naukri_jobs)} Naukri jobs")
```

### Database Operations
```python
from job_scraper import initialize, show_stats, show_recent_jobs, search_jobs

initialize()

# Show database statistics
show_stats()

# Show recent unposted jobs
show_recent_jobs(10)

# Search jobs by keyword
jobs = search_jobs("Python")
print(f"Found {len(jobs)} Python jobs")
```

## Configuration

The scraper is highly configurable. Key settings include:

### Telegram Settings
- `bot_token`: Your Telegram bot token from @BotFather
- `channel_id`: Target channel username or chat ID
- `post_delay_min/max`: Delay between posts to avoid rate limiting
- `batch_size`: Maximum jobs to post in one batch

### Platform Settings
Each platform (LinkedIn, Indeed, Naukri, Superset) has its own configuration:
- `enabled`: Enable/disable the scraper
- `keywords`: Search keywords
- `locations`: Target locations
- `experience_levels`: Experience filters
- `max_results_per_search`: Limit results per search

### Scraping Behavior
- `delay_min/max`: Random delays between requests
- `page_load_timeout`: Maximum page load time
- `request_timeout`: Maximum request timeout
- `randomize_order`: Randomize search order to avoid patterns

### Proxy Settings
- `enabled`: Enable proxy rotation
- `use_free_proxies`: Use free proxy sources
- `custom_proxies`: Add your own paid proxies
- `rotate_per_request`: Rotate proxy for each request

## Google Colab Setup

For running in Google Colab:

1. Mount Google Drive:
```python
from google.colab import drive
drive.mount('/content/drive')
```

2. Install dependencies:
```python
!pip install -r requirements.txt
!apt-get update && apt-get install -y chromium-chromedriver
```

3. Enable keep-alive:
```python
keep_alive()
```

## Data Storage

All data is stored in Google Drive at:
- `/MyDrive/JobScraper/data/job_scraper.db` - SQLite database
- `/MyDrive/JobScraper/logs/` - Log files
- `/MyDrive/JobScraper/exports/` - CSV/JSON exports
- `/MyDrive/JobScraper/cookies/` - Session cookies

## Database Schema

### Jobs Table
```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary TEXT,
    experience TEXT,
    description TEXT,
    skills TEXT,
    job_type TEXT,
    source TEXT NOT NULL,
    source_id TEXT,
    url TEXT,
    posted_date TEXT,
    deadline TEXT,
    keyword_matched TEXT,
    scraped_at TEXT NOT NULL,
    posted_to_telegram INTEGER DEFAULT 0,
    telegram_message_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

## Anti-Detection Features

- **Proxy Rotation**: Automatic proxy fetching and rotation
- **Browser Fingerprinting**: Randomized browser headers
- **Human-like Behavior**: Random delays, scrolling, typing
- **Rate Limiting**: Configurable delays between requests
- **Error Recovery**: Automatic retries with exponential backoff

## Telegram Message Format

Jobs are posted to Telegram in a formatted message:

```
🚨 NEW JOB ALERT 🔗

💼 Software Engineer
🏢 Google
📍 Bangalore, India
📊 Exp: 0-2 years
💰 10-20 LPA
🛠 Skills: Python, JavaScript, SQL

🔗 [Apply Now](https://example.com)

#linkedin #jobs #fresher
```

## Legal Disclaimer

⚠️ **Important**: Web scraping may violate Terms of Service of these platforms. Use responsibly and at your own risk.

- Do not use for commercial purposes without proper authorization
- Respect rate limits and robots.txt guidelines
- LinkedIn logged-in scraping may result in account suspension
- Regularly rotate proxies to avoid IP blocking

## Troubleshooting

### Common Issues

**LinkedIn returns empty results**
- Enable proxy rotation
- Increase delays between requests
- Try using login method (higher risk)

**Indeed shows CAPTCHA**
- Switch to RSS method: `CONFIG['indeed']['use_rss'] = True`
- Use proxy rotation

**Naukri API returns errors**
- Fallback to Selenium: `CONFIG['naukri']['use_api'] = False`
- Check if API headers need updating

**Superset login fails**
- Set `require_manual_login=True` and complete login manually
- Check credentials and college code
- Update login selectors if page structure changed

### Proxy Issues

**Too many proxy failures**
- Add paid proxies to `CONFIG['proxy']['custom_proxies']`
- Reduce scraping frequency
- Check if free proxy sources are working

## Development

### Architecture

```
JobScraperBot/
├── Core Classes
│   ├── Job (dataclass) - Unified job model
│   ├── ScrapingStats (dataclass) - Run statistics
│   └── ScrapingError (exception) - Custom exceptions
│
├── Infrastructure
│   ├── ConfigManager
│   ├── LogManager
│   ├── DatabaseManager
│   └── ProxyManager
│
├── HTTP Layer
│   ├── FingerprintGenerator
│   ├── HTTPClient
│   └── BrowserManager
│
├── Scrapers
│   ├── LinkedInScraper
│   ├── IndeedScraper
│   ├── NaukriScraper
│   └── SupersetScraper
│
├── Output
│   ├── TelegramPoster
│   └── ExportManager
│
└── Orchestrator
    └── JobScraperOrchestrator
```

### Adding New Platforms

To add a new job platform:

1. Create a new scraper class extending `BaseScraper`
2. Implement the `scrape_all()` method
3. Add platform configuration to `CONFIG`
4. Update the orchestrator to include the new scraper

### Testing

Test individual components:

```python
# Test Telegram connection
test_telegram()

# Test individual scrapers
test_linkedin()
test_indeed()
test_naukri()

# Test database operations
show_stats()
show_recent_jobs()
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Update documentation
5. Submit a pull request

## License

This project is for educational purposes only. Use responsibly and comply with all applicable laws and platform terms of service.

## Support

For issues and questions, please open a GitHub issue with:
- Detailed description of the problem
- Configuration settings
- Error messages/logs
- Steps to reproduce

## Roadmap

Future enhancements:
- Add more job platforms (Glassdoor, Monster, etc.)
- Email notifications
- Web dashboard for monitoring
- Advanced analytics and reporting
- Machine learning for job recommendations
- Browser extension for easy setup

## Credits

This project was inspired by the need for a comprehensive job scraping solution for freshers and entry-level professionals in India.

## Contact

For questions about this implementation, please refer to the GitHub repository or open an issue.
