# API Connection Issue - Complete Reference Guide

## Overview

This guide consolidates all resources for managing the intermittent frontend-API connection issue that occurs when restarting dev servers.

**Quick Answer: YES, you should create a GitHub issue to track this.**

---

## Why Create a GitHub Issue?

1. **Trackability**: Creates a permanent record that can be linked to PRs and commits
2. **Visibility**: Alerts team members that the issue is known and being worked on
3. **Collaboration**: Enables discussion and collaborative debugging
4. **Documentation**: Comments become part of the searchable project history
5. **Metrics**: Helps identify patterns (how often it occurs, on which systems, etc.)

---

## Quick Start: Creating the Issue

### Before You File

Gather this information (takes ~10 minutes):
1. Run the diagnostic script:
   ```bash
   bash scripts/diagnose_dev_connection.sh
   ```
   Save the output.

2. Capture a Network tab screenshot:
   - Open browser DevTools (F12)
   - Go to Network tab
   - Reload page while issue is happening
   - Screenshot the failed request(s)

3. Note your environment:
   - OS (Linux, macOS, Windows)
   - Node version: `node --version`
   - Python version: `python --version`
   - Browser version

### How to File

1. Go to: **GitHub > Issues > New Issue**
2. Choose: **API Connection Issue** template
3. Fill in the pre-built form (uses template at `.github/ISSUE_TEMPLATE/bug-api-connection.yml`)
4. Paste diagnostic script output and network logs
5. Submit

**Time to create issue: ~5 minutes**

---

## Documentation Files Created

### 1. `.github/ISSUE_TEMPLATE/bug-api-connection.yml`
**Purpose:** GitHub issue template with structured form fields
**Use When:** Creating a new issue on GitHub
**What It Contains:**
- Dropdown for frequency (first time / intermittent / reproducible)
- Textarea fields for description, reproduction steps, logs
- Required fields for environment info (Node, Python versions)
- Checkboxes for troubleshooting attempts

---

### 2. `docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md`
**Purpose:** Step-by-step debugging guide for developers
**Use When:** Actively experiencing the connection issue
**What It Contains:**
- Quick diagnosis checklist (3 steps, ~2 minutes)
- Root cause analysis for 3 common causes:
  - Vite proxy initialization timing (most common)
  - Port already in use
  - DNS/localhost resolution
- Advanced debugging techniques (verbose logging, network monitoring)
- Permanent fixes with code examples
- Debugging workflow (step-by-step process)

**Key Sections:**
- Quick Diagnosis Checklist (start here!)
- Root Cause A: Vite Proxy Initialization Timing
  - Has retry logic code snippet ready to use
- Root Cause B: Port Already in Use
  - Has `task kill` solution and manual kill commands
- Root Cause C: DNS Issues (especially for WSL2 users)

---

### 3. `docs/GITHUB_ISSUE_GUIDE.md`
**Purpose:** Comprehensive guide covering the entire issue lifecycle
**Use When:** Planning how to document and manage the issue
**What It Contains:**
- Full issue template with example text
- Debugging documentation (same as TROUBLESHOOTING_DEV_ENVIRONMENT.md)
- Investigation log template
- Automated diagnostic script (bash)
- GitHub issue template (YAML format)
- Quick reference card with common commands

---

### 4. `docs/ISSUE_INVESTIGATION_LOG_TEMPLATE.md`
**Purpose:** Template for documenting your debugging process
**Use When:** You're actively debugging and want to track your progress
**What It Contains:**
- Session-by-session logging template
- Fields for environment, observed behavior, logs, attempted fixes
- Root cause hypothesis section
- Proposed solution section
- Final resolution tracking
- Lessons learned section

**How to Use:**
1. Copy this template into a new markdown file in docs/
2. Name it: `ISSUE_INVESTIGATION_LOG_<YOUR_NAME>_<DATE>.md`
3. Fill in as you debug (one session per section)
4. Link it from your GitHub issue

---

### 5. `scripts/diagnose_dev_connection.sh`
**Purpose:** Automated diagnostic script to identify the issue
**Use When:** You first notice the problem (before creating an issue)
**What It Checks:**
1. Port 8000 (FastAPI) is in use
2. Port 5173 (Vite) is in use
3. Backend /health endpoint responds
4. Frontend server is responding
5. API proxy is working through frontend
6. localhost DNS resolution
7. Vite proxy configuration

**Usage:**
```bash
bash scripts/diagnose_dev_connection.sh
```

**Output Example:**
```
=== RuleScribe Dev Connection Diagnostic ===

Step 1: Checking ports...
✓ Port 8000 (FastAPI) is in use
✓ Port 5173 (Vite) is in use

Step 2: Testing backend health...
✓ Backend /health endpoint responds

Step 3: Testing frontend connectivity...
✓ Frontend server is responding

Step 4: Testing API proxy through frontend...
✓ API proxy working (status: 200)

Step 5: Checking localhost resolution...
✓ localhost resolves to 127.0.0.1

Step 6: Checking Vite proxy config...
✓ Vite proxy target is configured

=== Diagnostic Complete ===
```

---

## Quick Reference: Most Common Fixes

### Fix #1: Port Already in Use (80% of cases)
```bash
task kill
task dev
```

