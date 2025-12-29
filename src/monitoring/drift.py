"""Drift detection script using MonitoringService."""
from src.services import MonitoringService
from src.core import get_logger, setup_logging

logger = get_logger(__name__)


class DriftDetector:
    """Drift detector wrapper for command-line usage."""
    
    def __init__(self, limit: int = None):
        """
        Initialize drift detector.
        
        Args:
            limit: Maximum number of live records to use
        """
        self.monitoring_service = MonitoringService()
        self.limit = limit
        logger.debug(f"DriftDetector initialized with limit={limit}")
    
    def detect(self) -> dict:
        """
        Detect data drift.
        
        Returns:
            Dictionary with drift detection results
        
        Raises:
            DriftDetectionError: If drift detection fails
        """
        try:
            logger.info("Starting drift detection...")
            result = self.monitoring_service.detect_drift(limit=self.limit)
            logger.info("Drift detection completed successfully")
            return result
        except Exception as e:
            logger.error(f"Drift detection failed: {e}")
            raise


def main():
    """Main entry point for drift detection script."""
    # Setup logging
    setup_logging()
    
    try:
        detector = DriftDetector()
        result = detector.detect()
        
        print("\n" + "=" * 60)
        print("Drift Detection Results")
        print("=" * 60)
        print(f"Status: {result['status']}")
        print(f"Records analyzed: {result['record_count']}")
        print(f"HTML report: {result['html_path']}")
        print(f"JSON summary: {result['json_path']}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Drift detection script failed: {e}")
        print(f"\nError: {e}")
        exit(1)


if __name__ == "__main__":
    main()
