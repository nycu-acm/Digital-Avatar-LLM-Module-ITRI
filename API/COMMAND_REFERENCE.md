# Command Reference - Parallel Dynamic Tone Selection

## 🚀 Quick Start

```bash
# Start both servers (easiest way)
cd API && bash start_servers.sh

# Stop servers
# Press Ctrl+C in the terminal running start_servers.sh
```

## 🧪 Testing

```bash
# Test the parallel architecture
cd API && python3 test_parallel_dynamic_tone.py

# Test with hardcoded descriptions (original test)
cd API && python3 test_dynamic_tone_selection.py
```

## 🔧 Manual Server Control

### Start Servers Manually

```bash
# Terminal 1 - Start VLM simulator (port 5003)
cd API
python3 random_user_description_server.py --port 5003

# Terminal 2 - Start RAG API (port 5002)
cd API
python3 rag_llm_api.py --auto-init --user-description-server http://localhost:5003
```

### With Custom Configuration

```bash
# VLM simulator on custom port
python3 random_user_description_server.py --host 0.0.0.0 --port 6000 --debug

# RAG API with custom settings
python3 rag_llm_api.py \
    --host 0.0.0.0 \
    --port 6001 \
    --auto-init \
    --user-description-server http://localhost:6000 \
    --debug
```

## 🩺 Health Checks

```bash
# Check VLM simulator
curl http://localhost:5003/health

# Check RAG API
curl http://localhost:5002/health

# Both should return:
# {"status": "healthy", ...}
```

## 📊 Information Endpoints

```bash
# Get random user description
curl http://localhost:5003/api/get-user-description

# View all descriptions in pool
curl http://localhost:5003/api/get-user-description/pool

# Get RAG API session history
curl http://localhost:5002/api/rag-llm/sessions/test_session/history

# Delete session history
curl -X DELETE http://localhost:5002/api/rag-llm/sessions/test_session/history
```

## 💻 API Usage Examples

### Basic Query (Automatic Description Fetching)

```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "What is ITRI?",
    "convert_tone": true,
    "session_id": "user_123"
  }'
```

### Query with Manual Description (Backward Compatible)

```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "What is ITRI?",
    "user_description": "a young boy wearing glasses",
    "convert_tone": true,
    "session_id": "user_123"
  }'
```

### Standalone Tone Conversion (with Context)

```bash
curl -X POST http://localhost:5002/api/rag-llm/convert-tone \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ITRI is a research institute.",
    "tone": "child_friendly",
    "user_description": "a young boy wearing glasses",
    "user_msg": "What is ITRI?",
    "stream": true
  }'
```

### Initialize RAG System

```bash
curl -X POST http://localhost:5002/api/rag-llm/init
```

### Warmup Models

```bash
curl -X POST http://localhost:5002/api/rag-llm/warmup
```

### Close Session

```bash
curl -X POST http://localhost:5002/api/rag-llm/close \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user_123"
  }'
```

## 🐍 Python Client Examples

### Simple Client

```python
import requests

# Query with automatic description fetching
response = requests.post(
    "http://localhost:5002/api/rag-llm/query",
    json={
        "text_user_msg": "What is ITRI?",
        "convert_tone": True,
        "session_id": "user_123"
    },
    stream=True
)

for line in response.iter_lines(decode_unicode=True):
    if line == "END_FLAG":
        break
    if line and not line.startswith("ERROR:"):
        print(line, end='', flush=True)
```

### Full Example with Error Handling

```python
import requests
import time

def query_with_tone(question, session_id=None):
    """Query the API with automatic tone selection"""
    
    session_id = session_id or f"session_{int(time.time())}"
    
    payload = {
        "text_user_msg": question,
        "convert_tone": True,
        "session_id": session_id,
        "include_history": False
    }
    
    try:
        response = requests.post(
            "http://localhost:5002/api/rag-llm/query",
            json=payload,
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            result = ""
            for line in response.iter_lines(decode_unicode=True):
                if line == "END_FLAG":
                    break
                elif line.startswith("ERROR:"):
                    return None, line
                else:
                    result += line
            return result, None
        else:
            return None, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, str(e)

# Usage
result, error = query_with_tone("What is ITRI?")
if error:
    print(f"Error: {error}")
else:
    print(f"Response: {result}")
```

## 🛑 Stop & Cleanup

```bash
# If using start_servers.sh
# Just press Ctrl+C in that terminal

# Kill processes manually by port
kill $(lsof -t -i:5003)  # Kill VLM simulator
kill $(lsof -t -i:5002)  # Kill RAG API

# Kill all Python processes (careful!)
# pkill -f "python.*rag_llm_api"
# pkill -f "python.*random_user_description"
```

