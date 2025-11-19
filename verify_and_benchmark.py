#!/usr/bin/env python3
"""
System Verification and Benchmark Script
Verifies system capabilities and benchmarks performance
"""

import sys
import time
import os
import subprocess
import platform
from datetime import datetime

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_status(label, status, details=""):
    """Print status line"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {label:40s} {details}")

def check_python_version():
    """Check Python version"""
    print_header("Python Version Check")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    is_ok = version.major == 3 and version.minor >= 10
    print_status("Python Version", is_ok, version_str)
    return is_ok

def check_system_resources():
    """Check system resources"""
    print_header("System Resources")
    
    # CPU cores
    try:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        print_status("CPU Cores", True, f"{cpu_count} cores")
    except:
        print_status("CPU Cores", False, "Unable to detect")
    
    # RAM
    try:
        import psutil
        ram = psutil.virtual_memory()
        ram_gb = ram.total / (1024**3)
        ram_avail = ram.available / (1024**3)
        is_ok = ram_gb >= 4
        print_status("RAM", is_ok, f"{ram_gb:.1f} GB total, {ram_avail:.1f} GB available")
    except:
        print_status("RAM", False, "Unable to detect (install psutil)")
    
    # Disk space
    try:
        import shutil
        disk = shutil.disk_usage("/")
        disk_free_gb = disk.free / (1024**3)
        is_ok = disk_free_gb >= 1
        print_status("Disk Space", is_ok, f"{disk_free_gb:.1f} GB free")
    except:
        print_status("Disk Space", False, "Unable to detect")
    
    # GPU
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_info = result.stdout.strip()
            print_status("GPU (NVIDIA)", True, gpu_info)
        else:
            print_status("GPU (NVIDIA)", False, "Not detected")
    except:
        print_status("GPU (NVIDIA)", False, "Not available")

def check_dependencies():
    """Check required dependencies"""
    print_header("Dependency Check")
    
    dependencies = [
        ("numpy", "numpy"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("river", "river"),
        ("scikit-learn", "sklearn"),
        ("pydantic", "pydantic"),
    ]
    
    all_ok = True
    for display_name, import_name in dependencies:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            print_status(display_name, True, f"v{version}")
        except ImportError:
            print_status(display_name, False, "Not installed")
            all_ok = False
    
    return all_ok

def check_file_structure():
    """Check if all required files exist"""
    print_header("File Structure Check")
    
    required_files = [
        "config.py",
        "enhanced_anomaly_detector.py",
        "app_enhanced.py",
        "FilePersistence.py",
        "test_enhanced_system.py",
        "requirements_enhanced.txt",
    ]
    
    all_ok = True
    for filename in required_files:
        exists = os.path.exists(filename)
        size = os.path.getsize(filename) if exists else 0
        print_status(filename, exists, f"{size:,} bytes" if exists else "Missing")
        if not exists:
            all_ok = False
    
    return all_ok

def check_storage_configuration():
    """Check file-based storage configuration"""
    print_header("Storage Configuration Check")
    
    try:
        import config
        
        # Check if storage directory exists or can be created
        storage_dir = config.STORAGE_DIR
        
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
        
        # Check write permissions
        test_file = os.path.join(storage_dir, ".write_test")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        print_status("Storage Directory", True, f"{storage_dir}")
        print_status("Write Permissions", True, "OK")
        print_status("Storage Type", True, "File-based (No database required!)")
        return True
    
    except Exception as e:
        print_status("Storage Configuration", False, f"Failed: {str(e)[:50]}")
        return False

def benchmark_feature_extraction():
    """Benchmark feature extraction performance"""
    print_header("Feature Extraction Benchmark")
    
    try:
        from enhanced_anomaly_detector import EnhancedLogAnomalyDetector
        
        detector = EnhancedLogAnomalyDetector()
        
        sample_log = {
            "message": "User authentication failed: Invalid password attempt",
            "service": "auth-service",
            "method": "authenticate",
            "endpoint": "/api/v1/auth/login",
            "response_time": 0.15,
            "level": "ERROR",
            "correlationId": "test-123",
            "status_code": "401"
        }
        
        # Warm-up
        for _ in range(10):
            detector.extract_features(sample_log)
        
        # Benchmark
        iterations = 1000
        start_time = time.time()
        
        for _ in range(iterations):
            features = detector.extract_features(sample_log)
        
        elapsed = time.time() - start_time
        per_extraction = (elapsed / iterations) * 1000  # ms
        throughput = iterations / elapsed
        
        print(f"   Iterations: {iterations}")
        print(f"   Total Time: {elapsed:.3f}s")
        print(f"   Per Extraction: {per_extraction:.3f}ms")
        print(f"   Throughput: {throughput:.1f} extractions/sec")
        print(f"   Features Generated: {len(features)}")
        
        is_ok = per_extraction < 5.0  # Should be under 5ms
        print_status("Performance", is_ok, f"{per_extraction:.2f}ms per extraction")
        
        return is_ok
    
    except Exception as e:
        print_status("Benchmark", False, f"Error: {str(e)}")
        return False

def benchmark_model_inference():
    """Benchmark model inference performance"""
    print_header("Model Inference Benchmark")
    
    try:
        from enhanced_anomaly_detector import EnhancedLogAnomalyDetector
        
        detector = EnhancedLogAnomalyDetector()
        
        sample_logs = [
            {
                "message": f"Log message {i}",
                "service": "test-service",
                "method": "testMethod",
                "endpoint": "/api/test",
                "response_time": 0.1 + (i % 10) * 0.1,
                "level": "INFO",
                "correlationId": f"test-{i}",
                "status_code": "200"
            }
            for i in range(100)
        ]
        
        # Warm-up
        for log in sample_logs[:10]:
            detector.process_log(log)
        
        # Benchmark
        start_time = time.time()
        
        for log in sample_logs:
            decision, score = detector.process_log(log)
        
        elapsed = time.time() - start_time
        per_log = (elapsed / len(sample_logs)) * 1000  # ms
        throughput = len(sample_logs) / elapsed
        
        print(f"   Logs Processed: {len(sample_logs)}")
        print(f"   Total Time: {elapsed:.3f}s")
        print(f"   Per Log: {per_log:.3f}ms")
        print(f"   Throughput: {throughput:.1f} logs/sec")
        
        is_ok = per_log < 10.0  # Should be under 10ms per log
        print_status("Performance", is_ok, f"{per_log:.2f}ms per log")
        
        # Get statistics
        stats = detector.get_statistics()
        print("\n   Detector Statistics:")
        for key, value in stats.items():
            print(f"      {key}: {value}")
        
        return is_ok
    
    except Exception as e:
        print_status("Benchmark", False, f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_anomaly_detection_accuracy():
    """Test anomaly detection with known cases"""
    print_header("Anomaly Detection Accuracy Test")
    
    try:
        from enhanced_anomaly_detector import EnhancedLogAnomalyDetector
        
        detector = EnhancedLogAnomalyDetector()
        
        # Normal logs (should NOT be anomalies)
        normal_logs = [
            {
                "message": "User logged in successfully",
                "service": "auth-service",
                "method": "login",
                "endpoint": "/api/v1/auth/login",
                "response_time": 0.08,
                "level": "INFO",
                "correlationId": "norm-1",
                "status_code": "200"
            },
            {
                "message": "Data retrieved successfully",
                "service": "data-service",
                "method": "getData",
                "endpoint": "/api/v1/data",
                "response_time": 0.12,
                "level": "INFO",
                "correlationId": "norm-2",
                "status_code": "200"
            },
        ]
        
        # Anomalous logs (should BE anomalies)
        anomaly_logs = [
            {
                "message": "CRITICAL ERROR: Database connection timeout. Exception in DatabasePool.connect() after 30 seconds",
                "service": "database-service",
                "method": "connect",
                "endpoint": "/internal/db/connect",
                "response_time": 30.5,
                "level": "CRITICAL",
                "correlationId": "anom-1",
                "status_code": "500"
            },
            {
                "message": "OutOfMemoryError: Java heap space exhausted. Stack trace: at MemoryManager.allocate()",
                "service": "payment-service",
                "method": "processPayment",
                "endpoint": "/api/v1/payments",
                "response_time": 15.0,
                "level": "FATAL",
                "correlationId": "anom-2",
                "status_code": "500"
            },
        ]
        
        # Test normal logs
        normal_correct = 0
        print("\n   Testing Normal Logs:")
        for log in normal_logs:
            decision, score = detector.process_log(log)
            is_correct = decision == "NORMAL"
            normal_correct += is_correct
            icon = "✅" if is_correct else "❌"
            print(f"      {icon} Score: {score:.3f}, Decision: {decision}")
        
        # Test anomalous logs
        anomaly_correct = 0
        print("\n   Testing Anomalous Logs:")
        for log in anomaly_logs:
            decision, score = detector.process_log(log)
            is_correct = decision == "ANOMALY"
            anomaly_correct += is_correct
            icon = "✅" if is_correct else "❌"
            print(f"      {icon} Score: {score:.3f}, Decision: {decision}")
        
        total_correct = normal_correct + anomaly_correct
        total_tests = len(normal_logs) + len(anomaly_logs)
        accuracy = (total_correct / total_tests) * 100
        
        print(f"\n   Accuracy: {accuracy:.1f}% ({total_correct}/{total_tests})")
        
        is_ok = accuracy >= 50  # At least 50% accuracy
        print_status("Detection Accuracy", is_ok, f"{accuracy:.1f}%")
        
        return is_ok
    
    except Exception as e:
        print_status("Accuracy Test", False, f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def generate_report(results):
    """Generate final report"""
    print_header("VERIFICATION REPORT")
    
    print(f"\n📊 Overall Results:")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Platform: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version.split()[0]}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n   Tests Passed: {passed}/{total} ({percentage:.1f}%)")
    
    print("\n📋 Test Results:")
    for test_name, result in results.items():
        icon = "✅" if result else "❌"
        print(f"      {icon} {test_name}")
    
    if passed == total:
        print("\n🎉 System verification PASSED! Ready for production.")
        print("\n   Next steps:")
        print("   1. Start the API: python app_enhanced.py")
        print("   2. Run tests: python test_enhanced_system.py")
        print("   3. Review QUICK_START_GUIDE.md")
        return 0
    else:
        print("\n⚠️  System verification INCOMPLETE!")
        print("\n   Issues found:")
        for test_name, result in results.items():
            if not result:
                print(f"      ❌ {test_name}")
        print("\n   Actions:")
        print("   1. Review error messages above")
        print("   2. Install missing dependencies: pip install -r requirements_enhanced.txt")
        print("   3. Check database configuration in config.py")
        print("   4. Review QUICK_START_GUIDE.md for troubleshooting")
        return 1

def main():
    """Main verification function"""
    print("\n" + "="*80)
    print("  ENHANCED LOG ANOMALY DETECTION SYSTEM")
    print("  System Verification & Benchmark Tool")
    print("="*80)
    print(f"\n  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run all checks
    results["Python Version"] = check_python_version()
    
    check_system_resources()  # Informational only
    
    results["Dependencies"] = check_dependencies()
    results["File Structure"] = check_file_structure()
    results["Storage Configuration"] = check_storage_configuration()
    
    if results["Dependencies"] and results["File Structure"]:
        results["Feature Extraction"] = benchmark_feature_extraction()
        results["Model Inference"] = benchmark_model_inference()
        results["Detection Accuracy"] = test_anomaly_detection_accuracy()
    else:
        print("\n⚠️  Skipping benchmarks due to missing dependencies or files")
        results["Feature Extraction"] = False
        results["Model Inference"] = False
        results["Detection Accuracy"] = False
    
    # Generate final report
    exit_code = generate_report(results)
    
    print(f"\n  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    return exit_code

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Verification cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

