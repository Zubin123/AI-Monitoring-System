"""Repository for prediction data operations."""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd

from src.storage import DatabaseManager, get_database_manager
from src.core import get_logger, DatabaseError

logger = get_logger(__name__)


class PredictionRepository:
    """Repository for managing prediction data."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize prediction repository.
        
        Args:
            db_manager: Database manager instance (defaults to global instance)
        """
        self.db_manager = db_manager or get_database_manager()
        logger.debug("PredictionRepository initialized")
    
    def save_prediction(
        self,
        features: Dict[str, Any],
        prediction: int,
        probability: float,
        latency_ms: float,
        timestamp: Optional[str] = None,
    ) -> int:
        """
        Save a prediction to the database.
        
        Args:
            features: Feature dictionary
            prediction: Prediction value (0 or 1)
            probability: Prediction probability
            latency_ms: Prediction latency in milliseconds
            timestamp: Timestamp (defaults to current UTC time)
        
        Returns:
            int: Inserted row ID
        
        Raises:
            DatabaseError: If save operation fails
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO live_predictions 
                    (timestamp, features, prediction, probability, latency_ms)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        json.dumps(features),
                        prediction,
                        probability,
                        latency_ms,
                    ),
                )
                conn.commit()
                row_id = cursor.lastrowid
                logger.debug(f"Prediction saved with ID: {row_id}")
                return row_id
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
            raise DatabaseError(f"Failed to save prediction: {e}")
    
    def get_predictions(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        start_timestamp: Optional[str] = None,
        end_timestamp: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get predictions from the database.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_timestamp: Start timestamp filter (ISO format)
            end_timestamp: End timestamp filter (ISO format)
        
        Returns:
            List of prediction dictionaries
        
        Raises:
            DatabaseError: If query fails
        """
        try:
            query = "SELECT * FROM live_predictions WHERE 1=1"
            params = []
            
            if start_timestamp:
                query += " AND timestamp >= ?"
                params.append(start_timestamp)
            
            if end_timestamp:
                query += " AND timestamp <= ?"
                params.append(end_timestamp)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, tuple(params))
                rows = cursor.fetchall()
                
                # Get column names from cursor description
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                else:
                    columns = ["id", "timestamp", "features", "prediction", "probability", "latency_ms"]
                
                predictions = []
                for row in rows:
                    # Convert row to tuple first (works for both Row objects and tuples)
                    row_tuple = tuple(row) if not isinstance(row, tuple) else row
                    # Create dict from tuple using column names
                    row_dict = dict(zip(columns, row_tuple))
                    
                    predictions.append({
                        "id": row_dict.get("id"),
                        "timestamp": row_dict.get("timestamp"),
                        "features": json.loads(row_dict.get("features", "{}")),
                        "prediction": row_dict.get("prediction"),
                        "probability": row_dict.get("probability"),
                        "latency_ms": row_dict.get("latency_ms"),
                    })
                
                logger.debug(f"Retrieved {len(predictions)} predictions")
                return predictions
        except Exception as e:
            logger.error(f"Failed to get predictions: {e}")
            raise DatabaseError(f"Failed to get predictions: {e}")
    
    def get_feature_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get feature data as DataFrame for drift detection.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            DataFrame with feature columns
        
        Raises:
            DatabaseError: If query fails
        """
        try:
            query = "SELECT features FROM live_predictions ORDER BY timestamp DESC"
            params = []
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            with self.db_manager.get_connection() as conn:
                df = pd.read_sql(query, conn, params=tuple(params) if params else None)
                
                if df.empty:
                    logger.warning("No feature data found in database")
                    return pd.DataFrame()
                
                # Parse JSON features
                live_features = df["features"].apply(json.loads)
                live_features_df = pd.DataFrame(live_features.tolist())
                
                logger.debug(f"Retrieved {len(live_features_df)} feature records")
                return live_features_df
        except Exception as e:
            logger.error(f"Failed to get feature data: {e}")
            raise DatabaseError(f"Failed to get feature data: {e}")
    
    def get_prediction_count(self) -> int:
        """
        Get total number of predictions in database.
        
        Returns:
            int: Total prediction count
        
        Raises:
            DatabaseError: If query fails
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) as count FROM live_predictions")
                row = cursor.fetchone()
                if row:
                    # Convert to tuple and get first element
                    row_tuple = tuple(row) if not isinstance(row, tuple) else row
                    count = row_tuple[0]
                else:
                    count = 0
                logger.debug(f"Total predictions: {count}")
                return count
        except Exception as e:
            logger.error(f"Failed to get prediction count: {e}")
            raise DatabaseError(f"Failed to get prediction count: {e}")
    
    def delete_old_predictions(self, days: int = 30) -> int:
        """
        Delete predictions older than specified days.
        
        Args:
            days: Number of days to keep
        
        Returns:
            int: Number of deleted records
        
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            cutoff_date = datetime.utcnow().isoformat()
            # Simple date comparison (for production, use proper date arithmetic)
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM live_predictions 
                    WHERE timestamp < datetime('now', '-' || ? || ' days')
                    """,
                    (days,),
                )
                conn.commit()
                deleted_count = cursor.rowcount
                logger.info(f"Deleted {deleted_count} old predictions (older than {days} days)")
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old predictions: {e}")
            raise DatabaseError(f"Failed to delete old predictions: {e}")