## 📝 Logs & Debugging

```bash
# Run with debug mode
python3 random_user_description_server.py --debug
python3 rag_llm_api.py --auto-init --debug

# Watch logs in real-time (if using systemd)
# journalctl -u rag-api -f
# journalctl -u vlm-simulator -f

# Check if ports are in use
lsof -i :5003
lsof -i :5002
netstat -an | grep 5003
netstat -an | grep 5002
```

## 🔍 Troubleshooting Commands

```bash
# Check if Ollama is running (required for LLM)
curl http://localhost:11435/api/tags

# Check ChromaDB path
ls -la /path/to/chroma_db

# Check Python dependencies
pip list | grep -E "flask|requests|chromadb"

# Test network connectivity between services
curl http://localhost:5003/api/get-user-description
curl http://localhost:5002/health

# Check process status
ps aux | grep python
ps aux | grep rag_llm_api
ps aux | grep random_user_description
```

## 📦 Installation Commands

```bash
# Install required packages
pip install flask flask-cors requests chromadb

# Or use requirements.txt (if exists)
# pip install -r requirements.txt

# Make scripts executable
chmod +x API/*.py
chmod +x API/*.sh
```

## 🎯 Testing Commands

```bash
# Run all tests
cd API
python3 test_parallel_dynamic_tone.py
python3 test_dynamic_tone_selection.py

# Test specific endpoint
curl http://localhost:5002/health
curl http://localhost:5003/health

# Measure response time
time curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{"text_user_msg": "What is ITRI?", "convert_tone": true}'
```

## 📊 Monitoring Commands

```bash
# Watch server logs
tail -f /var/log/rag-api.log  # if logging to file
tail -f /var/log/vlm-simulator.log

# Monitor resource usage
top -p $(pgrep -f rag_llm_api)
htop -p $(pgrep -f rag_llm_api)

# Check memory usage
ps aux | grep rag_llm_api | awk '{print $6/1024 "MB"}'

# Monitor network connections
watch -n 1 'netstat -an | grep -E "5002|5003"'
```

## 🚢 Production Deployment Commands

```bash
# Using systemd (example)
sudo systemctl start vlm-simulator
sudo systemctl start rag-api
sudo systemctl status vlm-simulator
sudo systemctl status rag-api

# Using Docker (if containerized)
docker-compose up -d
docker-compose ps
docker-compose logs -f

# Using PM2 (Node.js process manager for Python)
pm2 start random_user_description_server.py --name vlm-simulator
pm2 start rag_llm_api.py --name rag-api -- --auto-init
pm2 status
pm2 logs
```

## 🔐 Security Commands

```bash
# Generate API key (example)
openssl rand -hex 32

# Test with authentication (if implemented)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5002/api/rag-llm/query

# Check SSL/TLS (production)
openssl s_client -connect your-domain.com:443
```

## 📈 Performance Testing

```bash
# Simple load test with curl
for i in {1..10}; do
  curl -X POST http://localhost:5002/api/rag-llm/query \
    -H "Content-Type: application/json" \
    -d '{"text_user_msg": "Test", "convert_tone": true}' &
done

# Using Apache Bench
ab -n 100 -c 10 -p query.json -T application/json \
  http://localhost:5002/api/rag-llm/query

# Using wrk (if installed)
wrk -t4 -c100 -d30s --timeout 60s \
  -s post.lua http://localhost:5002/api/rag-llm/query
```

## 🎓 Learning Commands

```bash
# View API structure
grep -n "def.*:" API/rag_llm_api.py

# View available routes
grep -n "@self.app.route" API/rag_llm_api.py

# Count lines of code
wc -l API/*.py

# View documentation
cat API/README_parallel_architecture.md | less
cat API/QUICK_START.md
```

## 📚 Documentation Commands

```bash
# View all documentation
ls -la API/*.md

# Quick reference
cat API/QUICK_START.md

# Full architecture
cat API/README_parallel_architecture.md

# Changes summary
cat API/CHANGES_SUMMARY.md

# What changed
cat API/README_WHAT_CHANGED.md
```

---

## 🎯 Most Common Commands

```bash
# 1. Start everything
bash API/start_servers.sh

# 2. Run tests
python3 API/test_parallel_dynamic_tone.py

# 3. Check health
curl http://localhost:5002/health
curl http://localhost:5003/health

# 4. Stop everything
# Press Ctrl+C in start_servers.sh terminal
```

**That's it! You're ready to go! 🚀**



