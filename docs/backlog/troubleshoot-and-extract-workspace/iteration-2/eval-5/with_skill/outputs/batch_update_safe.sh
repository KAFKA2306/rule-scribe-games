#!/bin/bash
# Emergency fix: Safe batch game update script
# Processes games sequentially with delays to avoid connection pool exhaustion
# Usage: bash batch_update_safe.sh

set -e

GAMES=(
    "catan"
    "ticket-to-ride"
    "carcassonne"
    "splendor"
    "azul"
    "wingspan"
    "everdell"
    "oink-games-title"
    "codenames"
    "dixit"
)

DELAY_BETWEEN_GAMES=1  # seconds
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=== Safe Batch Game Update ==="
echo "Total games: ${#GAMES[@]}"
echo "Delay between games: ${DELAY_BETWEEN_GAMES}s"
echo ""

SUCCESS_COUNT=0
FAILED_COUNT=0
FAILED_GAMES=()

for i in "${!GAMES[@]}"; do
    slug="${GAMES[$i]}"
    game_num=$((i + 1))

    echo "[${game_num}/${#GAMES[@]}] Processing $slug..."

    if python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.game_service import GameService
from app.core import logger

async def update():
    svc = GameService()
    result = await svc.update_game_content('$slug', fill_missing_only=True)
    return result

try:
    asyncio.run(update())
    print('✅ $slug updated successfully')
except Exception as e:
    print(f'❌ $slug failed: {e}')
    sys.exit(1)
"; then
        ((SUCCESS_COUNT++))
    else
        ((FAILED_COUNT++))
        FAILED_GAMES+=("$slug")
    fi

    if [ $game_num -lt ${#GAMES[@]} ]; then
        echo "  Waiting ${DELAY_BETWEEN_GAMES}s before next game..."
        sleep "$DELAY_BETWEEN_GAMES"
    fi
done

echo ""
echo "=== RESULTS ==="
echo "Succeeded: $SUCCESS_COUNT"
echo "Failed: $FAILED_COUNT"

if [ $FAILED_COUNT -gt 0 ]; then
    echo "Failed games:"
    for game in "${FAILED_GAMES[@]}"; do
        echo "  - $game"
    done
    exit 1
fi

echo "✅ All games processed successfully!"
exit 0
