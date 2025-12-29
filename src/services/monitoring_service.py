"""Monitoring service for drift detection."""
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

from src.config import get_settings
from src.repositories import PredictionRepository
from src.core import get_logger, DriftDetectionError

logger = get_logger(__name__)


class MonitoringService:
    """Service for data drift detection and monitoring."""
    
    def __init__(
        self,
        prediction_repository: Optional[PredictionRepository] = None,
        reference_data_path: Optional[Path] = None,
        min_records: Optional[int] = None,
    ):
        """
        Initialize monitoring service.
        
        Args:
            prediction_repository: Prediction repository instance
            reference_data_path: Path to reference data CSV
            min_records: Minimum records required for drift detection
        """
        settings = get_settings()
        self.prediction_repository = prediction_repository or PredictionRepository()
        self.reference_data_path = reference_data_path or settings.reference_data_path
        self.min_records = min_records or settings.min_records_for_drift
        logger.debug(f"MonitoringService initialized with min_records={self.min_records}")
    
    def load_reference_data(self) -> pd.DataFrame:
        """
        Load reference data.
        
        Returns:
            DataFrame with reference data
        
        Raises:
            DriftDetectionError: If loading fails
        """
        try:
            if not self.reference_data_path.exists():
                raise FileNotFoundError(f"Reference data not found at {self.reference_data_path}")
            
            logger.info(f"Loading reference data from {self.reference_data_path}")
            reference_df = pd.read_csv(self.reference_data_path)
            
            # Remove Class column if present (for drift detection, we only need features)
            if "Class" in reference_df.columns:
                reference_df = reference_df.drop(columns=["Class"])
            
            logger.info(f"Reference data loaded: {len(reference_df)} records, {len(reference_df.columns)} features")
            return reference_df
            
        except FileNotFoundError as e:
            logger.error(f"Reference data file not found: {e}")
            raise DriftDetectionError(f"Reference data not found: {e}")
        except Exception as e:
            logger.error(f"Failed to load reference data: {e}")
            raise DriftDetectionError(f"Failed to load reference data: {e}")
    
    def detect_drift(
        self,
        limit: Optional[int] = None,
        report_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Detect data drift between reference and live data.
        
        Args:
            limit: Maximum number of live records to use
            report_dir: Directory to save reports (defaults to artifacts)
        
        Returns:
            Dictionary with drift detection results
        
        Raises:
            DriftDetectionError: If drift detection fails
        """
        try:
            # Load reference data
            reference_df = self.load_reference_data()
            
            # Get live data
            logger.info("Retrieving live prediction data...")
            live_df = self.prediction_repository.get_feature_data(limit=limit)
            
            # Validate data availability
            if live_df.empty:
                raise DriftDetectionError(
                    "No live data found in database. Please make some predictions via the API first."
                )
            
            record_count = len(live_df)
            if record_count < self.min_records:
                logger.warning(
                    f"Only {record_count} records available. "
                    f"For reliable drift detection, recommend at least {self.min_records}+ records."
                )
                raise DriftDetectionError(
                    f"Not enough live data for drift detection. "
                    f"Found {record_count} records, but need at least {self.min_records} records. "
                    f"Please make more predictions via the API."
                )
            
            logger.info(f"Found {record_count} live prediction records")
            
            # Ensure feature columns match
            reference_features = set(reference_df.columns)
            live_features = set(live_df.columns)
            
            if reference_features != live_features:
                missing_in_live = reference_features - live_features
                extra_in_live = live_features - reference_features
                error_msg = "Feature mismatch between reference and live data."
                if missing_in_live:
                    error_msg += f" Missing in live: {sorted(missing_in_live)}"
                if extra_in_live:
                    error_msg += f" Extra in live: {sorted(extra_in_live)}"
                raise DriftDetectionError(error_msg)
            
            # Reorder live data columns to match reference
            live_df = live_df[reference_df.columns]
            
            # Generate drift report
            logger.info("Generating drift detection report...")
            report = Report(metrics=[DataDriftPreset()])
            report.run(
                reference_data=reference_df,
                current_data=live_df,
            )
            
            # Save reports
            if report_dir is None:
                settings = get_settings()
                report_dir = settings.artifacts_dir
            
            report_dir.mkdir(parents=True, exist_ok=True)
            html_path = report_dir / "monitoring_report.html"
            json_path = report_dir / "monitoring_summary.json"
            
            report.save_html(str(html_path))
            report.save_json(str(json_path))
            
            logger.info(f"Drift report generated: HTML={html_path}, JSON={json_path}")
            
            return {
                "status": "success",
                "record_count": record_count,
                "html_path": str(html_path),
                "json_path": str(json_path),
            }
            
        except DriftDetectionError:
            raise
        except Exception as e:
            logger.error(f"Drift detection failed: {e}")
            raise DriftDetectionError(f"Drift detection failed: {e}")
    
    def get_live_data_stats(self) -> Dict[str, Any]:
        """
        Get statistics about live data.
        
        Returns:
            Dictionary with statistics
        """
        try:
            count = self.prediction_repository.get_prediction_count()
            return {
                "total_predictions": count,
                "min_records_required": self.min_records,
                "sufficient_for_drift": count >= self.min_records,
            }
        except Exception as e:
            logger.error(f"Failed to get live data stats: {e}")
            return {
                "total_predictions": 0,
                "min_records_required": self.min_records,
                "sufficient_for_drift": False,
                "error": str(e),
            }

