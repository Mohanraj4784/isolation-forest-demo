"""
Configuration file for Log Anomaly Detection System
"""
import os

# Model Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "anomaly_model.pkl")
ENSEMBLE_MODEL_PATH = os.path.join(MODEL_DIR, "ensemble_model.pkl")

# Update Frequency Configuration
UPDATE_FREQUENCY = {
    "HIGH_ANOMALY": 10,      # Update every 10 logs when anomaly rate is high
    "NORMAL": 100,            # Update every 100 logs during normal operation
    "STABLE": 1000,           # Update every 1000 logs when stable
}

# Model Performance Thresholds
ANOMALY_THRESHOLD = {
    "DEFAULT": 0.7,
    "CRITICAL_SERVICES": 0.5,  # More sensitive for critical services
    "NON_CRITICAL": 0.85,      # Less sensitive for non-critical services
}

# Feature Configuration
SLOW_THRESHOLD = 3.0  # Response time threshold in seconds
ERROR_KEYWORDS = [
    "error", "exception", "failed", "timeout", "denied", 
    "unavailable", "refused", "crashed", "fatal", "panic"
]

# Storage Configuration (File-based - No Database Required!)
STORAGE_TYPE = "file"  # Changed from "mysql" to "file"
STORAGE_DIR = os.path.join(MODEL_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Legacy Database Configuration (Optional - not used by default)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "CARDHOST"),
    "password": os.getenv("DB_PASSWORD", "CARDHOST"),
    "database": os.getenv("DB_NAME", "AI_MODEL"),
    "enabled": False,  # Database disabled by default
}

# Logging Configuration
LOG_HISTORY_SIZE = 500
FEEDBACK_HISTORY_SIZE = 100

# Performance Configuration
BATCH_SIZE = 50  # Process features in batches
SAVE_INTERVAL = 100  # Save model every N logs processed
ASYNC_SAVE = True  # Save models asynchronously

# GPU Configuration
USE_GPU = True
GPU_MEMORY_FRACTION = 0.8  # Use 80% of available GPU memory

# Monitoring Configuration
ENABLE_METRICS = True
METRICS_WINDOW = 1000  # Calculate metrics over last N predictions

# Critical Services (higher sensitivity)
CRITICAL_SERVICES = [
    "payment-service",
    "auth-service",
    "user-service",
    "database-service"
]

# Model Versioning
KEEP_MODEL_VERSIONS = 5  # Keep last 5 model versions
MODEL_VERSION_PATH = os.path.join(MODEL_DIR, "versions")
os.makedirs(MODEL_VERSION_PATH, exist_ok=True)

