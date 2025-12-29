"""Logging configuration using loguru."""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

# Track if logging has been initialized
_logging_initialized = False


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None,
    log_rotation: Optional[str] = None,
    log_retention: Optional[str] = None,
) -> None:
    """
    Configure loguru logger with file and console handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_format: Format type ("json" or "text")
        log_rotation: Log rotation size (e.g., "10 MB")
        log_retention: Log retention period (e.g., "30 days")
    """
    from src.config import get_settings
    settings = get_settings()
    
    # Use provided values or fall back to settings
    level = log_level or settings.log_level
    file_path = log_file or settings.log_file
    format_type = log_format or settings.log_format
    rotation = log_rotation or settings.log_rotation
    retention = log_retention or settings.log_retention
    
    # Remove default handler
    logger.remove()
    
    # Define formats for text mode
    if format_type != "json":
        # Human-readable text format
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
    
    # Console handler (stderr)
    if format_type == "json":
        # For JSON format, use serialize=True
        logger.add(
            sys.stderr,
            serialize=True,
            level=level,
            backtrace=True,
            diagnose=True,
        )
    else:
        # For text format, use the format string
        logger.add(
            sys.stderr,
            format=console_format,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    
    # File handler
    if file_path:
        # Ensure log directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "json":
            # For JSON format, use serialize=True
            logger.add(
                str(file_path),
                serialize=True,
                level=level,
                rotation=rotation,
                retention=retention,
                compression="zip",
                backtrace=True,
                diagnose=True,
                enqueue=True,  # Thread-safe logging
            )
        else:
            # For text format, use the format string
            logger.add(
                str(file_path),
                format=file_format,
                level=level,
                rotation=rotation,
                retention=retention,
                compression="zip",
                backtrace=True,
                diagnose=True,
                enqueue=True,  # Thread-safe logging
            )
    
    global _logging_initialized
    _logging_initialized = True
    
    logger.info(f"Logging configured: level={level}, file={file_path}, format={format_type}")
    
    # Force flush to ensure log file is created and written
    logger.info("Logging system initialized successfully")


def get_logger(name: Optional[str] = None):
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    # Ensure logging is initialized if it hasn't been yet
    global _logging_initialized
    if not _logging_initialized:
        try:
            from src.config import get_settings
            setup_logging()
        except Exception:
            # If settings can't be loaded, use basic console logging
            logger.remove()
            logger.add(sys.stderr, level="INFO")
            _logging_initialized = True
    
    if name:
        return logger.bind(name=name)
    return logger


# Don't initialize logging on import - let it be called explicitly
# This prevents issues with circular imports and ensures settings are loaded first

