"""Dependency injection for FastAPI."""
from functools import lru_cache

from src.services import ModelService
from src.repositories import PredictionRepository
from src.storage import DatabaseManager, get_database_manager
from src.core import get_logger

logger = get_logger(__name__)


@lru_cache()
def get_model_service() -> ModelService:
    """
    Get model service instance (singleton).
    
    Returns:
        ModelService: Model service instance
    """
    service = ModelService.get_instance()
    if not service.is_loaded():
        service.load_model()
    return service


def get_prediction_repository() -> PredictionRepository:
    """
    Get prediction repository instance.
    
    Returns:
        PredictionRepository: Prediction repository instance
    """
    return PredictionRepository()


def get_db_manager() -> DatabaseManager:
    """
    Get database manager instance.
    
    Returns:
        DatabaseManager: Database manager instance
    """
    return get_database_manager()

