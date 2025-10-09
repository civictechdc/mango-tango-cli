"""
Application-wide logging system for Mango Tango CLI.

Provides structured JSON logging with:
- Console output (ERROR and CRITICAL levels only) to stderr
- File output (INFO and above) with automatic rotation
- Configurable log levels via CLI flag
"""

import logging
import logging.config
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict


class ContextEnrichmentFilter(logging.Filter):
    """
    Filter that enriches log records with contextual information.

    Adds:
    - process_id: Current process ID
    - thread_id: Current thread ID
    - app_version: Application version (if available)
    """

    def __init__(self, app_version: str = "unknown"):
        super().__init__()
        self.app_version = app_version
        self.process_id = os.getpid()

    def filter(self, record: logging.LogRecord) -> bool:
        # Add contextual information to the log record
        record.process_id = self.process_id
        record.thread_id = threading.get_ident()
        record.app_version = self.app_version
        return True


def setup_logging(
    log_file_path: Path, level: int = logging.INFO, app_version: str = "unknown"
) -> None:
    """
    Configure application-wide logging with structured JSON output.

    Args:
        log_file_path: Path to the log file
        level: Minimum logging level (default: logging.INFO)
        app_version: Application version to include in logs
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
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(process_id)s %(thread_id)s %(app_version)s",
                "rename_fields": {"levelname": "level", "asctime": "timestamp"},
            }
        },
        "filters": {
            "context_enrichment": {
                "()": ContextEnrichmentFilter,
                "app_version": app_version,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "json",
                "filters": ["context_enrichment"],
                "stream": sys.stderr,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "json",
                "filters": ["context_enrichment"],
                "filename": str(log_file_path),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {"level": level, "handlers": ["console", "file"]},
        "loggers": {
            # Third-party library loggers - keep them quieter by default
            "urllib3": {"level": "WARNING", "propagate": True},
            "requests": {"level": "WARNING", "propagate": True},
            "dash": {"level": "WARNING", "propagate": True},
            "plotly": {"level": "WARNING", "propagate": True},
            "shiny": {"level": "WARNING", "propagate": True},
            "uvicorn": {"level": "WARNING", "propagate": True},
            "starlette": {"level": "WARNING", "propagate": True},
            # Application loggers - inherit from root level
            "mangotango": {"level": level, "propagate": True},
            "app": {"level": level, "propagate": True},
            "analyzers": {"level": level, "propagate": True},
            "components": {"level": level, "propagate": True},
            "storage": {"level": level, "propagate": True},
            "importing": {"level": level, "propagate": True},
        },
    }

    # Apply the configuration
    logging.config.dictConfig(config)

    # Set up global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions by logging them."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt be handled normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger = logging.getLogger("uncaught_exception")
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_value),
            },
        )

    # Install the global exception handler
    sys.excepthook = handle_exception


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
