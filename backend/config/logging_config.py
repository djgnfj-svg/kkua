"""
Logging Configuration
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any
from app_config import settings


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colors for console output
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        if sys.stdout.isatty():  # Only add colors if output is to terminal
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': record.process,
            'thread_id': record.thread,
            'environment': settings.environment
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'room_id'):
            log_entry['room_id'] = record.room_id
        
        # Add extra data if available
        if hasattr(record, 'extra_data'):
            log_entry['extra'] = record.extra_data
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add performance metrics if available
        if hasattr(record, 'duration'):
            log_entry['performance'] = {
                'duration_ms': round(record.duration * 1000, 2),
                'operation': getattr(record, 'operation', 'unknown')
            }
        
        # Add security context if available
        if hasattr(record, 'security_event'):
            log_entry['security'] = {
                'event': record.security_event,
                'ip_address': getattr(record, 'ip_address', None),
                'user_agent': getattr(record, 'user_agent', None)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    """
    Add request context to log records
    """
    
    def filter(self, record):
        # Add request ID if available (would be set by middleware)
        record.request_id = getattr(record, 'request_id', 'N/A')
        record.user_id = getattr(record, 'user_id', 'N/A')
        record.session_id = getattr(record, 'session_id', 'N/A')
        return True


def setup_logging():
    """
    Setup centralized logging configuration with JSON structured logging
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Determine if we should use JSON formatting
    use_json_logging = os.getenv('USE_JSON_LOGGING', 'false').lower() == 'true'
    
    # Console handler with colors (human-readable for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    if use_json_logging:
        console_formatter = JSONFormatter()
    else:
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler for all logs (always use JSON for files)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/kkua.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    file_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(file_handler)
    
    # Error-only file handler (JSON format)
    error_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    error_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(error_handler)
    
    # Performance log handler
    performance_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/performance.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    performance_handler.setLevel(logging.INFO)
    performance_handler.setFormatter(JSONFormatter())
    performance_handler.addFilter(RequestContextFilter())
    
    # Create performance logger
    performance_logger = logging.getLogger('performance')
    performance_logger.setLevel(logging.INFO)
    performance_logger.addHandler(performance_handler)
    performance_logger.propagate = False  # Don't propagate to root logger
    
    # Create audit logger
    audit_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/audit.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(JSONFormatter())
    audit_handler.addFilter(RequestContextFilter())
    
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_handler)
    audit_logger.propagate = False
    
    # Security logger
    security_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/security.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(JSONFormatter())
    security_handler.addFilter(RequestContextFilter())
    
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False
    
    # Third-party loggers
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging system initialized - Environment: {settings.environment}")
    logger.info(f"Log files location: {os.path.abspath(log_dir)}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    """
    return logging.getLogger(name)


def log_performance(operation: str, duration: float, extra_data: Dict[str, Any] = None):
    """
    Log performance metrics
    """
    logger = logging.getLogger('performance')
    extra_data = extra_data or {}
    logger.info(f"PERFORMANCE: {operation} took {duration:.3f}s", extra=extra_data)


def log_audit(action: str, user_id: str, details: Dict[str, Any] = None):
    """
    Log audit events
    """
    logger = logging.getLogger('audit')
    details = details or {}
    logger.info(f"AUDIT: {action} by user {user_id}", extra=details)


def log_security(event: str, details: Dict[str, Any] = None):
    """
    Log security events
    """
    logger = logging.getLogger('security')
    details = details or {}
    logger.warning(f"SECURITY: {event}", extra=details)