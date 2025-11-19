"""
Enhanced FastAPI application for Log Anomaly Detection
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging
import time
from enhanced_anomaly_detector import EnhancedLogAnomalyDetector
import config

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enhanced Log Anomaly Detection API",
    description="AI-powered anomaly detection for application logs",
    version="2.0.0"
)

# Initialize enhanced detector
detector = EnhancedLogAnomalyDetector()

class LogRequest(BaseModel):
    message: str = Field(..., description="Log message content")
    service: str = Field(..., description="Service name")
    method: str = Field(..., description="Method or function name")
    endpoint: str = Field(..., description="API endpoint")
    response_time: float = Field(..., description="Response time in seconds")
    level: str = Field(..., description="Log level (DEBUG, INFO, WARN, ERROR, etc.)")
    correlationId: str = Field(..., description="Correlation ID for request tracking")
    status_code: str = Field(..., description="HTTP status code")
    timestamp: Optional[str] = Field(None, description="Log timestamp (ISO format)")

class AnomalyResponse(BaseModel):
    decision: str
    anomaly_score: float
    threshold: float
    processing_time_ms: float
    service: str
    is_critical_service: bool

class StatisticsResponse(BaseModel):
    total_processed: int
    total_anomalies: int
    anomaly_rate: str
    services_monitored: int
    cache_size: int
    total_model_saves: int  # Renamed to avoid Pydantic conflict
    uptime_seconds: float

# Track API start time
api_start_time = time.time()

@app.get("/")
def root():
    """API health check"""
    return {
        "status": "healthy",
        "service": "Enhanced Log Anomaly Detection API",
        "version": "2.0.0",
        "uptime_seconds": time.time() - api_start_time
    }

@app.get("/health")
def health_check():
    """Detailed health check"""
    stats = detector.get_statistics()
    return {
        "status": "healthy",
        "uptime_seconds": time.time() - api_start_time,
        "statistics": stats
    }

@app.post("/v1/ai/logs/ingest", response_model=AnomalyResponse)
def detect_anomaly(log_request: LogRequest):
    """
    Detect anomalies in log entries
    
    Returns:
        - decision: ANOMALY or NORMAL
        - anomaly_score: Numerical anomaly score
        - threshold: Dynamic threshold used for detection
        - processing_time_ms: Time taken to process
    """
    try:
        start_time = time.time()
        
        # Process the log
        decision, anomaly_score = detector.process_log(log_request.dict())
        
        # Get threshold used
        threshold = detector.get_adaptive_threshold(log_request.service)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        is_critical = log_request.service in config.CRITICAL_SERVICES
        
        return AnomalyResponse(
            decision=decision,
            anomaly_score=round(anomaly_score, 4),
            threshold=round(threshold, 4),
            processing_time_ms=round(processing_time, 2),
            service=log_request.service,
            is_critical_service=is_critical
        )
    
    except Exception as e:
        logger.error(f"Error processing log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing log: {str(e)}")

class FeedbackRequest(BaseModel):
    log_request: LogRequest
    is_anomaly: bool = Field(..., description="True if this was actually an anomaly")

@app.post("/v1/ai/logs/feedback")
def provide_feedback(feedback: FeedbackRequest):
    """
    Provide feedback to improve model accuracy
    
    Parameters:
        - feedback: Contains log_request and is_anomaly flag
    """
    try:
        # Extract features and update model with feedback
        features = detector.extract_features(feedback.log_request.dict())
        instance = {i: feature for i, feature in enumerate(features)}
        
        # Update all models in ensemble with feedback
        for model_name, model in detector.classifier:
            try:
                # Learn from the feedback
                model.learn_one(instance)
            except Exception as e:
                logger.error(f"Error updating {model_name} with feedback: {e}")
        
        # Save updated model
        detector.save_model()
        
        logger.info(f"✅ Feedback received: is_anomaly={feedback.is_anomaly} for service={feedback.log_request.service}")
        
        return {
            "status": "success",
            "message": "Feedback received and model updated"
        }
    
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")

@app.get("/v1/ai/stats", response_model=StatisticsResponse)
def get_statistics():
    """
    Get detector statistics and performance metrics
    """
    try:
        stats = detector.get_statistics()
        stats['uptime_seconds'] = time.time() - api_start_time
        return StatisticsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@app.get("/v1/ai/services")
def get_service_metrics():
    """
    Get per-service metrics
    """
    try:
        service_data = {}
        for service, metrics in detector.service_metrics.items():
            service_data[service] = {
                "total_requests": metrics['total_count'],
                "error_count": metrics['error_count'],
                "error_rate": f"{(metrics['error_count'] / max(metrics['total_count'], 1) * 100):.2f}%",
                "avg_response_time": f"{sum(metrics['response_times']) / max(len(metrics['response_times']), 1):.3f}s" if metrics['response_times'] else "N/A",
                "last_anomaly": metrics['last_anomaly_time'].isoformat() if metrics['last_anomaly_time'] else None,
                "is_critical": service in config.CRITICAL_SERVICES
            }
        
        return {
            "services": service_data,
            "total_services": len(service_data)
        }
    
    except Exception as e:
        logger.error(f"Error getting service metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting service metrics: {str(e)}")

class ThresholdRequest(BaseModel):
    service: str = Field(..., description="Service name")
    threshold: float = Field(..., ge=0.0, le=1.0, description="New threshold value")

@app.post("/v1/ai/threshold/adjust")
def adjust_threshold(request: ThresholdRequest):
    """
    Manually adjust anomaly threshold for a specific service
    """
    try:
        detector.service_thresholds[request.service] = request.threshold
        logger.info(f"✅ Threshold adjusted for {request.service}: {request.threshold}")
        
        return {
            "status": "success",
            "message": f"Threshold for {request.service} set to {request.threshold}",
            "service": request.service,
            "new_threshold": request.threshold
        }
    
    except Exception as e:
        logger.error(f"Error adjusting threshold: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adjusting threshold: {str(e)}")

@app.post("/v1/ai/model/save")
def force_save_model(background_tasks: BackgroundTasks):
    """
    Force save the current model (useful for backups)
    """
    try:
        background_tasks.add_task(detector.save_model)
        return {
            "status": "success",
            "message": "Model save scheduled"
        }
    
    except Exception as e:
        logger.error(f"Error scheduling model save: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error scheduling model save: {str(e)}")

@app.get("/v1/ai/config")
def get_config():
    """
    Get current configuration
    """
    return {
        "update_frequency": config.UPDATE_FREQUENCY,
        "anomaly_threshold": config.ANOMALY_THRESHOLD,
        "slow_threshold": config.SLOW_THRESHOLD,
        "critical_services": config.CRITICAL_SERVICES,
        "log_history_size": config.LOG_HISTORY_SIZE,
        "batch_size": config.BATCH_SIZE,
        "save_interval": config.SAVE_INTERVAL,
    }

# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Enhanced Log Anomaly Detection API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

