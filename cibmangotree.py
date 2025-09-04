import argparse
import logging
import sys
from multiprocessing import freeze_support
from pathlib import Path

from analyzers import suite
from app import App, AppContext
from app.logger import setup_logging
from components import ViewContext, main_menu, splash
from meta import get_version
from storage import Storage
from terminal_tools import enable_windows_ansi_support
from terminal_tools.inception import TerminalContext

if __name__ == "__main__":
    freeze_support()
    enable_windows_ansi_support()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Mango Tango CLI - Social Media Data Analysis Tool"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )
    parser.add_argument(
        "--noop", action="store_true", help="No-operation mode for testing"
    )

    args = parser.parse_args()

    # Handle no-op mode
    if args.noop:
        print("No-op flag detected. Exiting successfully.")
        sys.exit(0)

    # Initialize storage
    storage = Storage(app_name="MangoTango", app_author="Civic Tech DC")

    # Set up logging
    log_level = getattr(logging, args.log_level)
    log_file_path = Path(storage.user_data_dir) / "logs" / "mangotango.log"
    app_version = get_version() or "development"
    setup_logging(log_file_path, log_level, app_version)

    # Get logger for main module
    logger = logging.getLogger(__name__)
    logger.info(
        "Starting Mango Tango CLI application",
        extra={"log_level": args.log_level, "log_file": str(log_file_path)},
    )

    splash()
    main_menu(
        ViewContext(
            terminal=TerminalContext(),
            app=App(context=AppContext(storage=storage, suite=suite)),
        )
    )
