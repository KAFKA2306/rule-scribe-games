# Development Environment Troubleshooting Guide

## Issue: Intermittent Frontend-API Connection Failures

When running `task dev`, the frontend (http://localhost:5173) cannot reliably connect to the backend API (http://localhost:8000). This guide helps diagnose and resolve the problem.

---

## Quick Diagnosis Checklist

### Step 1: Verify Servers Are Running

```bash
# Check if ports are in use
lsof -i :8000  # FastAPI backend
lsof -i :5173  # Vite frontend

# If ports are stuck, kill them:
task kill
```

If the output shows process info, both servers are running. If empty, at least one server failed to start.

### Step 2: Verify CORS and Proxy Are Configured

```bash
# Test backend health endpoint
curl http://localhost:8000/health
# Expected output: {"status":"ok"}

# Test proxy through frontend
curl http://localhost:5173/api/health
# Expected output: {"status":"ok"}
```

### Step 3: Reproduce the Issue

1. Run: `task dev`
2. Wait for both servers to report "ready"
3. In a new terminal, test immediately:
   ```bash
   curl -v http://localhost:5173/api/games
   ```
4. Record the HTTP status code and any error messages

---

## Root Cause Analysis

### Cause A: Vite Proxy Initialization Timing (Most Common for Intermittent Issues)

**Symptoms:**
- First request after `task dev` finishes fails with `ERR_CONNECTION_REFUSED`
- Reloading the page (after a few seconds) succeeds
- Consistently fails on first attempt, works on second

**Explanation:**
The Vite development server initializes its proxy configuration, but the FastAPI backend may not be fully bound to port 8000 at the exact moment the first request arrives.

**Solution:**

Option 1 - Add a client-side health check with retry logic:

```javascript
// frontend/src/lib/healthCheck.js
export const waitForBackend = async (maxRetries = 10, delayMs = 500) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = await fetch('/api/health')
      if (res.ok) return true
    } catch (e) {
      await new Promise(resolve => setTimeout(resolve, delayMs))
    }
  }
  throw new Error('Backend not reachable after retries')
}
```

Use in your main App component:

```javascript
import { useEffect, useState } from 'react'
import { waitForBackend } from './lib/healthCheck'

export default function App() {
  const [error, setError] = useState(null)

  useEffect(() => {
    waitForBackend()
      .catch(err => setError(`Backend connection failed: ${err.message}`))
  }, [])

  if (error) return <div>{error}</div>
  // ... rest of app
}
```

Option 2 - Stagger server startup in Taskfile:

```yaml
# Modify Taskfile.yml
dev:
  desc: Backend and frontend with staggered startup
  cmds:
    - task: dev:backend &
    - sleep 3  # Give backend time to initialize
    - task: dev:frontend
```

---

### Cause B: Port Already in Use (Most Common for Total Failures)

**Symptoms:**
- Backend fails to start with error: "Address already in use"
- `lsof -i :8000` shows another process using the port
- Sometimes the old server appears to start but doesn't accept connections

**Explanation:**
A previous instance of the FastAPI or Vite server didn't shut down cleanly, leaving the port in a TIME_WAIT state or still holding the port.

**Solution:**

```bash
# Force kill all processes using the ports
task kill

# Verify ports are now free
lsof -i :8000  # Should be empty
lsof -i :5173  # Should be empty

# Start fresh
task dev
```

If `task kill` doesn't work, manually:

```bash
# Find process IDs
ps aux | grep -E "(uvicorn|node|npm)" | grep -v grep

# Kill by PID
kill -9 <PID>

# Or use fuser
fuser -k 8000/tcp
fuser -k 5173/tcp
```

---

### Cause C: DNS/localhost Resolution Issues

**Symptoms:**
- Errors like `ERR_NAME_NOT_RESOLVED` or `getaddrinfo ENOTFOUND localhost`
- Works with `127.0.0.1` but not `localhost`
- Only occurs on certain machines or after network changes

**Explanation:**
The system cannot resolve `localhost` to `127.0.0.1`, typically a `/etc/hosts` misconfiguration.

**Solution:**

Check your `/etc/hosts` file:

```bash
cat /etc/hosts | grep localhost
# Should contain:
# 127.0.0.1  localhost
```

If missing, add it:

```bash
# On Linux/macOS
echo "127.0.0.1  localhost" | sudo tee -a /etc/hosts

# On Windows (PowerShell as Admin)
# Edit C:\Windows\System32\drivers\etc\hosts directly
```

**Special Case: WSL2 on Windows**

WSL2 can have networking quirks. Try:

```bash
# Get WSL IP
hostname -I
# Output might be: 172.31.x.x

# Then update vite.config.js:
# target: 'http://172.31.x.x:8000'  (instead of localhost)
```

Or use the WSL distribution name:

```bash
# In vite.config.js
target: process.env.VITE_API_URL || 'http://localhost:8000'

# Then in .env:
VITE_API_URL=http://127.0.0.1:8000
```

---

## Advanced Debugging

### Enable Verbose Proxy Logging in Vite

Edit `frontend/vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      logLevel: 'debug',  // Add this line
    },
  },
},
```

Then restart `task dev` and watch the terminal for detailed proxy logs.

### Monitor Network Requests in Browser

1. Open DevTools (F12)
2. Go to **Network** tab
3. Filter by **XHR/Fetch**
4. Reproduce the issue
5. Click on the failed request and inspect:
   - **Request URL**: Should be the API endpoint
   - **Method**: GET, POST, etc.
   - **Status**: Should show error code (e.g., 0, ERR_CONNECTION_REFUSED)
   - **Response Headers**: Should show CORS headers if successful
   - **Response Body**: May contain error message from backend

### Test Direct API Connection (Outside Browser)

```bash
# Test backend directly
curl -v http://localhost:8000/api/games

# Test through Vite proxy
curl -v http://localhost:5173/api/games

# Compare response times and status codes
```

### Check Vite Configuration

```bash
# Verify proxy is configured
grep -A 5 "proxy:" frontend/vite.config.js

# Should show:
# '/api': {
#   target: 'http://localhost:8000',
#   changeOrigin: true,
# }
```

---

## Permanent Fixes

### 1. Add Backend Startup Confirmation

Enhance `app/main.py` to log full readiness:

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    print("[BACKEND] FastAPI fully initialized and ready to serve requests")
    print("[BACKEND] Listening on http://0.0.0.0:8000")
    yield
    print("[BACKEND] Shutting down...")

app = FastAPI(lifespan=lifespan)
```

Then update Taskfile to wait for this message before starting frontend.

### 2. Add Client-Side Connection Retry

Modify `frontend/src/lib/api.js`:

```javascript
const API_RETRY_CONFIG = {
  maxRetries: 3,
  initialDelayMs: 200,
  backoffMultiplier: 2,
}

const handleResponse = async (res) => {
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}))
    throw new Error(errorBody.message || `API Error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

const fetchWithRetry = async (path, options = {}, retryCount = 0) => {
  try {
    const res = await fetch(path, options)
    return await handleResponse(res)
  } catch (error) {
    if (retryCount < API_RETRY_CONFIG.maxRetries) {
      const delay = API_RETRY_CONFIG.initialDelayMs * 
                    Math.pow(API_RETRY_CONFIG.backoffMultiplier, retryCount)
      await new Promise(resolve => setTimeout(resolve, delay))
      return fetchWithRetry(path, options, retryCount + 1)
    }
    throw error
  }
}

export const api = {
  get: (path) => fetchWithRetry(path),
  post: (path, body) => fetchWithRetry(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }),
  patch: (path, body) => fetchWithRetry(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }),
}
```

### 3. Diagnostic Script

Run this script to automatically diagnose the issue:

```bash
bash scripts/diagnose_dev_connection.sh
```

The script checks:
- Port availability (8000, 5173)
- Backend health endpoint
- Frontend server responsiveness
- Vite proxy configuration
- localhost DNS resolution

---

## Debugging Workflow

When experiencing connection issues, follow this sequence:

1. **Run diagnostic script** (30 seconds):
   ```bash
   bash scripts/diagnose_dev_connection.sh
   ```

2. **Check port availability** (10 seconds):
   ```bash
   lsof -i :8000
   lsof -i :5173
   ```

3. **Force kill and restart** (15 seconds):
   ```bash
   task kill
   task dev
   ```

4. **Test with curl** (10 seconds):
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:5173/api/health
   ```

5. **Check browser Network tab** (20 seconds):
   - Open DevTools
   - Reload page
   - Look for failed XHR/Fetch requests
   - Check status code and response

6. **If still failing, create GitHub issue**:
   - Use template at `.github/ISSUE_TEMPLATE/bug-api-connection.yml`
   - Include output from diagnostic script
   - Attach Network tab screenshot
   - Document exact reproduction steps

---

## Related Configuration Files

- **Vite Proxy**: `frontend/vite.config.js`
- **FastAPI CORS**: `app/main.py`
- **Backend Settings**: `app/core/settings.py`
- **Frontend API Lib**: `frontend/src/lib/api.js`
- **Task Commands**: `Taskfile.yml`

---

## Escalation Checklist

If the issue persists after all above steps:

- [ ] Ran diagnostic script and saved output
- [ ] Verified ports are not in use (task kill)
- [ ] Tested direct curl requests to both servers
- [ ] Checked /etc/hosts for localhost
- [ ] Tried on a different machine/network
- [ ] Checked if there are firewall/antivirus rules blocking localhost
- [ ] Checked Node and Python versions match project requirements
- [ ] Created GitHub issue with all diagnostic information

---

## Resources

- [Vite Proxy Configuration](https://vitejs.dev/config/server-options.html#server-proxy)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [Troubleshooting Node.js Port Issues](https://nodejs.org/en/docs/)
- [GitHub Issue Template](./.github/ISSUE_TEMPLATE/bug-api-connection.yml)
