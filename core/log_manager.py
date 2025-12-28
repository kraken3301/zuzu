# ============================================================================
# LOG MANAGER - Centralized Logging
# ============================================================================

import logging
import os
from datetime import datetime
from typing import Optional
from .config import CONFIG


class LogManager:
    """Centralized logging manager"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger with consistent formatting"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        try:
            os.makedirs(CONFIG['paths']['logs_dir'], exist_ok=True)
            log_file = os.path.join(
                CONFIG['paths']['logs_dir'],
                f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not setup file logging: {e}")
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def setup_logging(cls) -> None:
        """Setup basic logging configuration"""
        # Ensure logs directory exists
        try:
            os.makedirs(CONFIG['paths']['logs_dir'], exist_ok=True)
        except Exception:
            pass
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )