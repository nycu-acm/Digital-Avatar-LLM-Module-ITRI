# Model Warmup Server

A standalone service that automatically keeps the RAG + LLM system models warm for optimal performance by running periodic warmup operations.

## Overview

The Model Warmup Server is designed to:
- **Prevent cold starts**: Keep embedding and LLM models loaded in memory
- **Reduce latency**: Ensure first requests are fast by maintaining model readiness
- **Monitor health**: Continuously check API service health
- **Provide statistics**: Track warmup success/failure rates and timing

## Files

- `model_warmup_server.py` - Main warmup server script
- `start_warmup_server.sh` - Bash startup script
- `model-warmup.service` - Systemd service file for production
- `README_warmup_server.md` - This documentation

## Quick Start

### Manual Execution

```bash
# Basic usage (default: every 10 minutes)
cd /mnt/HDD4/thanglq/he110/Demo_GitSpace/API
python3 model_warmup_server.py

# Custom interval (every 5 minutes)
python3 model_warmup_server.py --interval 5

# Custom API URL and interval
python3 model_warmup_server.py --api-url http://localhost:5003 --interval 15

# Test mode (single warmup and exit)
python3 model_warmup_server.py --test
```

### Using Startup Script

```bash
# Default settings
./start_warmup_server.sh

# Custom configuration
./start_warmup_server.sh --interval 5 --api-url http://localhost:5003

# Test warmup
./start_warmup_server.sh --test

# Help
./start_warmup_server.sh --help
```

## Production Deployment

### Install as Systemd Service

```bash
# Copy service file to systemd directory
sudo cp model-warmup.service /etc/systemd/system/

# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable model-warmup

# Start the service
sudo systemctl start model-warmup

# Check status
sudo systemctl status model-warmup

# View logs
sudo journalctl -u model-warmup -f
```

### Service Management Commands

```bash
# Start service
sudo systemctl start model-warmup

# Stop service
sudo systemctl stop model-warmup

# Restart service
sudo systemctl restart model-warmup

# Check status
sudo systemctl status model-warmup

# View logs (follow)
sudo journalctl -u model-warmup -f

# View recent logs
sudo journalctl -u model-warmup --since "1 hour ago"

# Disable service
sudo systemctl disable model-warmup
```

## Configuration Options

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--api-url` | `http://localhost:5002` | RAG + LLM API service URL |
| `--interval` | `10` | Warmup interval in minutes |
| `--test` | - | Run single test warmup and exit |

### Environment Variables

You can also configure via environment variables:
```bash
export WARMUP_API_URL="http://localhost:5002"
export WARMUP_INTERVAL="10"
```

### Systemd Service Configuration

Edit the service file to customize:
```ini
# Change API URL
ExecStart=/usr/bin/python3 ... --api-url http://your-api-url

# Change interval
ExecStart=/usr/bin/python3 ... --interval 5

# Change user/group
User=your-user
Group=your-group

# Adjust resource limits
MemoryLimit=1G
CPUQuota=100%
```

## Monitoring

### Real-time Statistics

The server displays statistics every warmup cycle:
```
📊 Warmup Server Statistics:
  Uptime: 2:15:30
  Total Warmups: 13
  Successful: 12
  Failed: 1
  Last Warmup: 2024-12-17 14:30:15
  Next Warmup: 2024-12-17 14:40:15
```

### Log Output

The server provides colored console output:
- 🔥 **Blue**: Warmup operations
- ✅ **Green**: Success messages
- ❌ **Red**: Error messages
- ⚠️ **Yellow**: Warning messages
- 📊 **Blue**: Statistics

### Health Monitoring

The server continuously monitors:
- API service health status
- Model warmup success/failure rates
- Connection stability
- Response times

## Troubleshooting

### Common Issues

1. **Service not healthy**
   ```
   ❌ Service health check failed - skipping warmup
   ```
   - Ensure RAG + LLM API service is running on the specified URL
   - Check if the API service is accessible

2. **Connection refused**
   ```
   ❌ Warmup error: Connection refused
   ```
   - Verify API URL is correct
   - Check if API service is running
   - Ensure firewall allows connections

3. **Permission denied (systemd)**
   ```
   ❌ Permission denied
   ```
   - Check user/group permissions in service file
   - Ensure service user has access to Python and script files

### Debug Steps

1. **Test API connectivity**
   ```bash
   curl http://localhost:5002/health
   ```

2. **Run test warmup**
   ```bash
   python3 model_warmup_server.py --test
   ```

3. **Check systemd logs**
   ```bash
   sudo journalctl -u model-warmup --since "10 minutes ago"
   ```

4. **Verify dependencies**
   ```bash
   python3 -c "import requests, json, time, threading, signal"
   python3 -c "from client_utils import warmup_models, check_service_health"
   ```

## Performance Benefits

### Before Warmup Server
- First request: 2-5 seconds (cold start)
- Model loading delay
- Inconsistent response times

### After Warmup Server
- First request: 200-500ms (warm start)
- Models always ready
- Consistent low latency

### Resource Usage
- Memory: ~50-100MB
- CPU: <5% average, peaks during warmup
- Network: Minimal (periodic health checks)

## Integration

### With Docker
```dockerfile
# Add to your Dockerfile
COPY model_warmup_server.py /app/
COPY client_utils.py /app/
RUN chmod +x /app/model_warmup_server.py
CMD ["python3", "/app/model_warmup_server.py"]
```

### With Docker Compose
```yaml
version: '3.8'
services:
  warmup-server:
    build: .
    command: python3 model_warmup_server.py --interval 10
    environment:
      - WARMUP_API_URL=http://rag-api:5002
    depends_on:
      - rag-api
    restart: unless-stopped
```

## Advanced Configuration

### Custom Warmup Logic

You can extend the server by modifying the `_perform_warmup` method to:
- Add custom health checks
- Implement more sophisticated warming strategies
- Add metrics collection
- Integrate with monitoring systems

### Scaling Considerations

For high-traffic deployments:
- Reduce interval (e.g., 5 minutes)
- Monitor memory usage
- Consider multiple warmup servers for redundancy
- Implement load balancing between API instances

## Support

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify all dependencies are installed
3. Test connectivity manually
4. Review configuration settings

For additional help, check the main project documentation or create an issue in the project repository.
