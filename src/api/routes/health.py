"""Health check routes."""
from fastapi import APIRouter, Depends

from src.models.prediction import HealthResponse
from src.api.dependencies import get_model_service, get_db_manager
from src.services import ModelService
from src.storage import DatabaseManager
from src.core import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(
    model_service: ModelService = Depends(get_model_service),
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Health status information
    """
    try:
        model_loaded = model_service.is_loaded()
        database_connected = db_manager.health_check()
        
        if model_loaded and database_connected:
            status = "healthy"
            message = "API is operational"
        else:
            status = "degraded"
            issues = []
            if not model_loaded:
                issues.append("model not loaded")
            if not database_connected:
                issues.append("database not connected")
            message = f"API is degraded: {', '.join(issues)}"
        
        logger.debug(f"Health check: status={status}, model={model_loaded}, db={database_connected}")
        
        return HealthResponse(
            status=status,
            message=message,
            model_loaded=model_loaded,
            database_connected=database_connected,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            message=f"Health check failed: {str(e)}",
            model_loaded=False,
            database_connected=False,
        )

