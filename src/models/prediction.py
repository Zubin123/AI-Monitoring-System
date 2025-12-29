"""Pydantic models for prediction responses."""
from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Prediction response model."""
    
    prediction: int = Field(..., description="Prediction (0=legitimate, 1=fraud)", ge=0, le=1)
    probability: float = Field(..., description="Fraud probability", ge=0.0, le=1.0)
    latency_ms: float = Field(..., description="Prediction latency in milliseconds", ge=0.0)
    timestamp: str = Field(..., description="Prediction timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 0,
                "probability": 0.0234,
                "latency_ms": 12.45,
                "timestamp": "2024-01-01T12:00:00.000000",
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Status message")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    database_connected: bool = Field(..., description="Whether database is connected")

