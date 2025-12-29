"""Test script to verify logging is working."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core import setup_logging, get_logger
from src.config import get_settings

# Setup logging
setup_logging()

# Get logger
logger = get_logger(__name__)

# Test logging at different levels
logger.debug("This is a DEBUG message")
logger.info("This is an INFO message")
logger.warning("This is a WARNING message")
logger.error("This is an ERROR message")

# Get settings to show log file path
settings = get_settings()
print(f"\nLog file path: {settings.log_file}")
print(f"Log file exists: {settings.log_file.exists()}")
if settings.log_file.exists():
    print(f"Log file size: {settings.log_file.stat().st_size} bytes")
    print(f"\nFirst 10 lines of log file:")
    try:
        with open(settings.log_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:10], 1):
                print(f"{i}: {line.rstrip()}")
    except Exception as e:
        print(f"Error reading log file: {e}")

