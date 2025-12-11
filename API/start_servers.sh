#!/bin/bash
# Start both the random user description server and the main RAG LLM API server

echo "🚀 Starting servers for parallel dynamic tone selection..."
echo "=================================================="
echo ""

# Check if servers are already running
if lsof -Pi :5003 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 5003 already in use. Killing existing process..."
    kill $(lsof -t -i:5003) 2>/dev/null
    sleep 1
fi

if lsof -Pi :5002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 5002 already in use. Killing existing process..."
    kill $(lsof -t -i:5002) 2>/dev/null
    sleep 1
fi

echo ""
echo "📸 Starting Random User Description Server (Port 5003)..."
echo "--------------------------------------------------"
python3 random_user_description_server.py --port 5003 &
USER_DESC_PID=$!
sleep 2

echo ""
echo "🤖 Starting RAG LLM API Server (Port 5002)..."
echo "--------------------------------------------------"
python3 rag_llm_api.py --auto-init --port 5002 --user-description-server http://localhost:5003 &
RAG_API_PID=$!
sleep 3

echo ""
echo "=================================================="
echo "✅ Both servers started successfully!"
echo ""
echo "📸 User Description Server:"
echo "   - URL: http://localhost:5003"
echo "   - PID: $USER_DESC_PID"
echo "   - Health: http://localhost:5003/health"
echo ""
echo "🤖 RAG LLM API Server:"
echo "   - URL: http://localhost:5002"
echo "   - PID: $RAG_API_PID"
echo "   - Health: http://localhost:5002/health"
echo ""
echo "=================================================="
echo "💡 To stop both servers, press Ctrl+C"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $USER_DESC_PID 2>/dev/null
    kill $RAG_API_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Wait for both processes
wait



