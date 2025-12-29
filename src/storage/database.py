"""Database connection management with context managers."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator
from threading import Lock

from src.config import get_settings
from src.core import get_logger, DatabaseError

logger = get_logger(__name__)


class DatabaseManager:
    """Database connection manager with context manager support."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to database file (defaults to settings)
        """
        settings = get_settings()
        self.db_path = db_path or settings.db_path
        self._lock = Lock()
        self._initialized = False
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_schema()
    
    def _initialize_schema(self) -> None:
        """Initialize database schema if not exists."""
        if self._initialized:
            return
        
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS live_predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        features TEXT NOT NULL,
                        prediction INTEGER NOT NULL,
                        probability REAL NOT NULL,
                        latency_ms REAL NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON live_predictions(timestamp)
                """)
                conn.commit()
                self._initialized = True
                logger.info(f"Database schema initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection with context manager.
        
        Yields:
            sqlite3.Connection: Database connection
        
        Raises:
            DatabaseError: If connection fails
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.debug(f"Database connection opened: {self.db_path}")
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Unexpected database error: {e}")
            raise DatabaseError(f"Unexpected database error: {e}")
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed")
    
    def execute(self, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        """
        Execute a query with automatic connection management.
        
        Args:
            query: SQL query
            params: Query parameters
        
        Returns:
            sqlite3.Cursor: Query cursor
        
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params or ())
                return cursor
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    def health_check(self) -> bool:
        """
        Check database health.
        
        Returns:
            bool: True if database is accessible
        """
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance (singleton pattern).
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# Backward compatibility function
def get_connection():
    """
    Get a database connection (backward compatibility).
    
    Note: This function is deprecated. Use DatabaseManager.get_connection() instead.
    
    Returns:
        sqlite3.Connection: Database connection
    """
    logger.warning("get_connection() is deprecated. Use DatabaseManager.get_connection() instead.")
    manager = get_database_manager()
    return manager.get_connection().__enter__()
