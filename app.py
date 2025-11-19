from fastapi import FastAPI
from moa_service import MOAAnomalyDetectionService
from anomalyDetectionService import AnomalyDetectionService
from logAnomalyDetector import LogAnomalyDetector
from pydantic import BaseModel
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
detector = LogAnomalyDetector()

class LogRequest(BaseModel):
    message: str
    service: str
    method: str
    endpoint: str
    response_time: float
    level: str
    correlationId: str
    status_code: str


@app.post("/v1/ai/logs/ingest")
def detect_anomaly(log_request: LogRequest):
    score = detector.process_log(log_request.dict())
    return {"anomaly_score": score}

# Run the FastAPI server using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)