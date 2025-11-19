import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
ENDPOINT = "/v1/ai/logs/ingest"

# ---- SAMPLE LOGS FOR TESTING ----
SAMPLE_LOGS = [
    {
        "message": "User login successful",
        "service": "auth-service",
        "method": "login",
        "endpoint": "/api/v1/auth/login",
        "response_time": 0.12,
        "level": "INFO",
        "correlationId": "test-1",
        "status_code": "200",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    },
    {
        "message": "Database timeout while fetching user",
        "service": "database-service",
        "method": "fetchUser",
        "endpoint": "/db/user",
        "response_time": 5.2,
        "level": "ERROR",
        "correlationId": "test-2",
        "status_code": "500",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    },
    {
        "message": "Payment gateway slow response",
        "service": "payments-service",
        "method": "charge",
        "endpoint": "/api/v1/pay",
        "response_time": 3.9,
        "level": "WARN",
        "correlationId": "test-3",
        "status_code": "200",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    },
    {
        "message": "Request completed",
        "service": "auth-service",
        "method": "check",
        "endpoint": "/api/v1/auth/check",
        "response_time": 0.20,
        "level": "INFO",
        "correlationId": "test-4",
        "status_code": "200",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
]


def run_tests():
    print("\n🔍 Running Enhanced Log Anomaly Detection Test...\n")

    total = len(SAMPLE_LOGS)
    normal_count = 0
    anomaly_count = 0
    success_count = 0
    fail_count = 0
    total_response_ms = 0

    # Per-service statistics
    per_service_stats = {}

    for idx, log_item in enumerate(SAMPLE_LOGS, start=1):
        url = BASE_URL + ENDPOINT
        start = time.time()

        try:
            resp = requests.post(url, json=log_item, timeout=5)
            elapsed_ms = (time.time() - start) * 1000
            total_response_ms += elapsed_ms

            if resp.status_code // 100 != 2:
                fail_count += 1
                print(f"[{idx}] ❌ FAIL | HTTP {resp.status_code}")
                continue

            success_count += 1
            data = resp.json()

            decision = data.get("decision")
            score = data.get("anomaly_score")
            threshold = data.get("threshold")

            # Update counters
            if decision == "ANOMALY":
                anomaly_count += 1
            else:
                normal_count += 1

            svc = log_item.get("service", "unknown")
            if svc not in per_service_stats:
                per_service_stats[svc] = {"normal": 0, "anomaly": 0}
            per_service_stats[svc]["anomaly" if decision == "ANOMALY" else "normal"] += 1

            # Pretty print
            print(f"------ LOG {idx}/{total} ------")
            print(f"Service:       {svc}")
            print(f"Method:        {log_item.get('method')}")
            print(f"Decision:      {decision}")
            print(f"Anomaly Score: {score}")
            print(f"Threshold:     {threshold}")
            print(f"Response Time: {elapsed_ms:.2f} ms")
            print("------------------------------\n")

        except Exception as e:
            fail_count += 1
            print(f"[{idx}] ❌ Exception: {e}")

    # -------- SUMMARY --------
    print("\n=================== SUMMARY ===================")
    print(f"Total logs sent:        {total}")
    print(f"Successful responses:   {success_count}")
    print(f"Failed responses:       {fail_count}")
    print(f"NORMAL decisions:       {normal_count}")
    print(f"ANOMALY decisions:      {anomaly_count}")

    if total > 0:
        avg_resp_ms = total_response_ms / max(success_count, 1)
        print(f"Avg API response time:  {avg_resp_ms:.2f} ms")

    print("\n-- Per Service Breakdown --")
    for svc, stats in per_service_stats.items():
        print(f"{svc}: NORMAL={stats['normal']} | ANOMALY={stats['anomaly']}")

    print("=================================================\n")


if __name__ == "__main__":
    run_tests()
