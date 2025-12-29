"""Application configuration using Pydantic Settings."""
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.paths import (
    get_base_dir,
    get_artifacts_dir,
    get_data_dir,
    get_reference_data_dir,
    get_logs_dir,
)


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Paths (computed from base_dir)
    base_dir: Path = Field(default_factory=get_base_dir)
    artifacts_dir: Path = Field(default_factory=get_artifacts_dir)
    data_dir: Path = Field(default_factory=get_data_dir)
    reference_data_dir: Path = Field(default_factory=get_reference_data_dir)
    logs_dir: Path = Field(default_factory=get_logs_dir)
    
    # Model paths
    model_path: Optional[Path] = None
    features_path: Optional[Path] = None
    reference_data_path: Optional[Path] = None
    db_path: Optional[Path] = None
    
    # Model settings
    model_type: str = Field(default="logistic_regression")
    
    # Monitoring settings
    min_records_for_drift: int = Field(default=500, ge=1)
    drift_detection_interval: int = Field(default=3600, ge=1)
    
    # Database settings
    db_pool_size: int = Field(default=5, ge=1, le=20)
    
    # Logging settings
    log_level: str = Field(default="INFO")
    log_file: Optional[Path] = None
    log_rotation: str = Field(default="10 MB")
    log_retention: str = Field(default="30 days")
    log_format: str = Field(default="json")  # "json" or "text"
    
    # API settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_title: str = Field(default="AI Model Monitoring API")
    api_version: str = Field(default="1.0.0")
    
    # Training settings
    train_test_split: float = Field(default=0.2, gt=0.0, lt=1.0)
    random_state: int = Field(default=42)
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}")
        return v.lower()
    
    def __init__(self, **kwargs):
        """Initialize settings with computed paths."""
        super().__init__(**kwargs)
        
        # Set default paths if not provided
        if self.model_path is None:
            self.model_path = self.artifacts_dir / "model.pkl"
        
        if self.features_path is None:
            self.features_path = self.artifacts_dir / "feature_list.json"
        
        if self.reference_data_path is None:
            self.reference_data_path = self.reference_data_dir / "reference_data.csv"
        
        if self.db_path is None:
            self.db_path = self.artifacts_dir / "live_data.db"
        
        if self.log_file is None:
            self.log_file = self.logs_dir / "app.log"
        
        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.reference_data_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

