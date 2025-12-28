# ============================================================================
# JOB SCRAPER ORCHESTRATOR - Main Controller
# ============================================================================

import os
import time
import random
import json
from datetime import datetime
from typing import List, Optional

from core.models import Job, ScrapingStats
from core.config import CONFIG, load_config, validate_config
from core.log_manager import LogManager
from core.database_manager import DatabaseManager
from core.proxy_manager import ProxyManager
from core.http_client import HTTPClient
from core.browser_manager import BrowserManager
from core.telegram_poster import TelegramPoster

from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.indeed_scraper import IndeedScraper
from scrapers.naukri_scraper import NaukriScraper
from scrapers.superset_scraper import SupersetScraper


class JobScraperOrchestrator:
    """Main orchestrator for job scraping"""
    
    def __init__(self):
        self.logger = LogManager.get_logger('Orchestrator')
        
        # Initialize components
        self.db = DatabaseManager()
        self.proxy_manager = ProxyManager()
        self.http_client = HTTPClient(self.proxy_manager)
        self.browser_manager = BrowserManager(self.proxy_manager)
        self.telegram = TelegramPoster()
        
        # Initialize scrapers
        self.linkedin_scraper = LinkedInScraper(
            self.db, self.proxy_manager, self.http_client, self.browser_manager
        )
        self.indeed_scraper = IndeedScraper(
            self.db, self.proxy_manager, self.http_client, self.browser_manager
        )
        self.naukri_scraper = NaukriScraper(
            self.db, self.proxy_manager, self.http_client, self.browser_manager
        )
        self.superset_scraper = SupersetScraper(
            self.db, self.proxy_manager, self.http_client, self.browser_manager
        )
        
        self._running = False
    
    def initialize(self) -> bool:
        """Initialize all components"""
        self.logger.info("=" * 60)
        self.logger.info("INITIALIZING JOB SCRAPER BOT")
        self.logger.info("=" * 60)
        
        # Load configuration
        load_config()
        
        # Validate config (warn but don't fail if Telegram not configured)
        is_valid, errors = validate_config()
        if not is_valid:
            for error in errors:
                self.logger.warning(f"Config warning: {error}")
            self.logger.info("Initializing with warnings (some features may not work)")
        
        # Initialize environment
        self._initialize_environment()
        
        # Initialize proxies
        if CONFIG['proxy']['enabled']:
            proxy_count = self.proxy_manager.initialize()
            self.logger.info(f"Proxy pool: {proxy_count} working proxies")
        
        # Test Telegram
        if CONFIG['telegram']['enabled']:
            if self.telegram.test_connection():
                self.logger.info("Telegram connection successful")
            else:
                self.logger.warning("Telegram connection failed")
        
        self.logger.info("Initialization complete!")
        return True
    
    def _initialize_environment(self) -> None:
        """Initialize environment (directories, etc.)"""
        try:
            # Create directory structure
            dirs = [
                CONFIG['paths']['base_dir'],
                CONFIG['paths']['database_dir'],
                CONFIG['paths']['logs_dir'],
                CONFIG['paths']['exports_dir'],
                CONFIG['paths']['cookies_dir'],
                CONFIG['paths']['backups_dir'],
            ]
            
            for dir_path in dirs:
                os.makedirs(dir_path, exist_ok=True)
                self.logger.debug(f"Directory ready: {dir_path}")
            
        except Exception as e:
            self.logger.error(f"Environment initialization failed: {e}")
    
    def run(self) -> ScrapingStats:
        """Run complete scraping cycle"""
        self.logger.info("=" * 60)
        self.logger.info("STARTING SCRAPING CYCLE")
        self.logger.info("=" * 60)
        
        stats = ScrapingStats()
        all_jobs = []
        
        try:
            # Scrape from each platform
            if CONFIG['linkedin']['enabled']:
                self.logger.info("Scraping LinkedIn...")
                try:
                    jobs = self.linkedin_scraper.scrape()
                    stats.linkedin_jobs = len(jobs)
                    all_jobs.extend(jobs)
                    self.logger.info(f"LinkedIn: {len(jobs)} jobs found")
                except Exception as e:
                    stats.linkedin_errors += 1
                    self.logger.error(f"LinkedIn scraping failed: {e}")
                    if CONFIG['telegram']['error_notifications']:
                        self.telegram.send_error(f"LinkedIn scraping failed: {e}")
            
            if CONFIG['indeed']['enabled']:
                self.logger.info("Scraping Indeed...")
                try:
                    jobs = self.indeed_scraper.scrape()
                    stats.indeed_jobs = len(jobs)
                    all_jobs.extend(jobs)
                    self.logger.info(f"Indeed: {len(jobs)} jobs found")
                except Exception as e:
                    stats.indeed_errors += 1
                    self.logger.error(f"Indeed scraping failed: {e}")
                    if CONFIG['telegram']['error_notifications']:
                        self.telegram.send_error(f"Indeed scraping failed: {e}")
            
            if CONFIG['naukri']['enabled']:
                self.logger.info("Scraping Naukri...")
                try:
                    jobs = self.naukri_scraper.scrape()
                    stats.naukri_jobs = len(jobs)
                    all_jobs.extend(jobs)
                    self.logger.info(f"Naukri: {len(jobs)} jobs found")
                except Exception as e:
                    stats.naukri_errors += 1
                    self.logger.error(f"Naukri scraping failed: {e}")
                    if CONFIG['telegram']['error_notifications']:
                        self.telegram.send_error(f"Naukri scraping failed: {e}")
            
            if CONFIG['superset']['enabled']:
                self.logger.info("Scraping Superset...")
                try:
                    jobs = self.superset_scraper.scrape()
                    stats.superset_jobs = len(jobs)
                    all_jobs.extend(jobs)
                    self.logger.info(f"Superset: {len(jobs)} jobs found")
                except Exception as e:
                    stats.superset_errors += 1
                    self.logger.error(f"Superset scraping failed: {e}")
                    if CONFIG['telegram']['error_notifications']:
                        self.telegram.send_error(f"Superset scraping failed: {e}")
            
            # Save jobs to database
            if all_jobs:
                self.logger.info(f"Saving {len(all_jobs)} jobs to database...")
                new_count, duplicate_count = self.db.save_jobs(all_jobs)
                stats.new_jobs = new_count
                stats.duplicate_jobs = duplicate_count
                self.logger.info(f"Saved {new_count} new jobs, {duplicate_count} duplicates")
            
            # Update total jobs count
            stats.total_jobs_in_db = self.db.get_total_jobs_count()
            
            # Post to Telegram
            if CONFIG['telegram']['enabled'] and all_jobs:
                self.logger.info(f"Posting {len(all_jobs)} jobs to Telegram...")
                try:
                    message_ids = self.telegram.post_jobs(all_jobs)
                    stats.telegram_posts = len(message_ids)
                    self.logger.info(f"Posted {len(message_ids)} jobs to Telegram")
                except Exception as e:
                    stats.telegram_errors += 1
                    self.logger.error(f"Telegram posting failed: {e}")
                    if CONFIG['telegram']['error_notifications']:
                        self.telegram.send_error(f"Telegram posting failed: {e}")
            
            # Send summary
            if CONFIG['telegram']['send_summary']:
                self.telegram.send_summary(stats)
            
            # Save stats
            self._save_stats(stats)
            
            self.logger.info("Scraping cycle completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Scraping cycle failed: {e}")
            if CONFIG['telegram']['error_notifications']:
                self.telegram.send_error(f"Scraping cycle failed: {e}")
        
        finally:
            stats.end_time = datetime.now()
        
        return stats
    
    def _save_stats(self, stats: ScrapingStats) -> None:
        """Save scraping statistics"""
        try:
            stats_dict = {
                'timestamp': stats.start_time.timestamp(),
                'linkedin_jobs': stats.linkedin_jobs,
                'indeed_jobs': stats.indeed_jobs,
                'naukri_jobs': stats.naukri_jobs,
                'superset_jobs': stats.superset_jobs,
                'linkedin_errors': stats.linkedin_errors,
                'indeed_errors': stats.indeed_errors,
                'naukri_errors': stats.naukri_errors,
                'superset_errors': stats.superset_errors,
                'new_jobs': stats.new_jobs,
                'duplicate_jobs': stats.duplicate_jobs,
                'total_jobs_in_db': stats.total_jobs_in_db,
                'telegram_posts': stats.telegram_posts,
                'telegram_errors': stats.telegram_errors
            }
            
            self.db.save_scraping_stats(stats_dict)
            self.logger.debug("Saved scraping statistics")
            
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
    
    def run_continuous(self, interval_hours: int = 6) -> None:
        """Run scraping continuously at specified intervals"""
        self._running = True
        
        try:
            while self._running:
                start_time = datetime.now()
                
                self.logger.info(f"Starting continuous run at {start_time}")
                
                # Run scraping cycle
                self.run()
                
                # Calculate sleep time
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, interval_hours * 3600 - elapsed)
                
                self.logger.info(f"Next run in {sleep_time/3600:.1f} hours...")
                
                # Sleep in smaller chunks to allow graceful shutdown
                chunk_size = min(3600, sleep_time)  # 1 hour chunks
                for i in range(int(sleep_time // chunk_size)):
                    if not self._running:
                        break
                    time.sleep(chunk_size)
                
                # Sleep remaining time
                if self._running:
                    remaining = sleep_time % chunk_size
                    if remaining > 0:
                        time.sleep(remaining)
        
        except KeyboardInterrupt:
            self.logger.info("Shutting down gracefully...")
        except Exception as e:
            self.logger.error(f"Continuous run failed: {e}")
            if CONFIG['telegram']['error_notifications']:
                self.telegram.send_error(f"Continuous run failed: {e}")
        
        finally:
            self._running = False
            self.cleanup()
    
    def stop(self) -> None:
        """Stop continuous running"""
        self._running = False
    
    def cleanup(self) -> None:
        """Clean up resources"""
        self.logger.info("Cleaning up resources...")
        
        try:
            self.browser_manager.close_browser()
            self.http_client.close()
            self.telegram.close()
            self.db.close()
            self.logger.info("Resources cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    def get_recent_jobs(self, hours: int = 24) -> List[Job]:
        """Get recently scraped jobs"""
        return self.db.get_recent_jobs(hours)
    
    def search_jobs(self, query: str, limit: int = 50) -> List[Job]:
        """Search jobs by query"""
        all_jobs = self.db.get_all_jobs(limit)
        query_lower = query.lower()
        
        return [
            job for job in all_jobs 
            if query_lower in job.title.lower() or 
               query_lower in job.company.lower() or
               query_lower in job.description.lower()
        ]
    
    def export_jobs(self, format: str = 'csv', filename: str = None) -> str:
        """Export jobs to CSV or JSON"""
        try:
            jobs = self.db.get_all_jobs()
            
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"jobs_{timestamp}.{format}"
            
            file_path = os.path.join(CONFIG['paths']['exports_dir'], filename)
            
            if format.lower() == 'csv':
                self._export_to_csv(jobs, file_path)
            elif format.lower() == 'json':
                self._export_to_json(jobs, file_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Exported {len(jobs)} jobs to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise
    
    def _export_to_csv(self, jobs: List[Job], file_path: str) -> None:
        """Export jobs to CSV"""
        import pandas as pd
        
        # Convert jobs to DataFrame
        job_dicts = [job.to_dict() for job in jobs]
        df = pd.DataFrame(job_dicts)
        
        # Reorder and select columns
        columns = ['title', 'company', 'location', 'url', 'source', 
                   'experience', 'salary', 'posted_date', 'is_remote', 'is_fresh']
        
        for col in columns:
            if col in df.columns:
                continue
            df[col] = ''
        
        df = df[columns]
        
        # Save to CSV
        df.to_csv(file_path, index=False)
    
    def _export_to_json(self, jobs: List[Job], file_path: str) -> None:
        """Export jobs to JSON"""
        job_dicts = [job.to_dict() for job in jobs]
        
        with open(file_path, 'w') as f:
            json.dump(job_dicts, f, indent=2)
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up old jobs from database"""
        deleted_count = self.db.cleanup_old_jobs(days)
        self.logger.info(f"Deleted {deleted_count} jobs older than {days} days")
        return deleted_count