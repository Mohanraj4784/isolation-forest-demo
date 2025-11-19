# Testing Instructions

## ❌ **Error You're Seeing**

```
Connection refused [Errno 111]
```

**Cause:** The API server is not running!

---

## ✅ **Solution: 3 Options**

### **Option 1: Use the Helper Script (Easiest!)**

```bash
./START_API_AND_TEST.sh
```

This will:
1. Start the API server automatically
2. Wait for it to be ready
3. Run all tests
4. Keep server running in background

---

### **Option 2: Manual - Two Terminals**

#### Terminal 1: Start the API Server
```bash
cd /home/arvind/Documents/log-ai-model
python app_enhanced.py
```

**Keep this terminal open!** The API will be running here.

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Terminal 2: Run Tests
```bash
cd /home/arvind/Documents/log-ai-model
python test_enhanced_system.py
```

---

### **Option 3: Background Mode**

Start API in background:
```bash
cd /home/arvind/Documents/log-ai-model
nohup python app_enhanced.py > api_server.log 2>&1 &
```

Wait a few seconds, then run tests:
```bash
sleep 5
python test_enhanced_system.py
```

Stop the server when done:
```bash
pkill -f app_enhanced.py
```

---

## 🔍 **Check if API is Running**

```bash
# Test if API is responding
curl http://127.0.0.1:8000/health

# Should return:
# {"status":"healthy",...}
```

---

## 🛠️ **Troubleshooting**

### Problem: "Address already in use"

**Solution:** Port 8000 is already taken
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it (if it's your old API)
kill <PID>

# Or use a different port
python app_enhanced.py --port 8001
# Then update test script to use 8001
```

### Problem: "ModuleNotFoundError"

**Solution:** Missing dependencies
```bash
pip install -r requirements_enhanced.txt
```

### Problem: API starts but crashes immediately

**Solution:** Check logs
```bash
# If using background mode
tail -f api_server.log

# If using terminal, look at the error messages
```

---

## 📊 **Expected Test Results**

When tests run successfully:

```
================================================================================
  TEST SUMMARY
================================================================================

✅ PASSED: Health Check
✅ PASSED: Configuration
✅ PASSED: Anomaly Detection
✅ PASSED: Statistics
✅ PASSED: Service Metrics
✅ PASSED: Threshold Adjustment

6/6 tests passed (100.0%)

🎉 All tests passed!
```

---

## 🚀 **Quick Start Command**

**Just run this:**
```bash
./START_API_AND_TEST.sh
```

It handles everything automatically!

---

## 📝 **After Testing**

### Stop the API Server

If you started in background:
```bash
# Find the process
ps aux | grep app_enhanced

# Kill it
kill <PID>

# Or kill all
pkill -f app_enhanced.py
```

If you started in terminal:
```bash
# Just press Ctrl+C in the terminal
```

---

## 💡 **Development Workflow**

### Recommended: Two Terminal Setup

**Terminal 1 (API Server):**
```bash
cd /home/arvind/Documents/log-ai-model
python app_enhanced.py
```
Leave this running during development.

**Terminal 2 (Testing/Commands):**
```bash
cd /home/arvind/Documents/log-ai-model

# Run tests
python test_enhanced_system.py

# Check health
curl http://127.0.0.1:8000/health

# View stats
curl http://127.0.0.1:8000/v1/ai/stats

# Send test log
curl -X POST http://127.0.0.1:8000/v1/ai/logs/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test log message",
    "service": "test-service",
    "method": "test",
    "endpoint": "/test",
    "response_time": 0.1,
    "level": "INFO",
    "correlationId": "test-123",
    "status_code": "200"
  }'
```

---

## 🎯 **Summary**

**The Error:** API server not running  
**The Fix:** Start `python app_enhanced.py` first  
**Easiest Way:** Run `./START_API_AND_TEST.sh`

**Then tests will pass!** ✅

