# 📱 Mobile Access Guide - Abby Unleashed Core

Use Abby from your phone with all processing happening on your PC!

## Quick Setup

### Step 1: Start Server on PC

```bash
# On your PC/laptop
cd Abby-Unleashed-Core

# Start the web API server
python api_server.py

# Or with Docker
docker-compose up
```

You'll see:
```
Starting Abby Unleashed API server on 0.0.0.0:8080
Access from your phone: http://<your-pc-ip>:8080
```

### Step 2: Find Your PC's IP Address

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., `192.168.1.100`)

**Mac/Linux:**
```bash
ifconfig | grep "inet "
# or
ip addr show
```
Look for your local IP (e.g., `192.168.1.100`)

### Step 3: Connect from Phone

1. **Ensure phone and PC are on same WiFi network**
2. Open browser on your phone
3. Navigate to: `http://YOUR-PC-IP:8080`
   - Example: `http://192.168.1.100:8080`
4. Bookmark the page for easy access!

## Features

✅ **Full Functionality**
- Execute any task Abby can handle
- Real-time progress updates
- All processing on your PC
- Secure local network only

✅ **Mobile Optimized**
- Touch-friendly interface
- Responsive design
- Works offline (once loaded)
- Low bandwidth usage

✅ **Data on PC**
- Files downloaded to PC
- Memory stored on PC
- No data on phone
- Privacy maintained

## Network Setup

### Same WiFi (Easiest)

Both devices on same network:
```
Phone <--WiFi--> Router <--WiFi--> PC
       192.168.1.x        192.168.1.x
```

### Port Forwarding (Advanced)

Access from outside your home:

1. Router settings → Port Forwarding
2. Forward external port 8080 → PC IP port 8080
3. Find public IP: https://whatismyipaddress.com
4. Access: `http://YOUR-PUBLIC-IP:8080`

⚠️ **Security Warning**: Only use with strong authentication!

### VPN (Most Secure)

Use Tailscale, WireGuard, or similar:
```bash
# Install Tailscale on both devices
# Access via Tailscale IP (100.x.x.x)
```

## Docker Setup

### docker-compose.yml includes web server:

```bash
# Start everything
docker-compose up -d

# Server accessible on port 8080
# Mobile UI at http://PC-IP:8080
```

### Expose to local network:

```yaml
# docker-compose.yml
services:
  abby:
    ports:
      - "0.0.0.0:8080:8080"  # Already configured!
```

## API Endpoints

The mobile app uses these REST APIs:

### Health Check
```bash
GET /api/health
```

### Execute Task
```bash
POST /api/task
Content-Type: application/json

{
  "task": "Your task description",
  "context": {},
  "use_orchestrator": true
}
```

### Get Statistics
```bash
GET /api/stats
```

### List Models
```bash
GET /api/models
```

## Troubleshooting

### Can't Connect from Phone

1. **Check firewall on PC:**
   ```bash
   # Linux
   sudo ufw allow 8080
   
   # Windows
   # Windows Defender → Allow app through firewall → Port 8080
   ```

2. **Verify server is running:**
   ```bash
   # On PC, should see "Running on http://0.0.0.0:8080"
   curl http://localhost:8080/api/health
   ```

3. **Test connectivity:**
   ```bash
   # On phone browser, try PC IP first
   ping YOUR-PC-IP
   ```

### Slow Response

- Check PC performance (CPU, RAM)
- Ensure Ollama model is loaded
- Try smaller model (mistral vs qwen2.5)
- Monitor with: `GET /api/stats`

### Connection Drops

- Enable WiFi sleep settings on phone
- Keep screen on while using
- Use "Add to Home Screen" for better experience

### Server Won't Start

```bash
# Check if port is in use
netstat -an | grep 8080
lsof -i :8080

# Use different port
python api_server.py --port 8081
```

## Security Best Practices

1. **Local Network Only**
   - Default configuration is secure
   - Only accessible on your WiFi

2. **Add Authentication (Optional)**
   ```python
   # In api_server.py, add:
   from flask_httpauth import HTTPBasicAuth
   auth = HTTPBasicAuth()
   
   @auth.verify_password
   def verify(username, password):
       return username == 'your_user' and password == 'your_pass'
   
   @app.route('/api/task', methods=['POST'])
   @auth.login_required
   def execute_task():
       # ... rest of code
   ```

3. **HTTPS (Advanced)**
   ```bash
   # Generate self-signed certificate
   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   
   # Run with SSL
   app.run(host='0.0.0.0', port=8080, ssl_context=('cert.pem', 'key.pem'))
   ```

4. **Firewall Rules**
   ```bash
   # Only allow from phone IP
   sudo ufw allow from 192.168.1.50 to any port 8080
   ```

## Advanced Usage

### Create PWA (Progressive Web App)

Add to your phone's home screen:
- iOS: Safari → Share → Add to Home Screen
- Android: Chrome → Menu → Add to Home Screen

### Use with Shortcuts

Create Siri/Google Assistant shortcuts:
```
URL: http://YOUR-PC-IP:8080
```

### Background Server

Keep running on PC startup:

**Linux (systemd):**
```bash
sudo cat > /etc/systemd/system/abby-api.service << EOF
[Unit]
Description=Abby Unleashed API Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Abby-Unleashed-Core
ExecStart=/usr/bin/python3 api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable abby-api
sudo systemctl start abby-api
```

**Windows (Task Scheduler):**
1. Task Scheduler → Create Task
2. Trigger: At startup
3. Action: Start program → `python.exe api_server.py`
4. Settings: Run whether user logged in or not

## Examples

### From Phone Browser

1. Navigate to `http://192.168.1.100:8080`
2. Type: "Create a Python script to download a YouTube video"
3. Script is created and saved on your PC!
4. Type: "Explain how the script works"
5. Get detailed explanation

### From API Client

```javascript
// Use in your own app
const response = await fetch('http://192.168.1.100:8080/api/task', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    task: 'Summarize this article: ...',
    use_orchestrator: true
  })
});

const result = await response.json();
console.log(result.output);
```

## Performance Tips

1. **Pre-load models on PC:**
   ```bash
   ollama pull qwen2.5:latest
   ```

2. **Adjust PC power settings:**
   - Prevent sleep when API running
   - Keep Ollama in memory

3. **Monitor resources:**
   ```bash
   # Check API server
   curl http://localhost:8080/api/health
   
   # Check Ollama
   curl http://localhost:11434/api/tags
   ```

4. **Use smaller models for mobile:**
   - `mistral:latest` - Fast, lightweight
   - `qwen2.5:latest` - Balanced
   - `deepseek-r1:latest` - Slow but high quality

## Comparison: Mobile vs PC

| Feature | Mobile (Phone) | PC (Server) |
|---------|---------------|-------------|
| Processing | ❌ None | ✅ All |
| Storage | ❌ None | ✅ All files saved here |
| Memory | ✅ UI only (~5MB) | ✅ Full (~GB) |
| Bandwidth | ✅ Low (text only) | ✅ Local network |
| Battery | ✅ Minimal impact | - |
| Performance | ⚡ Instant (PC does work) | Depends on PC specs |

---

**Ready to go mobile?** Start the server and connect! 📱✨

Need help? Check:
- [API Server Code](../api_server.py)
- [Mobile UI](../web/index.html)
- [Main README](../README.md)
