"""
Configuration module for the Calendar Booking Agent.
Handles environment variables, API keys, and application settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging
import structlog

load_dotenv()

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class Config:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
 
    CALENDAR_ID: str = os.getenv("CALENDAR_ID", "")
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")

    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8501"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    CREDENTIALS_PATH: Path = Path("../credentials/service_account.json")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        missing_configs = []
        
        if not cls.GOOGLE_API_KEY:
            missing_configs.append("GOOGLE_API_KEY")
        
        if not cls.CALENDAR_ID:
            missing_configs.append("CALENDAR_ID")
        
        if not cls.CREDENTIALS_PATH.exists():
            missing_configs.append("credentials/service_account.json")
        
        if missing_configs:
            logger.error("Missing required configuration", missing=missing_configs)
            return False
        
        logger.info("Configuration validated successfully")
        return True
    
    @classmethod
    def get_calendar_id(cls) -> str:
        """Get the calendar ID, handling both primary and custom calendars."""
        if cls.CALENDAR_ID == "primary":
            return "primary"
        return cls.CALENDAR_ID

config = Config()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) 