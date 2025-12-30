# AI Model Monitoring System

A comprehensive system for training, deploying, and monitoring an AI model for credit card fraud detection. The system includes model training, a REST API for predictions, a monitoring dashboard, and drift detection capabilities.

## Features

- **Model Training**: Automated pipeline for training a fraud detection model using logistic regression
- **REST API**: FastAPI-based service for real-time fraud predictions
- **Monitoring Dashboard**: Streamlit web app for visualizing model performance and metrics
- **Drift Detection**: Automated monitoring for data drift using Evidently
- **Logging**: Structured logging with JSON format and file rotation
- **Database**: SQLite-based storage for prediction history
- **Configuration**: Environment-based settings with Pydantic

## Project Structure

```
AI_model_monitoring/
├── requirements.txt              # Python dependencies
├── test_logging.py              # Logging test script
├── test_predictions.json        # Test prediction data
├── artifacts/                   # Model artifacts and metrics
│   ├── feature_list.json        # List of model features
│   ├── metrics.json            # Model performance metrics
│   ├── model.pkl               # Trained model pipeline
│   └── live_data.db            # SQLite database for predictions
├── dashboard/                   # Streamlit monitoring dashboard
│   └── app.py                   # Dashboard application
├── data/                        # Data files
│   ├── creditdata.csv          # Training data (credit card transactions)
│   └── reference/               # Reference data for drift detection
├── logs/                        # Application logs
├── src/                         # Source code
│   ├── api/                     # FastAPI application
│   │   ├── main.py             # Main API application
│   │   ├── dependencies.py     # API dependencies
│   │   └── routes/             # API route handlers
│   │       ├── health.py       # Health check endpoint
│   │       └── predict.py      # Prediction endpoint
│   ├── config/                  # Configuration management
│   │   ├── paths.py            # Path utilities
│   │   └── settings.py         # Application settings
│   ├── core/                    # Core utilities
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logger.py           # Logging configuration
│   ├── models/                  # Data models
│   │   ├── prediction.py       # Prediction data model
│   │   └── transaction.py      # Transaction data model
│   ├── monitoring/              # Monitoring and drift detection
│   │   └── drift.py            # Drift detection logic
│   ├── repositories/            # Data access layer
│   │   └── prediction_repository.py  # Prediction data repository
│   ├── services/                # Business logic services
│   │   ├── model_service.py    # Model loading and prediction
│   │   └── monitoring_service.py  # Monitoring services
│   ├── storage/                 # Storage utilities
│   │   └── database.py         # Database connection
│   └── training/                # Model training
│       └── train_model.py      # Training pipeline
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Zubin123/AI-Monitoring-System.git
   cd AI-Monitoring-System
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional):**
   Create a `.env` file in the root directory to override default settings:
   ```env
   API_HOST=0.0.0.0
   API_PORT=8000
   LOG_LEVEL=INFO
   ```

## Usage

### Training the Model

Train the fraud detection model using the provided training pipeline:

```bash
python -m src.training.train_model
```

This will:
- Load the credit card transaction data
- Train a logistic regression model with standard scaling
- Save the model, metrics, and feature list to the `artifacts/` directory
- Create reference data for drift detection

### Running the API

Start the FastAPI server for predictions:

```bash
python -m src.api.main
```

The API will be available at `http://localhost:8000`

**Endpoints:**
- `GET /` - API information
- `GET /health` - Health check
- `POST /predict` - Make fraud predictions
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

**Example prediction request:**
```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d @test_predictions.json
```

### Running the Dashboard

Launch the monitoring dashboard:

```bash
streamlit run dashboard/app.py
```

The dashboard will be available at `http://localhost:8501`

**Dashboard features:**
- Real-time metrics (total predictions, fraud rate, average latency)
- Charts for probability over time and latency distribution
- Recent predictions table
- Drift detection reports (when available)

### Testing Logging

Verify that logging is working correctly:

```bash
python test_logging.py
```

## Configuration

The application uses Pydantic settings for configuration. Default values are defined in `src/config/settings.py`. You can override settings using environment variables or a `.env` file.

**Key settings:**
- `API_HOST` / `API_PORT`: API server configuration
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT`: Log format (json or text)
- `MIN_RECORDS_FOR_DRIFT`: Minimum records required for drift detection
- `DRIFT_DETECTION_INTERVAL`: Interval for drift checks in seconds

## Data

The system uses the [Credit Card Fraud Detection dataset](https://www.kaggle.com/mlg-ulb/creditcardfraud) from Kaggle. The dataset contains transactions made by credit cards in September 2013 by European cardholders.

**Features:**
- `Time`: Number of seconds elapsed between this transaction and the first transaction
- `Amount`: Transaction amount
- `V1-V28`: Principal components obtained with PCA
- `Class`: Target variable (1 for fraud, 0 otherwise)

## Monitoring and Drift Detection

The system includes automated monitoring for:
- **Data Drift**: Uses Evidently to detect changes in data distribution
- **Model Performance**: Tracks prediction latency and success rates
- **Prediction History**: Stores all predictions in SQLite database

Drift reports are generated periodically and can be viewed in the dashboard.

## Development

### Running Tests

```bash
python -m pytest
```

### Code Quality

The project uses:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

### Adding New Features

1. Follow the modular structure in `src/`
2. Add appropriate logging
3. Update configuration if needed
4. Add tests for new functionality
5. Update this README

## Dependencies

**Core:**
- `fastapi`: Web framework for the API
- `uvicorn`: ASGI server
- `streamlit`: Dashboard framework
- `scikit-learn`: Machine learning library
- `pandas`: Data manipulation
- `numpy`: Numerical computing

**Monitoring:**
- `evidently`: ML model monitoring and drift detection

**Utilities:**
- `pydantic`: Data validation
- `loguru`: Logging library
- `python-dotenv`: Environment variable management
- `sqlite-utils`: SQLite database utilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Credit card fraud dataset from Kaggle
- Evidently for drift detection capabilities
- FastAPI and Streamlit communities</content>
<parameter name="filePath">c:\Users\LENOVO\AI_model_monitoring\README.md