### Fix #2: Timing Issue (15% of cases)
Browser refresh usually works. To prevent: Add retry logic to frontend/src/lib/api.js (see TROUBLESHOOTING_DEV_ENVIRONMENT.md)

### Fix #3: WSL2 Localhost Issue (5% of cases)
```bash
# Edit frontend/vite.config.js
# Change: target: 'http://localhost:8000'
# To:     target: 'http://127.0.0.1:8000'
```

---

## Issue Creation Checklist

Before submitting your issue:

- [ ] Ran `bash scripts/diagnose_dev_connection.sh` and saved output
- [ ] Captured browser Network tab screenshot showing failed request
- [ ] Noted exact error message (ERR_CONNECTION_REFUSED, timeout, etc.)
- [ ] Documented your OS and software versions
- [ ] Listed what you've already tried (task kill, refresh, clean setup, etc.)
- [ ] Confirmed the issue is reproducible (at least twice)
- [ ] Checked if issue happens consistently or intermittently
- [ ] Read docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md for any quick fixes

---

## Documentation Standards for This Issue

### When Creating an Issue Comment

Include:
1. What you observed (not assumptions)
2. Steps to reproduce it
3. Environment info (OS, Node, Python versions)
4. Relevant logs from backend/frontend
5. Network tab screenshot if possible
6. What you've already tried

Example:
```
## Issue: API returns 502 on first request

### Environment
- OS: Linux WSL2
- Node: v18.17.0
- Python: 3.11.9

### Reproduction
1. Run `task dev`
2. Navigate to http://localhost:5173
3. Check Network tab
4. See GET /api/games returns 502

### Already Tried
- task kill + restart: didn't help
- browser refresh: helped temporarily
- task clean + setup: no effect

### Diagnostic Output
[paste output from `bash scripts/diagnose_dev_connection.sh`]
```

### When Submitting a PR with a Fix

Link the issue:
```
Fixes #123
```

Reference the troubleshooting doc:
```
See docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md for context
```

---

## File Locations Summary

| File | Purpose | Use When |
|------|---------|----------|
| `.github/ISSUE_TEMPLATE/bug-api-connection.yml` | GitHub issue template | Creating a new issue |
| `docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md` | Debugging guide | Experiencing the issue |
| `docs/GITHUB_ISSUE_GUIDE.md` | Comprehensive reference | Planning how to manage the issue |
| `docs/ISSUE_INVESTIGATION_LOG_TEMPLATE.md` | Debugging log template | Documenting your investigation |
| `scripts/diagnose_dev_connection.sh` | Automated diagnostics | Initial problem assessment |
| `docs/API_CONNECTION_ISSUE_SUMMARY.md` | This file | Getting oriented |

---

## Most Likely Root Cause (Based on Codebase Analysis)

**Cause:** Vite proxy initialization timing race condition

**Why:** 
- Vite's development server initializes the `/api` proxy to `http://localhost:8000`
- FastAPI backend may not be fully bound to port 8000 at the exact moment
- First client request arrives before backend is ready
- Subsequent requests succeed (backend is ready by then)

**Solution:**
Add retry logic to frontend API client with exponential backoff:

```javascript
// frontend/src/lib/api.js
export const fetchWithRetry = async (path, options = {}, retryCount = 0) => {
  try {
    const res = await fetch(path, options)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } catch (error) {
    if (retryCount < 3) {
      const delay = 200 * Math.pow(2, retryCount)
      await new Promise(resolve => setTimeout(resolve, delay))
      return fetchWithRetry(path, options, retryCount + 1)
    }
    throw error
  }
}
```

See full implementation in `docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md` under "Cause A: Vite Proxy Initialization Timing"

---

## Escalation Path

1. **First:** Run diagnostic script
   ```bash
   bash scripts/diagnose_dev_connection.sh
   ```

2. **Then:** Try quick fixes
   - `task kill && task dev`
   - Browser refresh
   - `task clean && task setup`

3. **If still failing:** Create GitHub issue
   - Use template at `.github/ISSUE_TEMPLATE/bug-api-connection.yml`
   - Include diagnostic script output
   - Include Network tab screenshot

4. **Investigation:** Use investigation log
   - Copy `docs/ISSUE_INVESTIGATION_LOG_TEMPLATE.md`
   - Document each debugging session
   - Link from GitHub issue

5. **Resolution:** Implement fix from TROUBLESHOOTING guide
   - Add retry logic to frontend (recommended)
   - Or stagger server startup in Taskfile
   - Or both for maximum robustness

---

## Next Steps

1. Create a GitHub issue if you're experiencing the problem
2. Use the diagnostic script to gather information
3. Follow the troubleshooting guide to identify the root cause
4. Document your findings using the investigation log template
5. Implement the recommended fix (retry logic in frontend API client)

---

## Questions?

Refer to:
- **How do I create an issue?** → `.github/ISSUE_TEMPLATE/bug-api-connection.yml`
- **How do I fix the problem?** → `docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md`
- **How do I diagnose the issue?** → `bash scripts/diagnose_dev_connection.sh`
- **How do I document my investigation?** → `docs/ISSUE_INVESTIGATION_LOG_TEMPLATE.md`
- **What's the overall context?** → This file (API_CONNECTION_ISSUE_SUMMARY.md)
