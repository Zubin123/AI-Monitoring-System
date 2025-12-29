"""Custom exception classes for the application."""
from typing import Optional


class ModelMonitoringException(Exception):
    """Base exception for all model monitoring errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return string representation."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ModelLoadError(ModelMonitoringException):
    """Raised when model loading fails."""
    pass


class ConfigurationError(ModelMonitoringException):
    """Raised when configuration is invalid."""
    pass


class DatabaseError(ModelMonitoringException):
    """Raised when database operations fail."""
    pass


class DriftDetectionError(ModelMonitoringException):
    """Raised when drift detection fails."""
    pass


class ValidationError(ModelMonitoringException):
    """Raised when data validation fails."""
    pass


class PredictionError(ModelMonitoringException):
    """Raised when prediction fails."""
    pass

