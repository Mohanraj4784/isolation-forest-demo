from moa_service import MOAAnomalyDetectionService

def test_anomaly_detection():
    model_service = MOAAnomalyDetectionService()
    log_request = {"message": "Critical system failure!!!", "level": "FATAL"}
    score = model_service.process_log(log_request)
    assert 0.0 <= score <= 1.0

if __name__ == "__main__":
    test_anomaly_detection()
    print("✅ All tests passed!")
