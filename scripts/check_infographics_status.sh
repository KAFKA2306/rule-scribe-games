#!/bin/bash
# Infographics Feature Deployment Status Checker
# Verifies each stage of the infographics implementation

set -e

echo "🎨 Infographics Feature Status Check"
echo "===================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stage 1: Files exist
echo "📋 Stage 1: Files & Structure"
echo "----"

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

check_file "backend/app/db/migrations/002_add_infographics_column.sql"
check_file "backend/scripts/migrate_infographics.py"
check_file "frontend/src/components/game/InfographicsGallery.jsx"
check_file "tests/test_infographics.py"
check_file "docs/INFOGRAPHICS_DEPLOYMENT.md"
check_file ".claude/skills/infographics-deployment/SKILL.md"

echo ""

# Stage 2: Backend running
echo "🖥️  Stage 2: Backend Server"
echo "----"

if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} FastAPI running on :8000"
    
    # Check if infographics column exists
    INFOGRAPHICS_CHECK=$(curl -s http://localhost:8000/api/games/splendor | grep -o '"infographics"' || echo "")
    if [ ! -z "$INFOGRAPHICS_CHECK" ]; then
        echo -e "${GREEN}✓${NC} infographics field in API response"
    fi
else
    echo -e "${YELLOW}⚠${NC}  FastAPI not running (start with: task dev)"
fi

echo ""

# Stage 3: Frontend running
echo "🎨 Stage 3: Frontend Server"
echo "----"

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Vite running on :5173"
else
    echo -e "${YELLOW}⚠${NC}  Vite not running (start with: task dev)"
fi

echo ""

# Stage 4: Database migration
echo "💾 Stage 4: Database Migration"
echo "----"

echo -e "${YELLOW}ℹ${NC}  Migration requires Supabase dashboard access"
echo "   SQL to run:"
echo "   ---"
cat backend/app/db/migrations/002_add_infographics_column.sql | sed 's/^/   /'
echo "   ---"
echo ""
echo "   Dashboard: https://app.supabase.com → SQL Editor"

echo ""

# Stage 5: Next steps
echo "🚀 Next Steps"
echo "----"

echo "1. Apply database migration (Supabase dashboard)"
echo "2. Run: python backend/scripts/migrate_infographics.py"
echo "3. Test: http://localhost:5173/games/splendor → 📊 図解 tab"
echo "4. Verify: pytest tests/test_infographics.py"
echo "5. Deploy: git push origin main"

echo ""
echo "📖 Full guide: docs/INFOGRAPHICS_DEPLOYMENT.md"
echo "🛠️  Skill reference: .claude/skills/infographics-deployment/SKILL.md"
