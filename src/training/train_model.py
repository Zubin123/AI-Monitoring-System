"""Training pipeline for fraud detection model."""
import json
import joblib
import pandas as pd
from pathlib import Path
from typing import Optional
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

from src.config import get_settings
from src.core import get_logger, ConfigurationError, ModelLoadError

logger = get_logger(__name__)


class TrainingPipeline:
    """Training pipeline for fraud detection model."""
    
    def __init__(
        self,
        data_path: Optional[Path] = None,
        reference_data_path: Optional[Path] = None,
        artifacts_dir: Optional[Path] = None,
        test_size: Optional[float] = None,
        random_state: Optional[int] = None,
    ):
        """
        Initialize training pipeline.
        
        Args:
            data_path: Path to training data CSV
            reference_data_path: Path to save reference data
            artifacts_dir: Directory to save artifacts
            test_size: Test split size (defaults to settings)
            random_state: Random state for reproducibility (defaults to settings)
        """
        settings = get_settings()
        
        self.data_path = data_path or (settings.data_dir / "creditdata.csv")
        self.reference_data_path = reference_data_path or settings.reference_data_path
        self.artifacts_dir = artifacts_dir or settings.artifacts_dir
        self.test_size = test_size or settings.train_test_split
        self.random_state = random_state or settings.random_state
        
        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.reference_data_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(
            f"TrainingPipeline initialized: "
            f"data_path={self.data_path}, "
            f"test_size={self.test_size}, "
            f"random_state={self.random_state}"
        )
    
    def load_data(self) -> pd.DataFrame:
        """
        Load training data.
        
        Returns:
            DataFrame with training data
        
        Raises:
            ConfigurationError: If data file not found or invalid
        """
        try:
            if not self.data_path.exists():
                raise FileNotFoundError(f"Data file not found at {self.data_path}")
            
            logger.info(f"Loading training data from {self.data_path}")
            df = pd.read_csv(self.data_path)
            
            # Validate required columns
            required_columns = {"Class", "Amount", "Time"}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                raise ValueError(f"Required columns missing: {sorted(missing)}")
            
            logger.info(f"Data loaded: {len(df)} records, {len(df.columns)} columns")
            return df
            
        except FileNotFoundError as e:
            logger.error(f"Data file not found: {e}")
            raise ConfigurationError(f"Data file not found: {e}")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise ConfigurationError(f"Failed to load data: {e}")
    
    def prepare_data(self, df: pd.DataFrame) -> tuple:
        """
        Prepare features and target.
        
        Args:
            df: DataFrame with training data
        
        Returns:
            Tuple of (X_train, X_ref, y_train, y_ref, feature_list)
        """
        logger.info("Preparing features and target...")
        
        X = df.drop(columns=["Class"])
        y = df["Class"]
        
        feature_list = X.columns.tolist()
        logger.info(f"Features extracted: {len(feature_list)} features")
        
        # Train / Reference split
        X_train, X_ref, y_train, y_ref = train_test_split(
            X,
            y,
            test_size=self.test_size,
            stratify=y,
            random_state=self.random_state,
        )
        
        logger.info(
            f"Data split: train={len(X_train)}, reference={len(X_ref)}, "
            f"test_size={self.test_size}"
        )
        
        return X_train, X_ref, y_train, y_ref, feature_list
    
    def save_reference_data(
        self,
        X_ref: pd.DataFrame,
        y_ref: pd.Series,
    ) -> None:
        """
        Save reference data for drift detection.
        
        Args:
            X_ref: Reference features
            y_ref: Reference target
        """
        try:
            logger.info(f"Saving reference data to {self.reference_data_path}")
            reference_df = X_ref.copy()
            reference_df["Class"] = y_ref
            reference_df.to_csv(self.reference_data_path, index=False)
            logger.info(f"Reference data saved: {len(reference_df)} records")
        except Exception as e:
            logger.error(f"Failed to save reference data: {e}")
            raise ConfigurationError(f"Failed to save reference data: {e}")
    
    def create_pipeline(self) -> Pipeline:
        """
        Create model pipeline.
        
        Returns:
            sklearn Pipeline
        """
        logger.info("Creating model pipeline...")
        pipeline = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        n_jobs=1,
                    ),
                ),
            ]
        )
        logger.info("Pipeline created: StandardScaler -> LogisticRegression")
        return pipeline
    
    def train(self, pipeline: Pipeline, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """
        Train the model.
        
        Args:
            pipeline: Model pipeline
            X_train: Training features
            y_train: Training target
        """
        logger.info(f"Training model on {len(X_train)} samples...")
        pipeline.fit(X_train, y_train)
        logger.info("Model training completed")
    
    def evaluate(
        self,
        pipeline: Pipeline,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> dict:
        """
        Evaluate model performance.
        
        Args:
            pipeline: Trained pipeline
            X_train: Training features
            y_train: Training target
        
        Returns:
            Dictionary with metrics
        """
        logger.info("Evaluating model...")
        
        y_pred = pipeline.predict(X_train)
        y_proba = pipeline.predict_proba(X_train)[:, 1]
        
        metrics = {
            "accuracy": accuracy_score(y_train, y_pred),
            "precision": precision_score(y_train, y_pred),
            "recall": recall_score(y_train, y_pred),
            "roc_auc": roc_auc_score(y_train, y_proba),
        }
        
        logger.info(
            f"Model metrics: accuracy={metrics['accuracy']:.4f}, "
            f"precision={metrics['precision']:.4f}, "
            f"recall={metrics['recall']:.4f}, "
            f"roc_auc={metrics['roc_auc']:.4f}"
        )
        
        return metrics
    
    def save_artifacts(
        self,
        pipeline: Pipeline,
        feature_list: list,
        metrics: dict,
    ) -> None:
        """
        Save model artifacts.
        
        Args:
            pipeline: Trained pipeline
            feature_list: List of feature names
            metrics: Model metrics
        """
        try:
            logger.info("Saving model artifacts...")
            
            # Save model
            model_path = self.artifacts_dir / "model.pkl"
            joblib.dump(pipeline, model_path)
            logger.info(f"Model saved to {model_path}")
            
            # Save metrics
            metrics_path = self.artifacts_dir / "metrics.json"
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=4)
            logger.info(f"Metrics saved to {metrics_path}")
            
            # Save feature list
            features_path = self.artifacts_dir / "feature_list.json"
            with open(features_path, "w") as f:
                json.dump(feature_list, f, indent=4)
            logger.info(f"Feature list saved to {features_path}")
            
        except Exception as e:
            logger.error(f"Failed to save artifacts: {e}")
            raise ModelLoadError(f"Failed to save artifacts: {e}")
    
    def run(self) -> dict:
        """
        Run the complete training pipeline.
        
        Returns:
            Dictionary with training results and metrics
        """
        logger.info("=" * 60)
        logger.info("Starting training pipeline")
        logger.info("=" * 60)
        
        try:
            # Load data
            df = self.load_data()
            
            # Prepare data
            X_train, X_ref, y_train, y_ref, feature_list = self.prepare_data(df)
            
            # Save reference data
            self.save_reference_data(X_ref, y_ref)
            
            # Create and train pipeline
            pipeline = self.create_pipeline()
            self.train(pipeline, X_train, y_train)
            
            # Evaluate
            metrics = self.evaluate(pipeline, X_train, y_train)
            
            # Save artifacts
            self.save_artifacts(pipeline, feature_list, metrics)
            
            logger.info("=" * 60)
            logger.info("Training pipeline completed successfully")
            logger.info("=" * 60)
            
            return {
                "status": "success",
                "metrics": metrics,
                "feature_count": len(feature_list),
                "train_samples": len(X_train),
                "reference_samples": len(X_ref),
            }
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            raise


def main():
    """Main entry point for training script."""
    pipeline = TrainingPipeline()
    results = pipeline.run()
    print(f"\nTraining Results:")
    print(f"  Status: {results['status']}")
    print(f"  Metrics: {results['metrics']}")
    print(f"  Features: {results['feature_count']}")
    print(f"  Train samples: {results['train_samples']}")
    print(f"  Reference samples: {results['reference_samples']}")


if __name__ == "__main__":
    main()
