"""
Application-wide logging system for Mango Tango CLI.

Provides structured JSON logging with:
- Console output (ERROR and CRITICAL levels only) to stderr
- File output (INFO and above) with automatic rotation
- Configurable log levels via CLI flag
"""

import logging
import logging.config
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict


def setup_logging(log_file_path: Path, level: int = logging.INFO) -> None:
    """
    Configure application-wide logging with structured JSON output.

    Args:
        log_file_path: Path to the log file
        level: Minimum logging level (default: logging.INFO)
    """
    # Ensure the log directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Logging configuration dictionary
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "json",
                "stream": sys.stderr,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(log_file_path),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {"level": level, "handlers": ["console", "file"]},
    }

    # Apply the configuration
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
