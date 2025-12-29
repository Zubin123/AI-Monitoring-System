"""Centralized path management for the application."""
from pathlib import Path


def get_base_dir() -> Path:
    """Get the base directory of the project (2 levels up from this file)."""
    return Path(__file__).resolve().parents[2]


def get_artifacts_dir() -> Path:
    """Get the artifacts directory path."""
    return get_base_dir() / "artifacts"


def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_base_dir() / "data"


def get_reference_data_dir() -> Path:
    """Get the reference data directory path."""
    return get_data_dir() / "reference"


def get_logs_dir() -> Path:
    """Get the logs directory path."""
    logs_dir = get_base_dir() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir

