#!/usr/bin/env python3
"""
Model Training Script
=====================
This script trains the anomaly detection model using log data from a JSON file.

Usage:
    python train_model.py [--data-file path/to/data.json] [--mode api|direct]

Modes:
    api     - Send logs to the running API server (requires API to be running)
    direct  - Train the model directly without API (faster, no API needed)
"""

import json
import sys
import time
import argparse
import requests
from pathlib import Path
from typing import List, Dict
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_training_data(file_path: str) -> List[Dict]:
    """Load training data from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"✅ Loaded {len(data)} log entries from {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"❌ Training data file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in training data file: {e}")
        sys.exit(1)


def train_via_api(training_data: List[Dict], api_url: str = "http://127.0.0.1:8000"):
    """Train model by sending requests to the API"""
    logger.info(f"🔄 Training mode: API (sending to {api_url})")
    
    # Check if API is available
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code != 200:
            logger.error(f"❌ API is not healthy. Status: {response.status_code}")
            sys.exit(1)
        logger.info("✅ API server is healthy")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Cannot connect to API at {api_url}")
        logger.error(f"   Make sure the API is running: python app_enhanced.py")
        sys.exit(1)
    
    # Train with each log entry
    successful = 0
    failed = 0
    anomalies_detected = 0
    
    for i, log_entry in enumerate(training_data, 1):
        try:
            response = requests.post(
                f"{api_url}/v1/ai/logs/ingest",
                json=log_entry,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                successful += 1
                
                if result.get("anomaly_detected"):
                    anomalies_detected += 1
                    logger.info(f"   [{i}/{len(training_data)}] ⚠️  Anomaly detected: {log_entry.get('service', 'unknown')} - {log_entry.get('message', '')[:50]}")
                else:
                    logger.info(f"   [{i}/{len(training_data)}] ✅ Normal: {log_entry.get('service', 'unknown')}")
            else:
                failed += 1
                logger.error(f"   [{i}/{len(training_data)}] ❌ Failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            failed += 1
            logger.error(f"   [{i}/{len(training_data)}] ❌ Request failed: {e}")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TRAINING SUMMARY")
    print("="*70)
    print(f"Total logs processed:     {len(training_data)}")
    print(f"Successful:               {successful}")
    print(f"Failed:                   {failed}")
    print(f"Anomalies detected:       {anomalies_detected}")
    print(f"Success rate:             {(successful/len(training_data)*100):.1f}%")
    print("="*70)
    
    # Get updated statistics
    try:
        stats_response = requests.get(f"{api_url}/v1/ai/stats", timeout=5)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print("\n📈 MODEL STATISTICS")
            print("="*70)
            print(f"Total processed:          {stats.get('total_processed', 0)}")
            print(f"Total anomalies:          {stats.get('total_anomalies', 0)}")
            print(f"Anomaly rate:             {stats.get('anomaly_rate', 'N/A')}")
            print(f"Services monitored:       {stats.get('services_monitored', 0)}")
            print(f"Model saves:              {stats.get('total_model_saves', 0)}")
            print("="*70)
    except:
        pass


def train_direct(training_data: List[Dict]):
    """Train model directly without API"""
    logger.info("🔄 Training mode: Direct (no API required)")
    
    try:
        # Import the detector
        from enhanced_anomaly_detector import EnhancedLogAnomalyDetector
        
        # Initialize detector
        logger.info("Initializing detector...")
        detector = EnhancedLogAnomalyDetector()
        
        # Train with each log entry
        successful = 0
        anomalies_detected = 0
        
        for i, log_entry in enumerate(training_data, 1):
            try:
                # Process the log
                result = detector.detect_anomaly(log_entry)
                successful += 1
                
                if result.get("anomaly_detected"):
                    anomalies_detected += 1
                    logger.info(f"   [{i}/{len(training_data)}] ⚠️  Anomaly detected: {log_entry.get('service', 'unknown')} - Score: {result.get('anomaly_score', 0):.3f}")
                else:
                    logger.info(f"   [{i}/{len(training_data)}] ✅ Normal: {log_entry.get('service', 'unknown')} - Score: {result.get('anomaly_score', 0):.3f}")
                    
            except Exception as e:
                logger.error(f"   [{i}/{len(training_data)}] ❌ Error processing log: {e}")
        
        # Save the trained model
        logger.info("💾 Saving trained model...")
        detector.save_model()
        
        # Print summary
        print("\n" + "="*70)
        print("📊 TRAINING SUMMARY")
        print("="*70)
        print(f"Total logs processed:     {len(training_data)}")
        print(f"Successful:               {successful}")
        print(f"Anomalies detected:       {anomalies_detected}")
        print(f"Success rate:             {(successful/len(training_data)*100):.1f}%")
        print("="*70)
        
        # Get statistics
        stats = detector.get_statistics()
        print("\n📈 MODEL STATISTICS")
        print("="*70)
        print(f"Total processed:          {stats.get('total_processed', 0)}")
        print(f"Total anomalies:          {stats.get('total_anomalies', 0)}")
        print(f"Anomaly rate:             {stats.get('anomaly_rate', 'N/A')}")
        print(f"Services monitored:       {stats.get('services_monitored', 0)}")
        print(f"Model saves:              {stats.get('total_model_saves', 0)}")
        print("="*70)
        
        logger.info("✅ Training completed successfully!")
        
    except ImportError as e:
        logger.error(f"❌ Cannot import detector: {e}")
        logger.error("   Make sure enhanced_anomaly_detector.py is in the current directory")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Train the anomaly detection model with log data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train using API (default)
  python train_model.py

  # Train directly without API (faster)
  python train_model.py --mode direct

  # Use custom data file
  python train_model.py --data-file my_logs.json

  # Train directly with custom data file
  python train_model.py --data-file my_logs.json --mode direct
        """
    )
    
    parser.add_argument(
        '--data-file',
        type=str,
        default='training_data.json',
        help='Path to training data JSON file (default: training_data.json)'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['api', 'direct'],
        default='api',
        help='Training mode: api (requires running API) or direct (no API needed, faster)'
    )
    
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://127.0.0.1:8000',
        help='API URL for api mode (default: http://127.0.0.1:8000)'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "="*70)
    print("🤖 MODEL TRAINING SCRIPT")
    print("="*70)
    print(f"Data file:    {args.data_file}")
    print(f"Mode:         {args.mode}")
    if args.mode == 'api':
        print(f"API URL:      {args.api_url}")
    print("="*70 + "\n")
    
    # Load training data
    training_data = load_training_data(args.data_file)
    
    # Train based on mode
    if args.mode == 'api':
        train_via_api(training_data, args.api_url)
    else:
        train_direct(training_data)
    
    print("\n✅ Training complete!\n")


if __name__ == "__main__":
    main()

