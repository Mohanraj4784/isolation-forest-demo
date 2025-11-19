"""
Test script for the enhanced anomaly detection system
"""
import requests
import json
import time
from datetime import datetime
import random

# API endpoint
BASE_URL = "http://127.0.0.1:8000"

# Sample log data for testing
SAMPLE_LOGS = [
    # Normal logs
    {
        "message": "User successfully logged in",
        "service": "auth-service",
        "method": "login",
        "endpoint": "/api/v1/auth/login",
        "response_time": 0.12,
        "level": "INFO",
        "correlationId": "abc-123",
        "status_code": "200"
    },
    {
        "message": "Retrieved user profile data",
        "service": "user-service",
        "method": "getProfile",
        "endpoint": "/api/v1/users/profile",
        "response_time": 0.08,
        "level": "INFO",
        "correlationId": "def-456",
        "status_code": "200"
    },
    {
        "message": "Database query executed successfully",
        "service": "database-service",
        "method": "executeQuery",
        "endpoint": "/internal/query",
        "response_time": 0.05,
        "level": "DEBUG",
        "correlationId": "ghi-789",
        "status_code": "200"
    },
    # Anomalous logs
    {
        "message": "CRITICAL: Database connection timeout after 30 seconds. Exception: TimeoutError at line 234",
        "service": "database-service",
        "method": "connect",
        "endpoint": "/internal/connect",
        "response_time": 30.5,
        "level": "ERROR",
        "correlationId": "error-001",
        "status_code": "500"
    },
    {
        "message": "Payment processing failed: Insufficient funds. Exception in PaymentProcessor.process()",
        "service": "payment-service",
        "method": "processPayment",
        "endpoint": "/api/v1/payments/process",
        "response_time": 5.2,
        "level": "ERROR",
        "correlationId": "error-002",
        "status_code": "400"
    },
    {
        "message": "Memory allocation failed. OutOfMemoryError: Java heap space",
        "service": "user-service",
        "method": "processLargeFile",
        "endpoint": "/api/v1/files/process",
        "response_time": 45.0,
        "level": "FATAL",
        "correlationId": "error-003",
        "status_code": "500"
    },
    {
        "message": "SQL Injection attempt detected: DROP TABLE users; --",
        "service": "database-service",
        "method": "executeQuery",
        "endpoint": "/api/v1/query",
        "response_time": 0.01,
        "level": "CRITICAL",
        "correlationId": "security-001",
        "status_code": "403"
    },
]

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def test_health_check():
    """Test health check endpoint"""
    print_header("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_anomaly_detection():
    """Test anomaly detection with sample logs"""
    print_header("Testing Anomaly Detection")
    
    results = []
    
    for i, log in enumerate(SAMPLE_LOGS, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Service: {log['service']}")
        print(f"Message: {log['message'][:80]}...")
        print(f"Response Time: {log['response_time']}s")
        print(f"Status Code: {log['status_code']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/ai/logs/ingest",
                json=log
            )
            
            if response.status_code == 200:
                result = response.json()
                results.append(result)
                
                # Format output with colors (using emoji)
                decision_icon = "🚨" if result['decision'] == "ANOMALY" else "✅"
                critical_icon = "⚠️" if result['is_critical_service'] else "ℹ️"
                
                print(f"\n{decision_icon} Decision: {result['decision']}")
                print(f"   Anomaly Score: {result['anomaly_score']:.4f}")
                print(f"   Threshold: {result['threshold']:.4f}")
                print(f"   Processing Time: {result['processing_time_ms']:.2f}ms")
                print(f"{critical_icon} Critical Service: {result['is_critical_service']}")
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(response.text)
        
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        time.sleep(0.1)  # Small delay between requests
    
    return results

def test_statistics():
    """Test statistics endpoint"""
    print_header("Testing Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/ai/stats")
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_service_metrics():
    """Test service metrics endpoint"""
    print_header("Testing Service Metrics")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/ai/services")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        print(f"\nTotal Services Monitored: {data['total_services']}")
        print("\nPer-Service Metrics:")
        for service, metrics in data['services'].items():
            print(f"\n  {service}:")
            for key, value in metrics.items():
                print(f"    {key}: {value}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_config():
    """Test configuration endpoint"""
    print_header("Testing Configuration")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/ai/config")
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_threshold_adjustment():
    """Test threshold adjustment"""
    print_header("Testing Threshold Adjustment")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/ai/threshold/adjust",
            params={"service": "test-service", "threshold": 0.8}
        )
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def load_test(duration_seconds=10, requests_per_second=10):
    """Perform a simple load test"""
    print_header(f"Load Test ({duration_seconds}s @ {requests_per_second} req/s)")
    
    start_time = time.time()
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    total_processing_time = 0
    
    while time.time() - start_time < duration_seconds:
        batch_start = time.time()
        
        for _ in range(requests_per_second):
            # Pick a random log
            log = random.choice(SAMPLE_LOGS)
            
            try:
                response = requests.post(
                    f"{BASE_URL}/v1/ai/logs/ingest",
                    json=log,
                    timeout=5
                )
                
                total_requests += 1
                
                if response.status_code == 200:
                    successful_requests += 1
                    result = response.json()
                    total_processing_time += result['processing_time_ms']
                else:
                    failed_requests += 1
            
            except Exception as e:
                failed_requests += 1
                total_requests += 1
        
        # Wait to maintain requests_per_second rate
        elapsed = time.time() - batch_start
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
    
    # Print results
    total_time = time.time() - start_time
    avg_processing_time = total_processing_time / max(successful_requests, 1)
    actual_rps = total_requests / total_time
    
    print(f"\n📊 Load Test Results:")
    print(f"   Duration: {total_time:.2f}s")
    print(f"   Total Requests: {total_requests}")
    print(f"   Successful: {successful_requests} ({successful_requests/total_requests*100:.1f}%)")
    print(f"   Failed: {failed_requests} ({failed_requests/total_requests*100:.1f}%)")
    print(f"   Actual RPS: {actual_rps:.2f}")
    print(f"   Avg Processing Time: {avg_processing_time:.2f}ms")
    print(f"   Throughput: {1000/avg_processing_time:.2f} logs/second (theoretical max)")

def run_all_tests():
    """Run all tests"""
    print_header("ENHANCED LOG ANOMALY DETECTION SYSTEM - TEST SUITE")
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Configuration", test_config),
        ("Anomaly Detection", test_anomaly_detection),
        ("Statistics", test_statistics),
        ("Service Metrics", test_service_metrics),
        ("Threshold Adjustment", test_threshold_adjustment),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
        time.sleep(0.5)
    
    # Load test
    try:
        load_test(duration_seconds=10, requests_per_second=20)
    except Exception as e:
        print(f"\n❌ Load test crashed: {e}")
    
    # Final summary
    print_header("TEST SUMMARY")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed. Please review the output above.")

if __name__ == "__main__":
    print("\n⏳ Make sure the API server is running (python app_enhanced.py)")
    print("   Press Ctrl+C to cancel, or wait 3 seconds to start tests...")
    
    try:
        time.sleep(3)
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")

