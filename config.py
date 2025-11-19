"""
Configuration file for Log Anomaly Detection System
"""
import os

# ============================================================================
# Storage Configuration
# ============================================================================

# Model Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "anomaly_model.pkl")
ENSEMBLE_MODEL_PATH = os.path.join(MODEL_DIR, "ensemble_model.pkl")

# Storage directory for River model files
STORAGE_DIR = os.path.join(BASE_DIR, "models", "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Storage Configuration (File-based - No Database Required!)
STORAGE_TYPE = "file"  # Changed from "mysql" to "file"

# Legacy Database Configuration (Optional - not used by default)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "CARDHOST"),
    "password": os.getenv("DB_PASSWORD", "CARDHOST"),
    "database": os.getenv("DB_NAME", "AI_MODEL"),
    "enabled": False,  # Database disabled by default
}

# Model Versioning
KEEP_MODEL_VERSIONS = 5  # Keep last 5 model versions
MODEL_VERSION_PATH = os.path.join(MODEL_DIR, "versions")
os.makedirs(MODEL_VERSION_PATH, exist_ok=True)

# ============================================================================
# Thresholds Configuration
# ============================================================================

# Base thresholds for anomaly detection
ANOMALY_THRESHOLD = {
    "DEFAULT": 0.7,                 # Baseline threshold
    "CRITICAL_SERVICES": 0.6,       # More sensitive for critical paths
    "NON_CRITICAL": 0.85,           # Less sensitive for non-critical services
}

# Response-time related thresholds
SLOW_THRESHOLD = 1.0  # seconds

# ============================================================================
# History Configuration
# ============================================================================

# History sizes
FEEDBACK_HISTORY_SIZE = 1000
LOG_HISTORY_SIZE = 1000

# ============================================================================
# Critical Services Configuration
# ============================================================================

# List of services where anomalies must be caught aggressively
CRITICAL_SERVICES = [
    "auth-service",
    "payments-service",
    "database-service",
]

# ============================================================================
# Feature Extraction Configuration
# ============================================================================

# Error keywords used in text-based feature extraction
ERROR_KEYWORDS = [
    "error", "exception", "timeout", "failed", "failure",
    "critical", "panic", "stack trace", "connection reset"
]

# ============================================================================
# Model Update Configuration
# ============================================================================

# Frequency at which model will be saved depending on anomaly trend
UPDATE_FREQUENCY = {
    "NORMAL": 200,
    "HIGH_ANOMALY": 50,
    "STABLE": 500,
}

# Minimum number of NORMAL logs required to warm up model
MIN_TRAINING_SAMPLES = 200

# ============================================================================
# Monitoring & Metrics Configuration
# ============================================================================

# Toggle metrics/logging of anomaly detection
ENABLE_METRICS = True

METRICS_WINDOW = 1000  # Calculate metrics over last N predictions

# ============================================================================
# Performance Configuration
# ============================================================================

BATCH_SIZE = 50  # Process features in batches
SAVE_INTERVAL = 100  # Save model every N logs processed
ASYNC_SAVE = True  # Save models asynchronously

# ============================================================================
# GPU Configuration
# ============================================================================

USE_GPU = True
GPU_MEMORY_FRACTION = 0.8  # Use 80% of available GPU memory
