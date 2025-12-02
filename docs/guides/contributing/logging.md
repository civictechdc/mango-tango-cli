## Logging

The application uses a structured JSON logging system that provides consistent logging across all modules. The logging system automatically separates critical alerts from diagnostic information.

### Logging Architecture

- **Console Output**: Only `ERROR` and `CRITICAL` messages are displayed on stderr
- **File Output**: All messages from `INFO` level and above are written to log files
- **Log Format**: All logs are structured JSON for easy parsing and analysis
- **Log Rotation**: Log files automatically rotate at 10MB with 5 backup files retained
- **Log Location**: `~/.local/share/MangoTango/logs/mangotango.log` (varies by platform)

### Using the Logger in Your Code

#### Basic Usage

```python
from app.logger import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed debugging information")
logger.info("General information about program execution")
logger.warning("Something unexpected happened, but the program continues")
logger.error("A serious problem occurred")
logger.critical("A very serious error occurred, program may not be able to continue")
```

#### Example Log Output

**Console (stderr) - Only errors:**

```json
{"asctime": "2025-07-30 16:42:33,914", "name": "analyzers.hashtags", "levelname": "ERROR", "message": "Failed to process hashtags", "taskName": null}
```

**Log File - All info and above:**

```json
{"asctime": "2025-07-30 16:42:33,910", "name": "analyzers.hashtags", "levelname": "INFO", "message": "Starting hashtag analysis", "taskName": null}
{"asctime": "2025-07-30 16:42:33,914", "name": "analyzers.hashtags", "levelname": "ERROR", "message": "Failed to process hashtags", "taskName": null}
```

### Logging in Analyzers

When developing analyzers, add logging to help with debugging and monitoring:

```python
from app.logger import get_logger

def main(context):
    logger = get_logger(__name__)
    
    logger.info("Starting analysis", extra={
        "input_path": str(context.input_path),
        "output_path": str(context.output_path)
    })
    
    try:
        # Your analysis code here
        result = perform_analysis(context)
        
        logger.info("Analysis completed successfully", extra={
            "records_processed": len(result),
            "execution_time": time.time() - start_time
        })
        
    except Exception as e:
        logger.error("Analysis failed", extra={
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        raise
```

### Logging Best Practices

1. **Use Appropriate Log Levels**:
    
    - `DEBUG`: Detailed diagnostic information, only useful when debugging
    - `INFO`: General information about program execution
    - `WARNING`: Something unexpected happened, but the program continues
    - `ERROR`: A serious problem occurred
    - `CRITICAL`: A very serious error occurred, program may not be able to continue
2. **Include Context with `extra` Parameter**:
    
    ```python
    logger.info("Processing file", extra={
        "filename": filename,
        "file_size": file_size,
        "record_count": record_count
    })
    ```
    
3. **Log Exceptions Properly**:
    
    ```python
    try:
        risky_operation()
    except Exception as e:
        logger.error("Operation failed", exc_info=True)  # Includes stack trace
    ```
    
4. **Avoid Logging Sensitive Information**:
    
    - Never log passwords, API keys, or personal data
    - Be cautious with user-provided data

### Debugging with Logs

Users can control log verbosity when running the application:

```shell
# Default INFO level
python -m cibmangotree

# Verbose DEBUG level for troubleshooting
python -m cibmangotree --log-level DEBUG

# Only show warnings and errors in log file
python -m cibmangotree --log-level WARNING
```

### Log File Management

- Log files are automatically rotated when they reach 10MB
- Up to 5 backup files are kept (`mangotango.log.1`, `mangotango.log.2`, etc.)
- Older backup files are automatically deleted
- Log directory is created automatically if it doesn't exist

### Testing with Logs

When writing tests that involve logging:

```python
import logging
from app.logger import get_logger

def test_my_function_logs_correctly(caplog):
    with caplog.at_level(logging.INFO):
        my_function()
        
    assert "Expected log message" in caplog.text
```

# Next Steps

Once you finish reading this it's recommended to check out the [architecture](./architecture.md) section.