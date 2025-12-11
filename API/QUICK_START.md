# Quick Start Guide - Parallel Dynamic Tone Selection

## 🚀 Start Servers (Easy Way)

```bash
cd API
bash start_servers.sh
```

That's it! Both servers will start automatically.

## 🧪 Run Tests

```bash
cd API
python3 test_parallel_dynamic_tone.py
```

## 📋 What's Running?

After running `start_servers.sh`:

1. **Random User Description Server** (Port 5003)
   - Simulates VLM output
   - Returns random user descriptions
   - Health check: http://localhost:5003/health

2. **RAG LLM API Server** (Port 5002)
   - Main API with parallel processing
   - Fetches descriptions automatically
   - Health check: http://localhost:5002/health

## 🔧 Manual Start (If needed)

**Terminal 1:**
```bash
cd API
python3 random_user_description_server.py --port 5003
```

**Terminal 2:**
```bash
cd API
python3 rag_llm_api.py --auto-init --user-description-server http://localhost:5003
```

## 💻 Client Code Example

```python
import requests

# Simple query - user_description fetched automatically!
payload = {
    "text_user_msg": "What is ITRI?",
    "convert_tone": True
}

response = requests.post(
    "http://localhost:5002/api/rag-llm/query",
    json=payload,
    stream=True
)

for line in response.iter_lines(decode_unicode=True):
    if line == "END_FLAG":
        break
    print(line, end='', flush=True)
```

## 📊 What Happens Behind the Scenes?

```
Your Request
    ↓
Server does 2 things in PARALLEL:
    ├─→ Fetch user description from VLM server
    └─→ Generate QA response from RAG+LLM
    ↓
Both results combined
    ↓
Tone determined from description
    ↓
Response converted to appropriate tone
    ↓
Streaming response to you
```

## 🎯 Key Files

- `random_user_description_server.py` - VLM simulator
- `rag_llm_api.py` - Main API with parallel processing
- `start_servers.sh` - Start both servers
- `test_parallel_dynamic_tone.py` - Test the system

## 📚 More Information

- `README_parallel_architecture.md` - Detailed architecture
- `ARCHITECTURE_COMPARISON.md` - Before vs After comparison

## 🛑 Stop Servers

If you used `start_servers.sh`:
- Press `Ctrl+C` in the terminal

If you started manually:
- Press `Ctrl+C` in each terminal

## ❓ Troubleshooting

**Servers won't start?**
```bash
# Check if ports are in use
lsof -i :5002
lsof -i :5003

# Kill if needed
kill $(lsof -t -i:5002)
kill $(lsof -t -i:5003)
```

**Connection errors in tests?**
- Make sure both servers are running
- Check health endpoints:
  - http://localhost:5003/health
  - http://localhost:5002/health

## 🎉 Success Indicators

When everything is working, you'll see:
- ✅ Both servers start without errors
- ✅ Health checks return status: "healthy"
- ✅ Tests show parallel processing logs
- ✅ Responses have tone-specific markers (呢, 啊, 喔, etc.)

## 🔥 Next Steps

1. Try different questions in the test
2. Check the console logs to see parallel processing
3. Customize the description pool in `random_user_description_server.py`
4. Replace VLM simulator with real VLM when ready

Enjoy the faster, smarter tone selection! 🎊



