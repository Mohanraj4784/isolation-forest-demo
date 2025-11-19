import os
import pickle
import logging
from river import tree
import numpy as np

MODEL_PATH = "/home/f176/Documents/ai_model/moa_model.pkl"

class MOAAnomalyDetectionService:
    def __init__(self):
        self.classifier = self.load_model() or tree.HoeffdingTreeClassifier()
        logging.info("✅ Model initialized successfully!")
    
    def process_log(self, log_request):
        logging.info(log_request)
        instance = self.create_instance(log_request)
        votes = list(self.classifier.predict_proba_one(instance).values())
        anomaly_score = votes[1] if len(votes) > 1 else 0.0
        logging.info("✅ anomaly_score : {anomaly_score} ")
        if anomaly_score > 0.7:
            logging.warning(f"🚨 Anomaly Detected: Score = {anomaly_score}")
        self.classifier.learn_one(instance, 0)
        self.save_model()
        return anomaly_score
    
    def create_instance(self, log_request):
        features = self.extract_features(log_request)
        return {f'feature_{i}': val for i, val in enumerate(features)}
    
    def extract_features(self, log_request):
        message = log_request.get("message", "")
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
            self.scale(log_level_number, 0, 4)
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
                logging.info("ℹ️ No previous model found, starting fresh.")
        return None

