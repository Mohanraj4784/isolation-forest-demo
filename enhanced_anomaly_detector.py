"""
Enhanced Log Anomaly Detector with improved frequency control and features
"""
import re
import hashlib
import numpy as np
import logging
import pickle
import os
import time
from collections import deque, defaultdict
from datetime import datetime, timedelta
from river import anomaly, ensemble
from typing import Dict, Tuple, List, Any
import config
from FilePersistence import FileModelPersistence

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedLogAnomalyDetector:
    def __init__(self):
        # Initialize file-based persistence (No database required!)
        self.persistence = FileModelPersistence(
            storage_dir=config.STORAGE_DIR
        )
        
        # Initialize ensemble model
        self.classifier = self.load_model()
        
        # Adaptive thresholds per service
        self.service_thresholds = defaultdict(lambda: config.ANOMALY_THRESHOLD["DEFAULT"])
        
        # History tracking
        self.feedback_history = deque(maxlen=config.FEEDBACK_HISTORY_SIZE)
        self.log_history = deque(maxlen=config.LOG_HISTORY_SIZE)
        self.anomaly_history = deque(maxlen=100)
        
        # Performance tracking
        self.processed_count = 0
        self.last_save_count = 0
        self.anomaly_count = 0
        
        # Service-specific metrics
        self.service_metrics = defaultdict(lambda: {
            'response_times': deque(maxlen=100),
            'error_count': 0,
            'total_count': 0,
            'last_anomaly_time': None
        })
        
        # Feature cache for expensive computations
        self.feature_cache = {}
        
        # --- Warm-up training state ---
        self.training_only = True            # Until the model sees enough normal logs
        self.training_samples = 0            # Count of warm-up samples
        
        logger.info("✅ Enhanced Log Anomaly Detector initialized!")
    
    def _get_ensemble_model(self):
        """Create an ensemble of multiple anomaly detection models"""
        return [
            ('half_space_trees', anomaly.HalfSpaceTrees(n_trees=10, height=8, window_size=250)),
            ('half_space_trees_alt', anomaly.HalfSpaceTrees(n_trees=15, height=10, window_size=300)),
        ]
    
    def scale(self, value, min_value, max_value):
        """Scale value to [0, 1] range"""
        if max_value > min_value:
            return (value - min_value) / (max_value - min_value)
        return 0.0
    
    def extract_temporal_features(self, timestamp=None):
        """Extract time-based features"""
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        return [
            self.scale(hour, 0, 23),  # Hour of day
            1 if day_of_week >= 5 else 0,  # Weekend flag
            1 if 9 <= hour <= 17 else 0,  # Business hours flag
            np.sin(2 * np.pi * hour / 24),  # Cyclical hour encoding
            np.cos(2 * np.pi * hour / 24),
            np.sin(2 * np.pi * day_of_week / 7),  # Cyclical day encoding
            np.cos(2 * np.pi * day_of_week / 7),
        ]
    
    def extract_sequential_features(self, log_request):
        """Extract features based on recent history"""
        service = log_request.get("service", "unknown")
        metrics = self.service_metrics[service]
        
        # Update metrics
        response_time = float(log_request.get("response_time", 0))
        metrics['response_times'].append(response_time)
        metrics['total_count'] += 1
        
        # Calculate rolling statistics
        if len(metrics['response_times']) > 0:
            avg_response = np.mean(metrics['response_times'])
            std_response = np.std(metrics['response_times']) if len(metrics['response_times']) > 1 else 0
            max_response = np.max(metrics['response_times'])
            response_trend = (response_time - avg_response) / (std_response + 0.001)
        else:
            avg_response = response_time
            std_response = 0
            max_response = response_time
            response_trend = 0
        
        # Error rate calculation
        error_rate = metrics['error_count'] / max(metrics['total_count'], 1)
        
        # Request frequency: logs per minute over the last N minutes
        now = datetime.utcnow()
        window_minutes = 5  # can be made configurable if needed

        recent_logs = []
        for log in self.log_history:
            if log.get("service") != service:
                continue

            ts = log.get("timestamp")
            if isinstance(ts, str):
                # Convert ISO string to datetime; handle trailing 'Z'
                try:
                    ts_parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    # Convert timezone-aware to naive UTC for comparison
                    if ts_parsed.tzinfo is not None:
                        ts = ts_parsed.replace(tzinfo=None)
                    else:
                        ts = ts_parsed
                except Exception:
                    continue

            if isinstance(ts, datetime):
                if (now - ts).total_seconds() <= window_minutes * 60:
                    recent_logs.append(log)

        # Requests per minute in the last 'window_minutes'
        request_frequency = len(recent_logs) / max(window_minutes, 1)
        
        return [
            self.scale(avg_response, 0, 10),
            self.scale(std_response, 0, 5),
            self.scale(max_response, 0, 10),
            self.scale(response_trend, -3, 3),
            error_rate,
            self.scale(request_frequency, 0, 100),
            self.scale(metrics['total_count'], 0, 10000),
        ]
    
    def extract_text_features(self, message: str):
        """Extract advanced text features from log message"""
        if not message:
            return [0] * 8
        
        # Check cache
        msg_hash = hashlib.md5(message.encode()).hexdigest()
        if msg_hash in self.feature_cache:
            return self.feature_cache[msg_hash]
        
        message_lower = message.lower()
        
        # Error keyword analysis
        error_words = [kw for kw in config.ERROR_KEYWORDS if kw in message_lower]
        error_keyword_count = len(error_words)
        error_keyword_density = error_keyword_count / max(len(message.split()), 1)
        
        # Pattern detection
        has_stack_trace = 1 if any(x in message for x in ["Exception", "Traceback", "Stack trace"]) else 0
        has_ip_address = 1 if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', message) else 0
        has_url = 1 if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message) else 0
        has_sql_keywords = 1 if any(x in message_lower for x in ['select', 'insert', 'update', 'delete', 'drop']) else 0
        
        # Message structure
        uppercase_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
        line_count = message.count('\n') + 1
        
        features = [
            error_keyword_count,
            error_keyword_density,
            has_stack_trace,
            has_ip_address,
            has_url,
            has_sql_keywords,
            self.scale(uppercase_ratio, 0, 1),
            self.scale(line_count, 1, 20),
        ]
        
        # Cache the result
        self.feature_cache[msg_hash] = features
        
        # Limit cache size
        if len(self.feature_cache) > 1000:
            # Remove oldest entries
            keys_to_remove = list(self.feature_cache.keys())[:100]
            for key in keys_to_remove:
                del self.feature_cache[key]
        
        return features
    
    def extract_features(self, log_request):
        """Extract comprehensive features from log"""
        message = log_request.get("message", "")
        service_name = log_request.get("service", "unknown")
        method_name = log_request.get("method", "unknown")
        api_endpoint = log_request.get("endpoint", "unknown")
        response_time = float(log_request.get("response_time", 0))
        status_code = int(log_request.get("status_code", 200))
        log_level = log_request.get("level", "INFO").upper()
        
        # Basic message features
        message_length = len(message)
        word_count = len(message.split()) if message else 0
        digit_count = sum(c.isdigit() for c in message)
        special_char_count = sum(not c.isalnum() and not c.isspace() for c in message)
        digit_ratio = digit_count / message_length if message_length > 0 else 0.0
        special_char_ratio = special_char_count / message_length if message_length > 0 else 0.0
        
        # Log Level Encoding (one-hot)
        log_levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL", "CRITICAL"]
        log_level_encoding = [1 if log_level == level else 0 for level in log_levels]
        
        # Status Code Features
        status_code_error = 1 if status_code >= 500 else 0
        status_code_warning = 1 if 400 <= status_code < 500 else 0
        status_code_success = 1 if 200 <= status_code < 300 else 0
        
        # Response time features
        slow_response = 1 if response_time > config.SLOW_THRESHOLD else 0
        very_slow_response = 1 if response_time > (config.SLOW_THRESHOLD * 2) else 0
        
        # Service/Method hashing
        service_hash = int(hashlib.md5(service_name.encode()).hexdigest(), 16) % 1000
        method_hash = int(hashlib.md5(method_name.encode()).hexdigest(), 16) % 1000
        endpoint_hash = int(hashlib.md5(api_endpoint.encode()).hexdigest(), 16) % 1000
        
        # Check if critical service
        is_critical_service = 1 if service_name in config.CRITICAL_SERVICES else 0
        
        # Combine all features
        basic_features = [
            self.scale(message_length, 0, 1000),
            self.scale(word_count, 0, 100),
            digit_ratio,
            special_char_ratio,
            self.scale(service_hash, 0, 1000),
            self.scale(method_hash, 0, 1000),
            self.scale(endpoint_hash, 0, 1000),
            slow_response,
            very_slow_response,
            status_code_error,
            status_code_warning,
            status_code_success,
            is_critical_service,
            self.scale(response_time, 0, 10),
        ]
        
        # Get advanced features
        temporal_features = self.extract_temporal_features()
        sequential_features = self.extract_sequential_features(log_request)
        text_features = self.extract_text_features(message)
        
        # Combine all features
        all_features = (
            basic_features + 
            log_level_encoding + 
            temporal_features + 
            sequential_features + 
            text_features
        )
        
        return all_features
    
    def get_adaptive_threshold(self, service_name: str) -> float:
        """Get adaptive threshold based on service and recent history"""
        # Use service-specific threshold if available
        if service_name in config.CRITICAL_SERVICES:
            base_threshold = config.ANOMALY_THRESHOLD["CRITICAL_SERVICES"]
        else:
            base_threshold = config.ANOMALY_THRESHOLD["DEFAULT"]
        
        # Adjust based on recent anomaly rate
        if len(self.anomaly_history) > 10:
            recent_anomaly_rate = sum(self.anomaly_history) / len(self.anomaly_history)
            if recent_anomaly_rate > 0.3:  # High anomaly rate
                base_threshold += 0.1  # Increase threshold to reduce false positives
            elif recent_anomaly_rate < 0.05:  # Low anomaly rate
                base_threshold -= 0.05  # Decrease threshold to be more sensitive
        
        return np.clip(base_threshold, 0.4, 0.95)
    
    def get_update_frequency(self) -> int:
        """Determine how often to save model based on anomaly rate"""
        if len(self.anomaly_history) < 10:
            return config.UPDATE_FREQUENCY["NORMAL"]
        
        recent_anomaly_rate = sum(self.anomaly_history) / len(self.anomaly_history)
        
        if recent_anomaly_rate > 0.2:
            return config.UPDATE_FREQUENCY["HIGH_ANOMALY"]
        elif recent_anomaly_rate < 0.05:
            return config.UPDATE_FREQUENCY["STABLE"]
        else:
            return config.UPDATE_FREQUENCY["NORMAL"]
    
    def process_log(self, log_request: Dict) -> Tuple[str, float]:
        """Process a log entry and detect anomalies with warm-up logic."""
        start_time = time.time()

        # Extract features
        features = self.extract_features(log_request)
        instance = {i: feature for i, feature in enumerate(features)}

        # --------------------------
        # 1. WARM-UP MODE
        # --------------------------
        if self.training_only:
            for model_name, model in self.classifier:
                try:
                    model.learn_one(instance)
                except Exception as e:
                    logger.error(f"Warm-up learning error [{model_name}]: {e}")

            self.training_samples += 1
            self.processed_count += 1
            # Ensure log has timestamp before appending
            if "timestamp" not in log_request:
                log_request["timestamp"] = datetime.utcnow().isoformat() + "Z"
            self.log_history.append(log_request)

            # Exit warm-up when threshold reached
            if self.training_samples >= config.MIN_TRAINING_SAMPLES:
                self.training_only = False
                logger.info(
                    f"🟢 Warm-up complete: {self.training_samples} samples. "
                    f"Switching to anomaly detection mode."
                )

            # During warm-up: always return NORMAL with score=0.0
            return "NORMAL", 0.0

        # --------------------------
        # 2. SCORING PHASE
        # --------------------------
        anomaly_scores = []
        for model_name, model in self.classifier:
            try:
                score = model.score_one(instance)
                anomaly_scores.append(score)
            except Exception as e:
                logger.error(f"Scoring error [{model_name}]: {e}")
                anomaly_scores.append(0.0)

        anomaly_score = float(np.mean(anomaly_scores)) if anomaly_scores else 0.0

        # Threshold
        service_name = log_request.get("service", "unknown")
        threshold = self.get_adaptive_threshold(service_name)

        # Final decision
        is_anomaly = anomaly_score > threshold
        decision = "ANOMALY" if is_anomaly else "NORMAL"

        # --------------------------
        # 3. SAFE ONLINE LEARNING
        # --------------------------
        # Learn ONLY IF the log was classified NORMAL
        if not is_anomaly:
            for model_name, model in self.classifier:
                try:
                    model.learn_one(instance)
                except Exception as e:
                    logger.error(f"Online learn error [{model_name}]: {e}")

        # Histories
        self.feedback_history.append(anomaly_score)
        # Ensure log has timestamp before appending
        if "timestamp" not in log_request:
            log_request["timestamp"] = datetime.utcnow().isoformat() + "Z"
        self.log_history.append(log_request)
        self.processed_count += 1

        # Track anomaly
        self.anomaly_history.append(1 if is_anomaly else 0)
        if is_anomaly:
            self.anomaly_count += 1
            self.service_metrics[service_name]["error_count"] += 1
            self.service_metrics[service_name]["last_anomaly_time"] = datetime.now()
            logger.warning(
                f"🚨 Anomaly detected in {service_name}: "
                f"Score={anomaly_score:.3f}, Threshold={threshold:.3f}"
            )

        # --------------------------
        # 4. ADAPTIVE SAVE FREQUENCY
        # --------------------------
        update_freq = self.get_update_frequency()
        if (self.processed_count - self.last_save_count) >= update_freq:
            self.save_model()
            self.last_save_count = self.processed_count

        # Log system metrics
        if config.ENABLE_METRICS:
            duration = (time.time() - start_time) * 1000
            logger.info(
                f"Processed log in {duration:.2f}ms | "
                f"Score={anomaly_score:.3f} | "
                f"Threshold={threshold:.3f} | "
                f"Decision={decision}"
            )

        return decision, anomaly_score
    
    def detect_slow_trends(self):
        """Detect if API response times are increasing"""
        if len(self.log_history) < 10:
            return
        
        slow_calls = [log for log in self.log_history if log.get('response_time', 0) > config.SLOW_THRESHOLD]
        
        if slow_calls:
            avg_slow_response = np.mean([log.get('response_time', 0) for log in slow_calls])
            
            if len(slow_calls) > 5 or avg_slow_response > (config.SLOW_THRESHOLD * 2):
                logger.warning(
                    f"⚠️ Increasing API response times detected! "
                    f"Slow calls: {len(slow_calls)}, "
                    f"Avg: {avg_slow_response:.2f}s"
                )
                self.raise_failure_flag()
    
    def raise_failure_flag(self):
        """Alert on potential future failure"""
        logger.critical("🔴 CRITICAL: Service failure predicted due to sustained slow responses!")
    
    def save_model(self):
        """Save the trained ensemble model to file"""
        try:
            self.persistence.save_model(self.classifier)
            logger.info(f"✅ Model saved successfully to file (after {self.processed_count} logs)")
        except Exception as e:
            logger.error(f"❌ Error saving model: {e}")
    
    def load_model(self):
        """Load the trained ensemble model from file or create new one"""
        model = self.persistence.load_model()
        if model:
            logger.info("✅ Model loaded successfully from file")
            return model
        else:
            logger.info("ℹ️ No saved model found. Creating new ensemble model")
            return self._get_ensemble_model()
    
    def get_statistics(self) -> Dict:
        """Get detector statistics"""
        anomaly_rate = self.anomaly_count / max(self.processed_count, 1)
        
        stats = {
            "total_processed": self.processed_count,
            "total_anomalies": self.anomaly_count,
            "anomaly_rate": f"{anomaly_rate*100:.2f}%",
            "services_monitored": len(self.service_metrics),
            "cache_size": len(self.feature_cache),
            "total_model_saves": self.last_save_count,  # Renamed to avoid Pydantic conflict
        }
        
        # Add storage info
        try:
            storage_info = self.persistence.get_storage_info()
            stats["storage"] = storage_info
        except:
            pass
        
        return stats
    
    def get_calibration_snapshot(self) -> Dict[str, Any]:
        """
        Returns a snapshot of anomaly-score distribution and thresholds,
        both globally and per service, to aid threshold calibration.
        """
        # Global scores
        scores = list(self.feedback_history)
        total = len(scores)

        if total > 0:
            avg_score = float(np.mean(scores))
            p95_score = float(np.percentile(scores, 95))
            max_score = float(np.max(scores))
        else:
            avg_score = p95_score = max_score = 0.0

        total_anomalies = int(self.anomaly_count)
        total_processed = int(self.processed_count)
        global_anomaly_rate = (
            total_anomalies / total_processed if total_processed > 0 else 0.0
        )

        # Build per-service stats
        per_service: Dict[str, Any] = {}
        # Collect unique services from service_metrics and log_history
        services = set(self.service_metrics.keys()) | {
            log.get("service", "unknown") for log in self.log_history
        }

        for service in services:
            if not service:
                continue

            # Scores for this service by aligning feedback_history and log_history
            svc_scores: List[float] = []
            for score, log in zip(self.feedback_history, self.log_history):
                if log.get("service", "unknown") == service:
                    svc_scores.append(score)

            svc_total = len(svc_scores)
            if svc_total > 0:
                svc_avg = float(np.mean(svc_scores))
                svc_p95 = float(np.percentile(svc_scores, 95))
                svc_max = float(np.max(svc_scores))
            else:
                svc_avg = svc_p95 = svc_max = 0.0

            metrics = self.service_metrics.get(service, {})
            error_count = int(metrics.get("error_count", 0))
            total_count = int(metrics.get("total_count", 0))
            last_anomaly_time = metrics.get("last_anomaly_time")

            svc_anomaly_rate = (
                error_count / total_count if total_count > 0 else 0.0
            )

            threshold = self.get_adaptive_threshold(service)

            per_service[service] = {
                "avg_score": svc_avg,
                "p95_score": svc_p95,
                "max_score": svc_max,
                "threshold": float(threshold),
                "error_count": error_count,
                "total_count": total_count,
                "anomaly_rate": svc_anomaly_rate,
                "last_anomaly_time": (
                    last_anomaly_time.isoformat() if last_anomaly_time else None
                ),
            }

        snapshot = {
            "global": {
                "warmup_active": self.training_only,
                "training_samples": int(
                    getattr(self, "training_samples", 0)
                ),
                "avg_score": avg_score,
                "p95_score": p95_score,
                "max_score": max_score,
                "total_processed": total_processed,
                "total_anomalies": total_anomalies,
                "global_anomaly_rate": global_anomaly_rate,
            },
            "per_service": per_service,
        }

        return snapshot

