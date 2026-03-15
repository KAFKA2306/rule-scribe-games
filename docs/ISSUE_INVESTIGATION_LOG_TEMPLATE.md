# Investigation Log: Intermittent Frontend-API Connection

**Issue Title:** [Intermittent] Frontend cannot connect to API on dev server restart
**Date Opened:** [YYYY-MM-DD]
**Status:** [Open / In Progress / Resolved / Duplicate]
**Severity:** [Low / Medium / High / Critical]
**GitHub Issue:** #[number]

---

## Quick Summary

[Provide a one-paragraph overview of the problem and its impact]

---

## Timeline of Debugging Sessions

### Session 1 - [Date & Time]

**Environment:**
- OS: [Linux/macOS/Windows + version]
- Browser: [Chrome/Firefox/Safari version]
- Node Version: [output of `node --version`]
- Python Version: [output of `python --version`]

**Observed Behavior:**
- [Describe exactly what happened]
- Timestamp of failure: [exact time if possible]
- Frequency: [First time? Every restart? Every Nth attempt?]
- Reproducibility: [100% reproducible / intermittent / one-time]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. Observe: [What fails?]

**Network Tab Analysis:**
```
Request URL:     http://localhost:5173/api/[endpoint]
Request Method:  GET / POST / PATCH
Status Code:     [status or ERR_CONNECTION_REFUSED]
Response Headers:
  Content-Type: [header content]
  [other headers]
Response Body:   [error message or empty]
```

**Server Logs:**

Backend (FastAPI - uvicorn output):
```
[Paste relevant logs from terminal running `task dev:backend`]
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
[Any error messages around the time of failure]
```

Frontend (Vite - npm output):
```
[Paste relevant logs from terminal running `task dev:frontend`]
  ➜  Local:   http://localhost:5173/
[Any error messages or connection attempts]
```

**Diagnostic Script Output:**
```bash
# Run: bash scripts/diagnose_dev_connection.sh
[Paste full output here]
```

**Attempted Fixes:**
- [ ] Ran `task kill` and restarted `task dev`
- [ ] Reloaded browser (Ctrl+R / Cmd+R)
- [ ] Checked ports: `lsof -i :8000` and `lsof -i :5173`
- [ ] Tested direct API: `curl http://localhost:8000/health`
- [ ] Tested proxy: `curl http://localhost:5173/api/health`
- [ ] Ran `task clean && task setup`
- [ ] Checked `/etc/hosts` for localhost entry
- [ ] Other: [describe]

**Result of Each Fix:**
- task kill + restart: [worked / didn't work / partially worked]
- browser reload: [worked / didn't work]
- clean setup: [worked / didn't work]
- Other: [outcome]

**Root Cause Hypothesis (After Session 1):**
- [ ] Timing issue (Vite proxy before backend ready)
- [ ] Port already in use
- [ ] DNS/localhost resolution
- [ ] CORS misconfiguration
- [ ] Other: [describe]

**Evidence Supporting Hypothesis:**
[Link observations to likely cause]

---

### Session 2 - [Date & Time]

[Repeat the above structure for each debugging session. Track progression of understanding.]

---

### Session 3 - [Date & Time]

[Continue documenting sessions as new information emerges]

---

## Analysis & Findings

### What We Know

- Issue occurs: [describe the exact failure condition]
- Issue does NOT occur: [describe when it works fine]
- Pattern observed: [any recurring pattern? Time-based? Action-based?]

### What We've Ruled Out

- [ ] CORS misconfiguration (backend allows all origins)
- [ ] Firewall/antivirus blocking localhost (tested directly)
- [ ] Python/Node version incompatibility (verified versions)
- [ ] Other: [list]

### Most Likely Root Cause

**Primary Hypothesis:**
[Based on all evidence, what is the most likely cause?]

**Supporting Evidence:**
1. [Observation 1 that supports this]
2. [Observation 2 that supports this]
3. [Observation 3 that supports this]

**Confidence Level:** [Low / Medium / High]

---

## Proposed Solution

### Short-Term Workaround

For immediate relief while working on the permanent fix:
```bash
# Workaround steps
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

**Effectiveness:** [Worked/Partially worked/Didn't work]

### Long-Term Fix

**Implementation:**
- [ ] Add health check retry logic to frontend API client
- [ ] Stagger server startup in Taskfile
- [ ] Add backend startup confirmation logging
- [ ] Other: [describe]

**Files to Modify:**
1. `frontend/src/lib/api.js` - [describe change]
2. `Taskfile.yml` - [describe change]
3. `app/main.py` - [describe change]

**Testing Plan:**
1. Make the changes
2. Run `task dev`
3. Make 10 requests to API in quick succession
4. Test browser reload immediately after startup
5. Test after killing and restarting servers
6. Verify no errors in Network tab

**Expected Outcome:**
All API requests should succeed on first attempt without browser refresh.

---

## Resolution

**Final Root Cause:**
[Final determination after all investigation]

**Solution Applied:**
[What was actually done to fix it]

**Commits:**
- [commit hash] - [commit message]
- [commit hash] - [commit message]

**Testing Verification:**
- [Test 1 result]
- [Test 2 result]
- [Test 3 result]

**Status:** RESOLVED ✓

---

## Lessons Learned

1. [Key insight 1]
2. [Key insight 2]
3. [Key insight 3]

**Prevention for Future:**
- [Action to prevent recurrence]
- [Documentation update needed]
- [CI/CD check to add]

---

## Related Issues & References

- GitHub Issue: #[number]
- Related Issues: #[number], #[number]
- Documentation: [docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md](./TROUBLESHOOTING_DEV_ENVIRONMENT.md)
- Diagnostic Script: [scripts/diagnose_dev_connection.sh](../scripts/diagnose_dev_connection.sh)

---

## Quick Links for Next Developer

If this issue recurs, check:
1. Diagnostic script: `bash scripts/diagnose_dev_connection.sh`
2. Troubleshooting guide: `docs/TROUBLESHOOTING_DEV_ENVIRONMENT.md`
3. This investigation log: `docs/ISSUE_INVESTIGATION_LOG_TEMPLATE.md`
4. GitHub issue template: `.github/ISSUE_TEMPLATE/bug-api-connection.yml`

---

## Notes

[Any additional notes, gotchas, or important context for future reference]
