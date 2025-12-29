"""Storage package for database operations."""
from src.storage.database import (
    DatabaseManager,
    get_database_manager,
    get_connection,  # Backward compatibility
)

__all__ = [
    "DatabaseManager",
    "get_database_manager",
    "get_connection",
]

