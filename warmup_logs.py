"""
Warm-up script for Log Anomaly Detection service.

Generates and sends normal log entries to warm up the EnhancedLogAnomalyDetector model.
"""
import requests
import uuid
import random
from datetime import datetime, timedelta
import argparse
import time

# Configuration
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_ENDPOINT = "/v1/ai/logs/ingest"
DEFAULT_WARMUP_COUNT = 500  # number of logs to send by default


def generate_normal_log(service: str, method: str, endpoint: str) -> dict:
    """
    Generate a synthetic NORMAL log entry for warm-up.
    No errors, reasonable response times, 2xx codes.
    """
    now = datetime.utcnow()
    correlation_id = str(uuid.uuid4())

    # Slightly random response time in a normal range
    response_time = round(random.uniform(0.05, 0.4), 3)

    # Choose a 2xx status code (as string to match schema)
    status_code = str(random.choice([200, 201, 204]))

    message_templates = [
        "Request completed successfully.",
        "User action processed successfully.",
        "Operation finished without errors.",
        "Service call executed successfully.",
    ]
    message = random.choice(message_templates)

    log = {
        "message": message,
        "service": service,
        "method": method,
        "endpoint": endpoint,
        "response_time": response_time,
        "level": "INFO",
        "correlationId": correlation_id,
        "status_code": status_code,
        "timestamp": now.isoformat() + "Z",
    }
    return log


def send_log(base_url: str, api_path: str, log: dict, timeout: float = 3.0) -> bool:
    """
    Send a single log to the ingest endpoint.
    Returns True on success (2xx), False otherwise.
    """
    url = base_url.rstrip("/") + api_path
    try:
        resp = requests.post(url, json=log, timeout=timeout)
        return resp.status_code // 100 == 2
    except Exception as e:
        print(f"[WARN] Failed to send log: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Warm-up script for Log Anomaly Detector."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL of the API (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"Ingest endpoint path (default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_WARMUP_COUNT,
        help=f"Number of warm-up logs to send (default: {DEFAULT_WARMUP_COUNT})",
    )
    parser.add_argument(
        "--service",
        default="auth-service",
        help="Service name to simulate (default: auth-service)",
    )
    parser.add_argument(
        "--method",
        default="login",
        help="Method / operation name (default: login)",
    )
    parser.add_argument(
        "--endpoint-path",
        default="/api/v1/auth/login",
        help="Logical application endpoint (default: /api/v1/auth/login)",
    )

    args = parser.parse_args()

    success = 0
    fail = 0

    print(
        f"[INFO] Starting warm-up: sending {args.count} normal logs "
        f"to {args.base_url}{args.endpoint}"
    )

    start = time.time()

    for i in range(args.count):
        log = generate_normal_log(
            service=args.service,
            method=args.method,
            endpoint=args.endpoint_path,
        )
        ok = send_log(args.base_url, args.endpoint, log)
        if ok:
            success += 1
        else:
            fail += 1

        if (i + 1) % 50 == 0 or (i + 1) == args.count:
            print(
                f"[PROGRESS] Sent {i+1}/{args.count} | "
                f"Success: {success} | Fail: {fail}"
            )

    duration = time.time() - start
    print(
        f"[DONE] Warm-up completed in {duration:.2f}s | "
        f"Total: {args.count} | Success: {success} | Fail: {fail}"
    )


if __name__ == "__main__":
    main()

