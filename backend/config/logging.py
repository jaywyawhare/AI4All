import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
import sys

def setup_logging():
    """Setup comprehensive logging configuration for all services."""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create temp directories
    Path("temp_audio").mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter with timestamp and service name
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    all_logs_file = logs_dir / f"all_services_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        all_logs_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_logs_file = logs_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_logs_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Service-specific loggers
    services = [
        'main',
        'audio_service',
        'gemini_service', 
        'weather_service',
        'crop_service',
        'health_service',
        'scheme_service',
        'sarvam_service'
    ]
    
    for service in services:
        service_logger = logging.getLogger(service)
        service_logger.setLevel(logging.DEBUG)
        
        # Service-specific file handler
        service_log_file = logs_dir / f"{service}_{datetime.now().strftime('%Y%m%d')}.log"
        service_handler = logging.handlers.RotatingFileHandler(
            service_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        service_handler.setLevel(logging.DEBUG)
        service_handler.setFormatter(formatter)
        service_logger.addHandler(service_handler)
    
    # Set specific log levels for external libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific service."""
    return logging.getLogger(name)

# Initialize logging when module is imported
setup_logging() 