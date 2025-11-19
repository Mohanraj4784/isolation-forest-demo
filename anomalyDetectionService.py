import os
import pickle
import logging
import numpy as np
from sklearn.ensemble import IsolationForest
from collections import deque

MODEL_PATH = "/home/f176/Documents/ai_model/moa_model.pkl"
WINDOW_SIZE = 10000  # Number of recent logs to analyze as a sequence

class AnomalyDetectionService:
    def __init__(self):
        self.classifier = self.load_model() or IsolationForest(contamination=0.1)
        self.log_history = deque(maxlen=WINDOW_SIZE)
        logging.info("✅ Model initialized successfully!")
    
    def process_log(self, log_request):
        logging.info(log_request)
        instance = self.create_instance(log_request)
        self.log_history.append(instance)

        if len(self.log_history) == WINDOW_SIZE:
            feature_matrix = np.array([list(log.values()) for log in self.log_history])
            anomaly_scores = self.classifier.decision_function(feature_matrix)
            anomaly_score = -anomaly_scores[-1]  # Negative score indicates anomaly
        else:
            anomaly_score = 0.0  # Not enough data for sequence-based anomaly detection

        logging.info(f"✅ Anomaly Score: {anomaly_score}")

        if anomaly_score > 0.7:
            logging.warning(f"🚨 Anomaly Detected: Score = {anomaly_score}")

        # Corrected line: Use `learn_one()` instead of `fit()`
        for instance in self.log_history:
            self.classifier.learn_one(instance, 0)  # '0' is assumed to be the normal label

        self.save_model()
        return anomaly_score

    
    def create_instance(self, log_request):
        features = self.extract_features(log_request)
        return {f'feature_{i}': val for i, val in enumerate(features)}
    
    def extract_features(self, log_request):
        message = log_request.get("message", "")
        logging.basicConfig(level=logging.INFO)
        logging.info(f"Message:{message}")
        message_length = len(message)
        word_count = len(message.split()) if message else 0
        digit_count = sum(c.isdigit() for c in message)
        special_char_count = sum(not c.isalnum() for c in message)
        
        digit_ratio = digit_count / message_length if message_length > 0 else 0.0
        special_char_ratio = special_char_count / message_length if message_length > 0 else 0.0
        
        log_level_number = self.map_log_level_to_number(log_request.get("level", ""))
        
        return [
            self.scale(message_length, 0, 1000),
            self.scale(word_count, 0, 100),
            digit_ratio,
            special_char_ratio,
            self.scale(log_level_number, 0, 5)
        ]
    
    @staticmethod
    def scale(value, min_val, max_val):
        return (value - min_val) / (max_val - min_val) if max_val > min_val else 0.0
    
    @staticmethod
    def map_log_level_to_number(level):
        levels = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3, "FATAL": 4, "CRITICAL": 5}
        return levels.get(level.upper(), 0)
    
    def save_model(self):
        try:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self.classifier, f)
            logging.info("✅ Model saved successfully!")
        except Exception as e:
            logging.error(f"❌ Error saving model: {e}")
    
    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    model = pickle.load(f)
                logging.info("✅ Model loaded successfully!")
                return model
            except Exception as e:
                logging.warning("ℹ️ No previous model found, starting fresh.")
        return None

