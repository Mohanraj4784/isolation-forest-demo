import re
import hashlib
import numpy as np
import logging
import pickle  # For saving/loading model
import os
from collections import deque
from river import anomaly
from ModelPersistence import MySQLModelPersistence
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ERROR_KEYWORDS = ["error", "exception", "failed", "timeout", "denied", "unavailable"]
SLOW_THRESHOLD = 3  # Response time in seconds

class LogAnomalyDetector:
    def __init__(self):
         # Initialize MySQL persistence
        self.persistence = MySQLModelPersistence(
            host="localhost", 
            user="CARDHOST", 
            password="CARDHOST", 
            database="AI_MODEL"
        )
        #self.classifier = self.load_model()  # Load model if available, else create new one
        self.classifier = self.load_model()
        self.anomaly_threshold = 0.7
        #self.anomaly_threshold = np.mean(anomaly_scores) + (1.5 * np.std(anomaly_scores))
        self.feedback_history = deque(maxlen=100)
        self.log_history = deque(maxlen=500)
    
    def scale(self, value, min_value, max_value):
        return (value - min_value) / (max_value - min_value) if max_value > min_value else 0
    
    def extract_features(self, log_request):
        """Extracts relevant features from log."""
        message = log_request.get("message", "")
        service_name = log_request.get("service", "unknown")
        method_name = log_request.get("method", "unknown")
        api_endpoint = log_request.get("endpoint", "unknown")
        response_time = float(log_request.get("response_time", 0))
        status_code = int(log_request.get("status_code", 200))

        # Numeric features
        message_length = len(message)
        word_count = len(message.split()) if message else 0
        logger.info("word_count = %s",word_count)
        digit_count = sum(c.isdigit() for c in message)
        special_char_count = sum(not c.isalnum() and not c.isspace() for c in message)
        digit_ratio = digit_count / message_length if message_length > 0 else 0.0
        special_char_ratio = special_char_count / message_length if message_length > 0 else 0.0
        
        # Log Level Encoding
        log_levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL", "CRITICAL"]
        log_level = log_request.get("level", "").upper()
        log_level_encoding = [1 if log_level == level else 0 for level in log_levels]
        
        # Error-related features
        error_word_count = sum(1 for word in ERROR_KEYWORDS if word in message.lower())
        stack_trace_flag = 1 if "Exception" in message or "Traceback" in message else 0
        
        # Status Code Encoding
        status_code_error = 1 if status_code >= 500 else 0
        status_code_warning = 1 if 400 <= status_code < 500 else 0
        
        # Identify Slow Responses
        slow_response = 1 if response_time > SLOW_THRESHOLD else 0
        
        # Hash Service and API Name to Numeric Value
        service_hash = int(hashlib.md5(service_name.encode()).hexdigest(), 16) % 1000
        method_hash = int(hashlib.md5(method_name.encode()).hexdigest(), 16) % 1000
        
        return [
            self.scale(message_length, 0, 1000),
            self.scale(word_count, 0, 100),
            digit_ratio,
            special_char_ratio,
            error_word_count,
            stack_trace_flag,
            self.scale(service_hash, 0, 1000),
            self.scale(method_hash, 0, 100),
            slow_response,
            status_code_error,
            status_code_warning
        ] + log_level_encoding
    
    def process_log(self, log_request):
        """Detect anomalies in logs."""
        instance = {i: feature for i, feature in enumerate(self.extract_features(log_request))}
        logger.info("instance = %s",instance)
        anomaly_score = self.classifier.score_one(instance)
        logger.info("anomaly_score = %s", anomaly_score)
        # Update model with new data
        self.classifier.learn_one(instance)
        self.feedback_history.append(anomaly_score)
        self.update_threshold()
        #Updating the feedback
        #self.update_feedback(log_request,anomaly_score)
        # **Append the log to the history for slow trend detection**
        self.log_history.append(log_request)
        self.detect_slow_trends()
        
        # Save the updated model after learning
        self.save_model()

        # Make decision based on the anomaly score and threshold
        decision = "ANOMALY" if anomaly_score > self.anomaly_threshold else "NORMAL"
        if decision == "ANOMALY":
            logger.warning(f"Anomaly detected in {log_request.get('service', 'unknown')} ({log_request.get('method', 'unknown')})")
        else:
            logger.info("Log is normal.")
        
        # Return the decision and the anomaly score
        return decision, anomaly_score
    
    def update_threshold(self):
        """Adjusts anomaly threshold based on feedback history."""
        if len(self.feedback_history) > 10:
            avg_score = np.mean(self.feedback_history)
            self.anomaly_threshold = max(0.5, min(avg_score + 0.1, 0.9))

    def update_feedback(self, log_request, is_anomaly):
        """Manually updates feedback to improve model."""
        instance = {i: feature for i, feature in enumerate(self.extract_features(log_request))}
        true_label = 1 if is_anomaly else 0
        logger.info("true_label =%s",true_label)
        self.classifier.learn_one(instance, true_label)
        
        # Save the updated model after manual feedback
        self.save_model()
        logging.info("Model updated with feedback.")
    
    def detect_slow_trends(self):
        """Detects if API response times are increasing."""
        slow_calls = [log for log in self.log_history if log['response_time'] > SLOW_THRESHOLD]
        logger.info("slow_calls =%s",slow_calls)
          # Example: Calculate rolling average response time for slow calls
        if slow_calls:
            avg_slow_response = np.mean([log.get('response_time', 0) for log in slow_calls])
            logger.info("Average slow response time = %s", avg_slow_response)
        else:
            avg_slow_response = 0
            # Check if the count of slow calls exceeds the threshold or if the average is critically high
        if len(slow_calls) > 5 or avg_slow_response > (SLOW_THRESHOLD * 2):
            logger.warning("Increasing API response times detected! Possible future failure.")
            # Here you can raise a flag, e.g., set an internal variable, trigger an alert, etc.
            self.raise_failure_flag()

    

    def save_model(self):
            """Saves the trained model to MySQL."""
            try:
                self.persistence.save_model(self.classifier)
                logger.info("Model saved successfully to MySQL.")
            except Exception as e:
                logger.error(f"Error saving model: {e}")  

    def load_model(self):
            """Loads the trained model from MySQL, or creates a new one if not found."""
            model = self.persistence.load_model()
            if model:
                logger.info("Model loaded successfully from MySQL.")
                return model
            else:
                logger.info("No model found in MySQL. Creating a new one.")
                return anomaly.HalfSpaceTrees()


    def raise_failure_flag(self):
        """
        Function to take additional actions when a potential future failure is detected.
        For example, send an alert or trigger an automated remediation process.
        """
        # Example: Log critical message, send alert to monitoring system, etc.
        logger.critical("CRITICAL: Service failure predicted due to sustained slow responses!")
        # notify a monitoring system (email, SMS, API call to alerting service, etc.)

