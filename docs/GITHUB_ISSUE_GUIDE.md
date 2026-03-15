# GITHUB ISSUE CREATION & DOCUMENTATION GUIDE
# Frontend-API Connection Issues (Intermittent on Dev Server Restart)

================================================================================
## PART 1: GITHUB ISSUE TEMPLATE
================================================================================

Title: [Intermittent] Frontend cannot connect to API on dev server restart

Labels: 
  - bug
  - frontend
  - api
  - intermittent
  - dev-environment

Body:

### Description
Frontend fails to connect to the API (http://localhost:8000) when restarting dev servers (`task dev`). The issue occurs intermittently—sometimes the connection establishes immediately, other times requires manual intervention (browser refresh, server restart).

### Expected Behavior
After running `task dev`, both the FastAPI backend (port 8000) and Vite frontend (port 5173) should start cleanly. The frontend should proxy all `/api/*` requests to `http://localhost:8000` via Vite's proxy configuration, and API calls should succeed immediately.

### Actual Behavior
- Backend starts but frontend cannot reach API endpoints
- Network tab shows failed requests to `/api/*` with connection refused or timeout
- Manual page refresh sometimes resolves it
- Restarting both servers (using `task kill` then `task dev`) sometimes helps
- No clear error messages in browser console or server logs

### Reproduction Steps
1. Start fresh dev environment: `task setup`
2. Run: `task dev`
3. Navigate to http://localhost:5173
4. Attempt to load game list or interact with API endpoints
5. Observe: Intermittent failures, no consistent pattern

### Environment Information
- OS: [Linux/macOS/Windows WSL]
- Node version: [output of `node --version`]
- Python version: 3.11+
- Browser: [Chrome/Firefox/Safari]
- Task command used: `task dev`

### Logs / Screenshots
**Browser Network Tab:**
- Request URL: http://localhost:5173/api/games
- Status: [CORS error / Connection refused / Timeout]
- Response Headers: [paste relevant headers or "empty"]

**Backend Logs (FastAPI):**
[Paste any relevant startup or error logs from terminal running `task dev:backend`]

**Frontend Logs (Vite):**
[Paste any console errors or warnings from terminal running `task dev:frontend`]

### Related Configuration
- **Vite Proxy Config** (`frontend/vite.config.js`):
  ```
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  ```

- **FastAPI CORS Config** (`app/main.py`):
  ```
  app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
  )
  ```

### Possible Root Causes
- [ ] Vite proxy not initialized before frontend loads
- [ ] FastAPI backend not fully ready when frontend connects
- [ ] Port 8000 still in use from previous process (use `task kill` to verify)
- [ ] DNS/localhost resolution issue
- [ ] Timing race condition between server startup and initial client request

### Questions for Debugging
1. Does the issue occur if you start backend first, wait 3 seconds, then start frontend?
2. What's the exact error message in the Network tab?
3. Does reloading the browser immediately after `task dev` finishes resolve it?
4. Is there a pattern (e.g., always fails on first attempt, then works)?

================================================================================
## PART 2: DEBUGGING DOCUMENTATION FOR DEVELOPERS
================================================================================

# Development Environment Troubleshooting Guide

## Issue: Intermittent Frontend-API Connection Failures

### Quick Diagnosis Checklist

**Step 1: Verify Servers Are Running**
```bash
# Check if ports are in use
lsof -i :8000  # FastAPI backend
lsof -i :5173  # Vite frontend

# If ports are stuck, kill them:
task kill
```

**Step 2: Verify CORS and Proxy Are Configured**
```bash
# Test backend health
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Check Vite proxy (should NOT appear in browser network tab)
# Proxy requests are transparent—inspect the actual target
```

**Step 3: Reproduce the Issue**
1. Run: `task dev`
2. Wait for both servers to report "ready"
3. In new terminal, test immediately:
   ```bash
   curl -v http://localhost:5173/api/games
   ```
4. Record the exact response (status code, headers, body)

### Root Cause Analysis

#### Cause A: Vite Proxy Initialization Timing
**Symptoms:**
- First request fails with ERR_CONNECTION_REFUSED
- Subsequent requests (after page refresh) succeed

**Solution:**
- Ensure backend is fully ready before making requests
- Add a health-check utility in frontend:

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

Use in component initialization:
```javascript
useEffect(() => {
  waitForBackend().catch(err => setError(err.message))
}, [])
```

#### Cause B: Port Already in Use (Most Common)
**Symptoms:**
- Backend won't start
- Error: "Address already in use"
- Sometimes appears to start but doesn't accept connections

**Solution:**
```bash
# Force kill all node and python processes using the ports
task kill

# Verify ports are free
netstat -tlnp | grep -E "(8000|5173)"

# Start fresh
task dev
```

#### Cause C: DNS/localhost Resolution
**Symptoms:**
- Errors like "ERR_NAME_NOT_RESOLVED"
- Works with 127.0.0.1 but not localhost

**Solution:**
- Check /etc/hosts contains:
  ```
  127.0.0.1  localhost
  ```
- On WSL2, you may need to use the WSL IP instead of localhost:
  ```
  # Get WSL IP
  hostname -I
  # Then in vite.config.js, proxy target might need:
  target: 'http://172.x.x.x:8000'
  ```

### Advanced Debugging

#### Enable Verbose Logging in Vite
```javascript
// frontend/vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      logLevel: 'debug',  // Add this
    },
  },
},
```

#### Monitor Network Requests
1. Open DevTools → Network tab
2. Filter by XHR/Fetch
3. Reproduce the issue
4. Check:
   - Request URL and method
   - Status code (should be 200 or error status, not pending)
   - Response headers (CORS headers present?)
   - Response body (actual error message?)

#### Test Direct API Connection
```bash
# From your machine, NOT the browser
curl -v http://localhost:8000/api/games
curl -v http://127.0.0.1:8000/api/games

# Compare to proxied request
curl -v http://localhost:5173/api/games
```

### Permanent Fixes

#### 1. Add Startup Delay (Temporary)
If timing is the issue, add a startup sequence to Taskfile:

```yaml
dev:
  desc: Backend and frontend with staggered startup
  cmds:
    - task: dev:backend &
    - sleep 3  # Give backend time to initialize
    - task: dev:frontend
```

#### 2. Add Health Check Middleware
Enhance FastAPI to report full readiness:

```python
@app.on_event("startup")
async def startup_event():
    print("FastAPI fully initialized")
    # Verify DB connection, cache, etc.
```

#### 3. Configure Vite with Connection Retry
```javascript
// frontend/src/lib/api.js
const API_RETRY_CONFIG = {
  maxRetries: 3,
  delayMs: 500,
}

export const api = {
  get: async (path) => {
    let lastError
    for (let i = 0; i < API_RETRY_CONFIG.maxRetries; i++) {
      try {
        const res = await fetch(path)
        return handleResponse(res)
      } catch (e) {
        lastError = e
        if (i < API_RETRY_CONFIG.maxRetries - 1) {
          await new Promise(r => setTimeout(r, API_RETRY_CONFIG.delayMs))
        }
      }
    }
    throw lastError
  },
  // ... other methods
}
```

================================================================================
## PART 3: INVESTIGATION LOG TEMPLATE
================================================================================

# Investigation Log: Intermittent Frontend-API Connection

**Date Opened:** [YYYY-MM-DD]
**Status:** [Open / In Progress / Resolved]
**Severity:** [Low / Medium / High / Critical]

## Timeline

### Session 1 - [Date & Time]
**Observed Behavior:**
- [Describe what happened]
- Timestamp: [When exactly did it fail?]
- Frequency: [First time? Consistently? Every Nth attempt?]

**Environment:**
- OS: [details]
- Browser: [details]
- Ports: [output of `lsof -i :8000` and `lsof -i :5173`]

**Network Tab Screenshot:**
- [Attach or describe HTTP request/response]

**Server Logs:**
- Backend: [relevant logs]
- Frontend: [relevant logs]

**Attempted Fixes:**
- [ ] Ran `task kill` and restarted `task dev`
- [ ] Reloaded browser
- [ ] Checked if port 8000 is in use
- [ ] Other: [describe]

**Result:**
- [Did it work? What changed?]

---

### Session 2 - [Date & Time]
[Repeat above sections for each debugging session]

---

## Summary & Hypothesis

Based on sessions above, the most likely cause is:
- [ ] Timing issue (vite proxy before backend ready)
- [ ] Port conflict
- [ ] DNS/localhost resolution
- [ ] Other: [describe]

## Next Steps
1. [Action item 1]
2. [Action item 2]
3. [Testing plan]

================================================================================
## PART 4: AUTOMATED DIAGNOSTIC SCRIPT
================================================================================

Script location: `scripts/diagnose_dev_connection.sh`

```bash
#!/bin/bash
# Diagnostic script for frontend-API connection issues

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== RuleScribe Dev Connection Diagnostic ===${NC}\n"

# 1. Check ports
echo -e "${YELLOW}Step 1: Checking ports...${NC}"
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Port 8000 (FastAPI) is in use${NC}"
else
    echo -e "${RED}✗ Port 8000 (FastAPI) is NOT in use${NC}"
fi

if lsof -i :5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Port 5173 (Vite) is in use${NC}"
else
    echo -e "${RED}✗ Port 5173 (Vite) is NOT in use${NC}"
fi

# 2. Test backend health
echo -e "\n${YELLOW}Step 2: Testing backend health...${NC}"
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✓ Backend /health endpoint responds${NC}"
else
    echo -e "${RED}✗ Backend /health endpoint failed${NC}"
fi

# 3. Test frontend connectivity
echo -e "\n${YELLOW}Step 3: Testing frontend connectivity...${NC}"
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend server is responding${NC}"
else
    echo -e "${RED}✗ Frontend server is not responding${NC}"
fi

# 4. Test API proxying
echo -e "\n${YELLOW}Step 4: Testing API proxy through frontend...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:5173/api/health)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ API proxy working (status: 200)${NC}"
else
    echo -e "${RED}✗ API proxy failed (status: $HTTP_CODE)${NC}"
fi

# 5. Check localhost resolution
echo -e "\n${YELLOW}Step 5: Checking localhost resolution...${NC}"
if getent hosts localhost | grep -q "127.0.0.1"; then
    echo -e "${GREEN}✓ localhost resolves to 127.0.0.1${NC}"
else
    echo -e "${RED}✗ localhost resolution issue${NC}"
fi

# 6. Vite config check
echo -e "\n${YELLOW}Step 6: Checking Vite proxy config...${NC}"
if grep -q "target: 'http://localhost:8000'" frontend/vite.config.js; then
    echo -e "${GREEN}✓ Vite proxy target is configured${NC}"
else
    echo -e "${RED}✗ Vite proxy configuration issue${NC}"
fi

echo -e "\n${YELLOW}=== Diagnostic Complete ===${NC}"
echo -e "If issues remain, refer to: docs/GITHUB_ISSUE_GUIDE.md"
```

================================================================================
## PART 5: ISSUE TEMPLATE FOR GITHUB
================================================================================

File location: `.github/ISSUE_TEMPLATE/bug-api-connection.yml`

```yaml
name: API Connection Issue
description: Report problems connecting frontend to backend API
labels: ["bug", "api"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        Thank you for reporting this issue. Please provide as much detail as possible.

  - type: dropdown
    id: frequency
    attributes:
      label: Issue Frequency
      options:
        - First occurrence
        - Intermittent (sometimes happens)
        - Consistently reproducible
        - Only on specific conditions
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Description
      placeholder: Describe what happens when the connection fails
    validations:
      required: true

  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      placeholder: |
        1. Run `task dev`
        2. Navigate to...
        3. Observe...
    validations:
      required: true

  - type: textarea
    id: network-log
    attributes:
      label: Network Tab Error
      placeholder: |
        Status code:
        Response headers:
        Error message:
    validations:
      required: true

  - type: textarea
    id: server-logs
    attributes:
      label: Server Logs
      placeholder: Paste relevant backend/frontend logs
    validations:
      required: false

  - type: input
    id: node-version
    attributes:
      label: Node Version
      placeholder: "$(node --version)"

  - type: input
    id: python-version
    attributes:
      label: Python Version
      placeholder: "$(python --version)"

  - type: textarea
    id: env-info
    attributes:
      label: Environment Info
      placeholder: |
        OS: Linux/macOS/Windows
        Browser: Chrome/Firefox/Safari
        Proxy tool: Vite/nginx/other
```

================================================================================
## PART 6: QUICK REFERENCE CARD
================================================================================

# Quick Fix Cheat Sheet

**Most Common Fix (Try This First):**
```bash
task kill
task dev
```

**Port Already in Use:**
```bash
task kill
# or manually:
fuser -k 8000/tcp 5173/tcp
task dev
```

**Verify Both Servers Running:**
```bash
# Terminal 1:
lsof -i :8000

# Terminal 2:
lsof -i :5173

# Both should show process info, not empty
```

**Test Connection Without Browser:**
```bash
curl http://localhost:8000/health
curl http://localhost:5173/api/health
```

**Clear All Cache:**
```bash
task clean
task setup
task dev
```

**Detailed Debug (Add to Vite):**
Edit `frontend/vite.config.js`, set: `logLevel: 'debug'` in proxy config.

================================================================================
## SUMMARY: RECOMMENDED APPROACH
================================================================================

YES, you should create a GitHub issue for this intermittent connection problem.

### Why:
1. **Trackability**: Creates a permanent record and discussion thread
2. **Visibility**: Alerts other team members to the issue
3. **Resolution**: Allows collaborative debugging and solution testing
4. **Documentation**: Issue comments become searchable history for future occurrences

### Recommended Steps:

1. **Before Creating Issue:**
   - Document the EXACT reproduction steps
   - Capture browser Network tab screenshot
   - Record backend and frontend startup logs
   - Run the diagnostic script above to gather environment info

2. **When Creating Issue:**
   - Use the template in PART 1 above
   - Be specific about frequency (first time only? every restart?)
   - Include environment details (OS, Node version, Python version)
   - Mention what you've already tried (task kill, browser refresh, etc.)

3. **After Creating Issue:**
   - Link it to your debugging notes
   - Add the `intermittent` label if available
   - Check box for issues that need environment info collected
   - Monitor comments for reproduction confirmation from others

4. **Documentation Steps:**
   - Create or append to: `docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md`
   - Add investigation log: `docs/ISSUE_INVESTIGATION_LOG.md`
   - Place diagnostic script at: `scripts/diagnose_dev_connection.sh`
   - Register issue template: `.github/ISSUE_TEMPLATE/bug-api-connection.yml`

### Most Likely Causes in This Codebase:

Given the architecture examined:
- **Vite Proxy Config**: Currently targets `http://localhost:8000` without retry logic
- **FastAPI CORS**: Configured permissively, so not the blocker
- **Timing**: No startup synchronization between backend and frontend servers

**Root cause is most likely:** Vite proxy initializes before FastAPI fully binds to port 8000, causing initial requests to fail.

**Recommended Fix:**
Add health check retry logic to frontend API client (see Part 2, Cause A section).

================================================================================
End of Document
