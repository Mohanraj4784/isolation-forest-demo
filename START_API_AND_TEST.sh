#!/bin/bash
# Script to start API and run tests

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Starting Enhanced Log Anomaly Detection System               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if API is already running
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✅ API is already running!"
    echo ""
    read -p "Do you want to run tests now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python test_enhanced_system.py
    fi
    exit 0
fi

echo "📋 Starting API server in background..."
echo ""

# Start API in background
nohup python app_enhanced.py > api_server.log 2>&1 &
API_PID=$!

echo "   API PID: $API_PID"
echo "   Log file: api_server.log"
echo ""

# Wait for API to start
echo "⏳ Waiting for API to start..."
MAX_WAIT=30
COUNTER=0

while [ $COUNTER -lt $MAX_WAIT ]; do
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo ""
        echo "✅ API server is ready!"
        echo ""
        break
    fi
    
    echo -n "."
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -eq $MAX_WAIT ]; then
    echo ""
    echo "❌ API failed to start within ${MAX_WAIT} seconds"
    echo ""
    echo "Check the log file for errors:"
    echo "   tail -f api_server.log"
    exit 1
fi

# Run tests
echo "🧪 Running tests..."
echo ""
python test_enhanced_system.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "API server is still running in background (PID: $API_PID)"
echo ""
echo "Useful commands:"
echo "  View logs:        tail -f api_server.log"
echo "  Stop API:         kill $API_PID"
echo "  Check status:     curl http://127.0.0.1:8000/health"
echo "  View stats:       curl http://127.0.0.1:8000/v1/ai/stats"
echo ""
echo "To stop the API server, run:"
echo "  kill $API_PID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
