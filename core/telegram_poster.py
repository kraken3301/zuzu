# ============================================================================
# TELEGRAM POSTER - Post Jobs to Telegram Channel
# ============================================================================

import time
import random
import asyncio
from typing import List, Optional
from datetime import datetime

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter

from core.models import Job, ScrapingStats
from core.config import CONFIG
from core.log_manager import LogManager


class TelegramPoster:
    """Post jobs to Telegram channel"""
    
    def __init__(self):
        self.logger = LogManager.get_logger('TelegramPoster')
        self.bot = None
        self._loop = None
        
        if CONFIG['telegram']['enabled']:
            self.bot = Bot(token=CONFIG['telegram']['bot_token'])
            self._loop = asyncio.new_event_loop()
    
    def _run_async(self, coro):
        """Run async coroutine safely in notebooks or scripts"""
        if not self._loop:
            return None
        
        try:
            # Check if a loop is already running (e.g. in Colab/Jupyter)
            try:
                running_loop = asyncio.get_running_loop()
                if running_loop:
                    # If we're in an existing event loop, create a task instead
                    return running_loop.create_task(coro)
            except RuntimeError:
                # No loop running, use our own loop
                pass
            
            # Use our own event loop
            return self._loop.run_until_complete(coro)
        except Exception as e:
            self.logger.error(f"Async error: {e}")
            return None
    
    async def _test_connection_async(self) -> bool:
        """Test Telegram bot connection (async version)"""
        if not self.bot:
            return False
        
        try:
            bot_info = await self.bot.get_me()
            self.logger.info(f"Connected to Telegram bot: @{bot_info.username}")
            return True
        except Exception as e:
            self.logger.error(f"Telegram connection failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        return self._run_async(self._test_connection_async())
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        now = datetime.now()
        start_hour = CONFIG['schedule']['quiet_hours_start']
        end_hour = CONFIG['schedule']['quiet_hours_end']
        
        if start_hour > end_hour:  # Overnight quiet hours (e.g., 23-7)
            return now.hour >= start_hour or now.hour < end_hour
        else:
            return start_hour <= now.hour < end_hour
    
    def post_job(self, job: Job) -> Optional[int]:
        """Post single job, returns message_id"""
        if not CONFIG['telegram']['enabled'] or not self.bot:
            return None
        
        if self._is_quiet_hours():
            self.logger.debug("Quiet hours - skipping post")
            return None
        
        try:
            message = job.to_telegram_message()
            
            # Try MarkdownV2 first (required for proper escaping)
            try:
                result = self._run_async(self.bot.send_message(
                    chat_id=CONFIG['telegram']['channel_id'],
                    text=message,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    disable_web_page_preview=True
                ))
            except:
                # Fallback to plain text
                plain_message = self._strip_formatting(message)
                result = self._run_async(self.bot.send_message(
                    chat_id=CONFIG['telegram']['channel_id'],
                    text=plain_message,
                    disable_web_page_preview=True
                ))
            
            if result:
                self.logger.debug(f"Posted job: {job.title}")
                return result.message_id if hasattr(result, 'message_id') else None
            return None
            
        except RetryAfter as e:
            self.logger.warning(f"Rate limited, waiting {e.retry_after}s")
            time.sleep(e.retry_after)
            return self.post_job(job)
        except Exception as e:
            self.logger.error(f"Failed to post job: {e}")
            return None
    
    def _strip_formatting(self, text: str) -> str:
        """Remove Markdown formatting from text"""
        # Remove MarkdownV2 escape characters
        text = text.replace('\\', '')
        
        # Remove formatting characters
        text = text.replace('*', '').replace('_', '').replace('`', '')
        text = text.replace('[', '').replace(']', '')
        text = text.replace('(', '').replace(')', '')
        
        return text
    
    def post_jobs(self, jobs: List[Job]) -> List[int]:
        """Post multiple jobs with rate limiting"""
        message_ids = []
        
        for job in jobs:
            msg_id = self.post_job(job)
            if msg_id:
                message_ids.append(msg_id)
            
            # Delay between posts
            delay = random.uniform(
                CONFIG['telegram']['post_delay_min'],
                CONFIG['telegram']['post_delay_max']
            )
            time.sleep(delay)
        
        return message_ids
    
    def send_summary(self, stats: ScrapingStats):
        """Send run summary"""
        if not CONFIG['telegram']['enabled'] or not self.bot:
            return False
        
        if self._is_quiet_hours():
            self.logger.debug("Quiet hours - skipping summary")
            return False
        
        try:
            message = self._build_summary_message(stats)
            
            result = self._run_async(self.bot.send_message(
                chat_id=CONFIG['telegram']['channel_id'],
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True
            ))
            
            if result:
                self.logger.info("Sent scraping summary to Telegram")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to send summary: {e}")
            return False
    
    def _build_summary_message(self, stats: ScrapingStats) -> str:
        """Build summary message"""
        duration = stats.duration_seconds()
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        message = "📊 *Scraping Summary*\n\n"
        message += f"🕒 *Duration*: {int(hours)}h {int(minutes)}m {int(seconds)}s\n"
        message += f"🔍 *Total Jobs Found*: {stats.total_jobs()}\n"
        message += f"📝 *New Jobs*: {stats.new_jobs}\n"
        message += f"🔄 *Duplicates*: {stats.duplicate_jobs}\n"
        message += f"💾 *Total in DB*: {stats.total_jobs_in_db}\n\n"
        
        # Source breakdown
        if stats.linkedin_jobs > 0:
            message += f"🔵 *LinkedIn*: {stats.linkedin_jobs} jobs\n"
        if stats.indeed_jobs > 0:
            message += f"🟢 *Indeed*: {stats.indeed_jobs} jobs\n"
        if stats.naukri_jobs > 0:
            message += f"🟣 *Naukri*: {stats.naukri_jobs} jobs\n"
        if stats.superset_jobs > 0:
            message += f"🟡 *Superset*: {stats.superset_jobs} jobs\n"
        
        # Error reporting
        total_errors = stats.total_errors()
        if total_errors > 0:
            message += f"\n⚠️ *Errors*: {total_errors}\n"
            if stats.linkedin_errors > 0:
                message += f"  • LinkedIn: {stats.linkedin_errors}\n"
            if stats.indeed_errors > 0:
                message += f"  • Indeed: {stats.indeed_errors}\n"
            if stats.naukri_errors > 0:
                message += f"  • Naukri: {stats.naukri_errors}\n"
            if stats.superset_errors > 0:
                message += f"  • Superset: {stats.superset_errors}\n"
        
        # Telegram stats
        if stats.telegram_posts > 0:
            message += f"\n📢 *Telegram Posts*: {stats.telegram_posts}\n"
        if stats.telegram_errors > 0:
            message += f"📢 *Telegram Errors*: {stats.telegram_errors}\n"
        
        message += f"\n🗓️ *Completed*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def send_error(self, error_message: str):
        """Send error notification"""
        if not CONFIG['telegram']['enabled'] or not self.bot:
            return False
        
        if not CONFIG['telegram']['error_notifications']:
            return False
        
        try:
            # Send to admin chat if specified, otherwise to main channel
            chat_id = CONFIG['telegram']['admin_chat_id'] or CONFIG['telegram']['channel_id']
            
            message = f"❗ *Error Alert*\n\n{error_message}"
            
            result = self._run_async(self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True
            ))
            
            if result:
                self.logger.info("Sent error notification to Telegram")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to send error notification: {e}")
            return False
    
    def close(self) -> None:
        """Close Telegram poster"""
        if self._loop:
            try:
                self._loop.close()
            except Exception:
                pass
            self._loop = None