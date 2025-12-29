"""Model service for loading and making predictions."""
import json
import joblib
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
from threading import Lock

from src.config import get_settings
from src.core import get_logger, ModelLoadError, PredictionError

logger = get_logger(__name__)


class ModelService:
    """Service for model loading and prediction."""
    
    _instance: Optional['ModelService'] = None
    _lock = Lock()
    
    def __init__(self, model_path: Optional[Path] = None, features_path: Optional[Path] = None):
        """
        Initialize model service.
        
        Args:
            model_path: Path to model file (defaults to settings)
            features_path: Path to feature list file (defaults to settings)
        """
        settings = get_settings()
        self.model_path = model_path or settings.model_path
        self.features_path = features_path or settings.features_path
        self.model: Optional[Any] = None
        self.feature_list: Optional[List[str]] = None
        self._loaded = False
        logger.debug(f"ModelService initialized with model_path={self.model_path}")
    
    @classmethod
    def get_instance(cls) -> 'ModelService':
        """
        Get singleton instance of ModelService.
        
        Returns:
            ModelService: Singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def load_model(self) -> None:
        """
        Load model and feature list.
        
        Raises:
            ModelLoadError: If model loading fails
        """
        if self._loaded:
            logger.debug("Model already loaded")
            return
        
        try:
            # Validate paths
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model file not found at {self.model_path}")
            
            if not self.features_path.exists():
                raise FileNotFoundError(f"Feature list not found at {self.features_path}")
            
            # Load model
            logger.info(f"Loading model from {self.model_path}")
            self.model = joblib.load(self.model_path)
            
            # Load feature list
            logger.info(f"Loading feature list from {self.features_path}")
            with open(self.features_path, 'r') as f:
                self.feature_list = json.load(f)
            
            if not isinstance(self.feature_list, list):
                raise ValueError("Feature list must be a list")
            
            if len(self.feature_list) == 0:
                raise ValueError("Feature list cannot be empty")
            
            self._loaded = True
            logger.info(f"Model loaded successfully: {len(self.feature_list)} features")
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise ModelLoadError(f"Model file not found: {e}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise ModelLoadError(f"Model loading failed: {e}")
    
    def is_loaded(self) -> bool:
        """
        Check if model is loaded.
        
        Returns:
            bool: True if model is loaded
        """
        return self._loaded and self.model is not None and self.feature_list is not None
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction.
        
        Args:
            features: Feature dictionary
        
        Returns:
            Dictionary with prediction, probability, and metadata
        
        Raises:
            ModelLoadError: If model is not loaded
            PredictionError: If prediction fails
        """
        if not self.is_loaded():
            raise ModelLoadError("Model is not loaded. Call load_model() first.")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([features])
            
            # Reorder columns to match feature list
            missing_features = set(self.feature_list) - set(df.columns)
            if missing_features:
                raise PredictionError(
                    f"Missing features: {sorted(missing_features)}",
                    details={"missing_features": sorted(missing_features)}
                )
            
            extra_features = set(df.columns) - set(self.feature_list)
            if extra_features:
                logger.warning(f"Extra features provided (will be ignored): {sorted(extra_features)}")
            
            # Select only required features in correct order
            df = df[self.feature_list]
            
            # Make prediction
            prediction = int(self.model.predict(df)[0])
            probability = float(self.model.predict_proba(df)[0][1])
            
            logger.debug(f"Prediction made: {prediction}, probability: {probability:.4f}")
            
            return {
                "prediction": prediction,
                "probability": probability,
            }
            
        except PredictionError:
            raise
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise PredictionError(f"Prediction failed: {e}")
    
    def get_feature_list(self) -> List[str]:
        """
        Get the feature list.
        
        Returns:
            List of feature names
        
        Raises:
            ModelLoadError: If model is not loaded
        """
        if not self.is_loaded():
            raise ModelLoadError("Model is not loaded. Call load_model() first.")
        
        return self.feature_list.copy()
    
    def reload_model(self) -> None:
        """
        Reload the model (useful for model updates).
        
        Raises:
            ModelLoadError: If reloading fails
        """
        logger.info("Reloading model...")
        self._loaded = False
        self.model = None
        self.feature_list = None
        self.load_model()

