"""
Unit tests for the logging configuration module.
"""

import logging
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.logger import setup_logging, get_logger


class TestSetupLogging:
    """Test cases for the setup_logging function."""
    
    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = Path(temp_dir) / "logs" / "test.log"
            
            # Directory shouldn't exist initially
            assert not log_file_path.parent.exists()
            
            setup_logging(log_file_path)
            
            # Directory should be created
            assert log_file_path.parent.exists()
    
    def test_setup_logging_configures_root_logger(self):
        """Test that setup_logging configures the root logger with correct level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = Path(temp_dir) / "test.log"
            
            setup_logging(log_file_path, logging.DEBUG)
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
    
    def test_setup_logging_configures_handlers(self):
        """Test that setup_logging configures both console and file handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = Path(temp_dir) / "test.log"
            
            setup_logging(log_file_path)
            
            root_logger = logging.getLogger()
            
            # Should have 2 handlers (console and file)
            assert len(root_logger.handlers) >= 2
            
            # Find console and file handlers
            console_handler = None
            file_handler = None
            
            for handler in root_logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
                    console_handler = handler
                elif hasattr(handler, 'baseFilename'):
                    file_handler = handler
            
            # Console handler should exist and be set to ERROR level
            assert console_handler is not None
            assert console_handler.level == logging.ERROR
            
            # File handler should exist and be set to INFO level
            assert file_handler is not None
            assert file_handler.level == logging.INFO
    
    def test_console_handler_only_shows_errors(self):
        """Test that console handler only shows ERROR and CRITICAL messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = Path(temp_dir) / "test.log"
            
            # Use StringIO to capture stderr output
            from io import StringIO
            captured_stderr = StringIO()
            
            # Temporarily replace sys.stderr before setting up logging
            original_stderr = sys.stderr
            sys.stderr = captured_stderr
            
            try:
                setup_logging(log_file_path, logging.DEBUG)
                logger = logging.getLogger("test")
                
                # Log messages at different levels
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")
                logger.critical("Critical message")
                
                # Force handlers to flush
                for handler in logging.getLogger().handlers:
                    handler.flush()
                
                # Get captured output
                stderr_output = captured_stderr.getvalue()
                
                # Only ERROR and CRITICAL should appear on console
                assert "Error message" in stderr_output
                assert "Critical message" in stderr_output
                assert "Debug message" not in stderr_output
                assert "Info message" not in stderr_output
                assert "Warning message" not in stderr_output
                
            finally:
                # Restore original stderr
                sys.stderr = original_stderr
    
    def test_file_handler_logs_info_and_above(self):
        """Test that file handler logs INFO and above messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = Path(temp_dir) / "test.log"
            
            setup_logging(log_file_path, logging.DEBUG)
            
            logger = logging.getLogger("test")
            
            # Log messages at different levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            
            # Force handlers to flush
            for handler in logging.getLogger().handlers:
                handler.flush()
            
            # Read log file content
            if log_file_path.exists():
                log_content = log_file_path.read_text()
                
                # Should contain INFO, WARNING, ERROR, CRITICAL but not DEBUG
                assert "Info message" in log_content
                assert "Warning message" in log_content
                assert "Error message" in log_content
                assert "Critical message" in log_content
                assert "Debug message" not in log_content
    
    def test_log_format_is_json(self):
        """Test that log messages are formatted as JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = Path(temp_dir) / "test.log"
            
            setup_logging(log_file_path, logging.INFO)
            
            logger = logging.getLogger("test")
            logger.info("Test JSON format")
            
            # Force handlers to flush
            for handler in logging.getLogger().handlers:
                handler.flush()
            
            # Read log file and verify JSON format
            if log_file_path.exists():
                log_content = log_file_path.read_text().strip()
                if log_content:
                    # Each line should be valid JSON
                    for line in log_content.split('\n'):
                        if line.strip():
                            try:
                                log_entry = json.loads(line)
                                assert 'asctime' in log_entry
                                assert 'name' in log_entry
                                assert 'levelname' in log_entry
                                assert 'message' in log_entry
                            except json.JSONDecodeError:
                                pytest.fail(f"Log line is not valid JSON: {line}")


class TestGetLogger:
    """Test cases for the get_logger function."""
    
    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a logging.Logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_with_different_names(self):
        """Test that get_logger returns different loggers for different names."""
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")
        
        assert logger1.name == "test1"
        assert logger2.name == "test2"
        assert logger1 is not logger2
    
    def test_get_logger_with_same_name_returns_same_instance(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        
        assert logger1 is logger2


class TestIntegration:
    """Integration tests for the logging system."""
    
    def test_full_logging_workflow(self):
        """Test the complete logging workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = Path(temp_dir) / "integration_test.log"
            
            # Setup logging
            setup_logging(log_file_path, logging.INFO)
            
            # Get logger and log messages
            logger = get_logger("integration_test")
            logger.info("Integration test started")
            logger.warning("This is a warning")
            logger.error("This is an error")
            
            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()
            
            # Verify log file exists and contains expected content
            assert log_file_path.exists()
            log_content = log_file_path.read_text()
            assert "Integration test started" in log_content
            assert "This is a warning" in log_content
            assert "This is an error" in log_content
            
            # Verify JSON format
            for line in log_content.strip().split('\n'):
                if line.strip():
                    log_entry = json.loads(line)
                    assert log_entry['name'] == 'integration_test'
                    assert log_entry['levelname'] in ['INFO', 'WARNING', 'ERROR']