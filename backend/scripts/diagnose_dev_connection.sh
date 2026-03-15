#!/bin/bash
# Diagnostic script for frontend-API connection issues
# Usage: bash scripts/diagnose_dev_connection.sh

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
