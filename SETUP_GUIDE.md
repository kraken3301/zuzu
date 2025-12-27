# Multi-Platform Job Scraper - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install --break-system-packages -r requirements.txt
```

### 2. Update Configuration

Edit `job_scraper.py` and update the `CONFIG` dictionary:

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
stats = run()
print(f"Found {stats.total_new} new jobs!")
```

## Detailed Setup

### Google Colab Setup

For running in Google Colab:

```python
# First cell - Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Second cell - Install dependencies
!pip install --break-system-packages -q requests beautifulsoup4 lxml fake-useragent selenium webdriver-manager python-telegram-bot pandas tenacity feedparser
!apt-get update && apt-get install -y chromium-chromedriver

# Third cell - Run the scraper
from job_scraper import initialize, run

initialize()
run()
```

### Local Environment Setup

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the scraper
python job_scraper.py
```

## Configuration Options

### Telegram Settings

```python
'telegram': {
    'enabled': True,                    # Enable Telegram posting
    'bot_token': 'YOUR_BOT_TOKEN',      # Required: Get from @BotFather
    'channel_id': '@your_channel',      # Required: Channel username or ID
    'post_delay_min': 2,                # Min seconds between posts
    'post_delay_max': 5,                # Max seconds between posts
    'batch_size': 20,                   # Max jobs per batch
    'send_summary': True,               # Send run summary
    'error_notifications': True,        # Send error alerts
    'admin_chat_id': None,              # Admin chat for errors
}
```

### Platform Settings

Each platform has similar configuration:

```python
'linkedin': {
    'enabled': True,                    # Enable LinkedIn scraper
    'use_login': False,                 # ⚠️ Risk of account ban
    'email': '',                        # Login email (if use_login=True)
    'password': '',                     # Login password (if use_login=True)
    'keywords': ['software engineer fresher', ...],  # Search keywords
    'locations': ['India', 'Bangalore', ...],        # Target locations
    'experience_levels': [1, 2],       # 1=Internship, 2=Entry
    'time_posted': 'r86400',            # Past 24 hours
    'max_results_per_search': 100,      # Limit results
}
```

### Proxy Settings

```python
'proxy': {
    'enabled': True,                    # Enable proxy rotation
    'use_free_proxies': True,           # Use free proxy sources
    'free_proxy_count': 50,             # Max free proxies to fetch
    'test_before_use': True,            # Test proxies before use
    'custom_proxies': [                 # Add your paid proxies
        # 'http://user:pass@ip:port',
        # 'socks5://user:pass@ip:port',
    ],
    'rotate_per_request': True,         # Rotate proxy for each request
    'max_failures_before_blacklist': 3, # Auto-blacklist failing proxies
}
```

## Running the Scraper

### Single Run

```python
from job_scraper import initialize, run

initialize()
stats = run()
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
from job_scraper import test_linkedin, test_indeed, test_naukri

test_linkedin()
test_indeed()
test_naukri()
```

## Database Operations

### Show Statistics

```python
from job_scraper import show_stats

show_stats()
```

### Show Recent Jobs

```python
from job_scraper import show_recent_jobs

show_recent_jobs(10)  # Show 10 most recent jobs
```

### Search Jobs

```python
from job_scraper import search_jobs

jobs = search_jobs("Python")
print(f"Found {len(jobs)} Python jobs")
```

### Export Data

```python
from job_scraper import export_all

export_all()  # Exports to CSV and JSON
```

### Cleanup Old Jobs

```python
from job_scraper import cleanup

cleanup(30)  # Remove jobs older than 30 days
```

## Troubleshooting

### Common Issues

**Import Errors**
- Ensure all dependencies are installed
- Check Python version (3.8+ required)
- Verify virtual environment is activated

**Telegram Connection Failed**
- Check bot token is correct
- Verify channel ID is correct
- Ensure bot is added as admin to channel

**Database Errors**
- Check Google Drive is mounted (for Colab)
- Verify directory permissions
- Ensure CONFIG paths are correct

**Proxy Issues**
- Free proxies may be unreliable
- Consider adding paid proxies
- Check proxy test URL is accessible

### Debugging

```python
from job_scraper import show_logs

show_logs(50)  # Show last 50 log entries
```

## Deployment Options

### Scheduled Execution

**Cron Job**
```bash
0 */6 * * * /usr/bin/python3 /path/to/job_scraper.py
```

**GitHub Actions**
```yaml
- name: Run job scraper
  run: python job_scraper.py
  schedule:
    - cron: '0 */6 * * *'
```

### Cloud Deployment

**Google Colab**
- Use the provided Colab setup
- Enable keep-alive for long runs
- Monitor via Telegram notifications

**AWS/GCP**
- Deploy in a container
- Use cloud scheduling
- Monitor with cloud logging

## Best Practices

### Configuration
- Start with conservative settings
- Gradually increase scraping frequency
- Monitor for blocking/rate limiting

### Proxy Usage
- Use paid proxies for reliability
- Rotate proxies regularly
- Monitor proxy health

### Error Handling
- Check logs regularly
- Set up error notifications
- Implement graceful recovery

### Performance
- Start with single platform testing
- Monitor resource usage
- Optimize based on results

## Legal Compliance

⚠️ **Important**: Web scraping may violate platform Terms of Service.

- Use responsibly and at your own risk
- Respect platform rate limits
- Do not use for commercial purposes without authorization
- Regularly review platform policies

## Support

For issues and questions:
- Check the README.md for comprehensive documentation
- Review the IMPLEMENTATION_SUMMARY.md for technical details
- Examine test files for usage examples
- Consult the code comments for implementation details

## Next Steps

1. **Test Individual Scrapers**: Verify each platform works
2. **Configure Telegram**: Set up bot and channel
3. **Run Single Cycle**: Test the complete workflow
4. **Monitor Results**: Check logs and Telegram posts
5. **Adjust Configuration**: Optimize based on results
6. **Deploy**: Set up scheduled execution

## Additional Resources

- `README.md`: Comprehensive documentation
- `IMPLEMENTATION_SUMMARY.md`: Technical implementation details
- `example_usage.py`: Practical usage examples
- `test_core.py`: Core functionality tests
- `config.py`: Configuration template

## Contact

For questions about this implementation, please refer to the GitHub repository or open an issue with detailed information about the problem.