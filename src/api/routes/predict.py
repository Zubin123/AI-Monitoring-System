"""Prediction routes."""
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from src.models.transaction import Transaction
from src.models.prediction import PredictionResponse
from src.api.dependencies import get_model_service, get_prediction_repository
from src.services import ModelService
from src.repositories import PredictionRepository
from src.core import get_logger, ModelLoadError, PredictionError, ValidationError

logger = get_logger(__name__)

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
def predict(
    tx: Transaction,
    model_service: ModelService = Depends(get_model_service),
    prediction_repository: PredictionRepository = Depends(get_prediction_repository),
) -> PredictionResponse:
    """
    Make a fraud detection prediction.
    
    Args:
        tx: Transaction data
        model_service: Model service instance
        prediction_repository: Prediction repository instance
    
    Returns:
        PredictionResponse: Prediction result
    
    Raises:
        HTTPException: If prediction fails
    """
    start_time = time.time()
    
    try:
        # Convert transaction to dict
        features = tx.model_dump()
        
        # Make prediction
        result = model_service.predict(features)
        prediction = result["prediction"]
        probability = result["probability"]
        
        # Calculate latency
        latency_ms = round((time.time() - start_time) * 1000, 2)
        timestamp = datetime.utcnow().isoformat()
        
        # Save prediction to database
        try:
            prediction_repository.save_prediction(
                features=features,
                prediction=prediction,
                probability=probability,
                latency_ms=latency_ms,
                timestamp=timestamp,
            )
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Failed to save prediction to database: {e}")
        
        logger.info(
            f"Prediction made: {prediction}, "
            f"probability={probability:.4f}, "
            f"latency={latency_ms}ms"
        )
        
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            latency_ms=latency_ms,
            timestamp=timestamp,
        )
        
    except ModelLoadError as e:
        logger.error(f"Model not loaded: {e}")
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please check server logs."
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except PredictionError as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

