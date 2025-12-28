# ============================================================================
# DATABASE MANAGER - SQLite Job Storage
# ============================================================================

import os
import sqlite3
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from .models import Job
from .config import CONFIG
from .log_manager import LogManager


class DatabaseManager:
    """SQLite database manager for job storage"""
    
    def __init__(self):
        self.logger = LogManager.get_logger('DatabaseManager')
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database connection and create tables"""
        try:
            # Ensure directory exists
            os.makedirs(CONFIG['paths']['database_dir'], exist_ok=True)
            
            # Connect to database
            db_path = os.path.join(CONFIG['paths']['database_dir'], 'jobs.db')
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.execute('PRAGMA journal_mode=WAL')
            
            # Create tables
            self._create_tables()
            
            self.logger.info(f"Database initialized: {db_path}")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                posted_date TEXT,
                experience TEXT,
                salary TEXT,
                job_id TEXT,
                is_remote INTEGER DEFAULT 0,
                is_fresh INTEGER DEFAULT 1,
                scrape_timestamp REAL NOT NULL,
                UNIQUE(url)
            )
        ''')
        
        # Stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                linkedin_jobs INTEGER DEFAULT 0,
                indeed_jobs INTEGER DEFAULT 0,
                naukri_jobs INTEGER DEFAULT 0,
                superset_jobs INTEGER DEFAULT 0,
                linkedin_errors INTEGER DEFAULT 0,
                indeed_errors INTEGER DEFAULT 0,
                naukri_errors INTEGER DEFAULT 0,
                superset_errors INTEGER DEFAULT 0,
                new_jobs INTEGER DEFAULT 0,
                duplicate_jobs INTEGER DEFAULT 0,
                total_jobs_in_db INTEGER DEFAULT 0,
                telegram_posts INTEGER DEFAULT 0,
                telegram_errors INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()
    
    def save_job(self, job: Job) -> bool:
        """Save job to database, return True if new, False if duplicate"""
        try:
            job_id = job.generate_unique_id()
            
            # Check if job already exists
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1 FROM jobs WHERE id = ?', (job_id,))
            
            if cursor.fetchone():
                # Update existing job (refresh timestamp)
                cursor.execute('''
                    UPDATE jobs SET 
                        title = ?,
                        company = ?,
                        location = ?,
                        url = ?,
                        description = ?,
                        posted_date = ?,
                        experience = ?,
                        salary = ?,
                        job_id = ?,
                        is_remote = ?,
                        is_fresh = ?,
                        scrape_timestamp = ?
                    WHERE id = ?
                ''', (
                    job.title, job.company, job.location, job.url,
                    job.description, job.posted_date, job.experience,
                    job.salary, job.job_id, int(job.is_remote),
                    int(job.is_fresh), job.scrape_timestamp, job_id
                ))
                self.conn.commit()
                return False
            else:
                # Insert new job
                cursor.execute('''
                    INSERT INTO jobs (
                        id, title, company, location, url, source, 
                        description, posted_date, experience, salary, 
                        job_id, is_remote, is_fresh, scrape_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_id, job.title, job.company, job.location, job.url,
                    job.source, job.description, job.posted_date,
                    job.experience, job.salary, job.job_id,
                    int(job.is_remote), int(job.is_fresh), job.scrape_timestamp
                ))
                self.conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save job {job.title}: {e}")
            return False
    
    def save_jobs(self, jobs: List[Job]) -> Tuple[int, int]:
        """Save multiple jobs, return (new_count, duplicate_count)"""
        new_count = 0
        duplicate_count = 0
        
        for job in jobs:
            if self.save_job(job):
                new_count += 1
            else:
                duplicate_count += 1
        
        return new_count, duplicate_count
    
    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_job(row)
        return None
    
    def get_job_by_url(self, url: str) -> Optional[Job]:
        """Get job by URL"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE url = ?', (url,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_job(row)
        return None
    
    def get_all_jobs(self, limit: int = 1000) -> List[Job]:
        """Get all jobs from database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM jobs ORDER BY scrape_timestamp DESC LIMIT ?', (limit,))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append(self._row_to_job(row))
        
        return jobs
    
    def get_recent_jobs(self, hours: int = 24) -> List[Job]:
        """Get jobs scraped in the last N hours"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM jobs 
            WHERE scrape_timestamp >= ? 
            ORDER BY scrape_timestamp DESC
        ''', (cutoff,))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append(self._row_to_job(row))
        
        return jobs
    
    def get_jobs_by_source(self, source: str, limit: int = 100) -> List[Job]:
        """Get jobs by source"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM jobs 
            WHERE source = ? 
            ORDER BY scrape_timestamp DESC 
            LIMIT ?
        ''', (source, limit))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append(self._row_to_job(row))
        
        return jobs
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Delete jobs older than N days"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM jobs WHERE scrape_timestamp < ?', (cutoff,))
        deleted_count = cursor.rowcount
        self.conn.commit()
        return deleted_count
    
    def get_total_jobs_count(self) -> int:
        """Get total number of jobs in database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM jobs')
        return cursor.fetchone()[0]
    
    def save_scraping_stats(self, stats: Dict[str, Any]) -> None:
        """Save scraping statistics"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_stats (
                    timestamp, linkedin_jobs, indeed_jobs, naukri_jobs, superset_jobs,
                    linkedin_errors, indeed_errors, naukri_errors, superset_errors,
                    new_jobs, duplicate_jobs, total_jobs_in_db, telegram_posts, telegram_errors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stats.get('timestamp', datetime.now().timestamp()),
                stats.get('linkedin_jobs', 0),
                stats.get('indeed_jobs', 0),
                stats.get('naukri_jobs', 0),
                stats.get('superset_jobs', 0),
                stats.get('linkedin_errors', 0),
                stats.get('indeed_errors', 0),
                stats.get('naukri_errors', 0),
                stats.get('superset_errors', 0),
                stats.get('new_jobs', 0),
                stats.get('duplicate_jobs', 0),
                stats.get('total_jobs_in_db', 0),
                stats.get('telegram_posts', 0),
                stats.get('telegram_errors', 0)
            ))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save scraping stats: {e}")
    
    def _row_to_job(self, row: Tuple) -> Job:
        """Convert database row to Job object"""
        return Job(
            title=row[1],
            company=row[2],
            location=row[3],
            url=row[4],
            source=row[5],
            description=row[6] or "",
            posted_date=row[7] or "",
            experience=row[8] or "",
            salary=row[9] or "",
            job_id=row[10] or "",
            is_remote=bool(row[11]),
            is_fresh=bool(row[12]),
            scrape_timestamp=row[13]
        )
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None