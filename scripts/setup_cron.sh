#!/bin/bash
#
# Setup Cron Job for Daily Simulation
# This script helps configure a cron job to run the daily simulation automatically
#

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================================================="
echo "           Daily Simulation Cron Job Setup"
echo "======================================================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo ""

# Check if virtualenv exists
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "❌ Virtual environment not found at $PROJECT_DIR/.venv"
    echo "   Please create it first: python -m venv .venv"
    exit 1
fi

echo "✓ Virtual environment found"
echo ""

# Generate cron command
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCRIPT_PATH="$PROJECT_DIR/scripts/daily_simulation.py"
LOG_PATH="$PROJECT_DIR/logs/daily_simulation.log"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Cron entry (runs daily at 9:00 AM)
CRON_ENTRY="0 9 * * * $VENV_PYTHON $SCRIPT_PATH --days 1 >> $LOG_PATH 2>&1"

echo "Suggested cron entry (runs daily at 9:00 AM):"
echo ""
echo -e "${GREEN}$CRON_ENTRY${NC}"
echo ""
echo "======================================================================="
echo "MANUAL SETUP INSTRUCTIONS"
echo "======================================================================="
echo ""
echo "1. Open your crontab editor:"
echo "   ${YELLOW}crontab -e${NC}"
echo ""
echo "2. Add the following line:"
echo "   ${YELLOW}$CRON_ENTRY${NC}"
echo ""
echo "3. Save and exit (in vi: press ESC, then type :wq and press ENTER)"
echo ""
echo "4. Verify the cron job was added:"
echo "   ${YELLOW}crontab -l${NC}"
echo ""
echo "5. Check logs at:"
echo "   ${YELLOW}$LOG_PATH${NC}"
echo ""
echo "======================================================================="
echo "CRON SCHEDULE OPTIONS"
echo "======================================================================="
echo ""
echo "Change the first part to adjust the schedule:"
echo "  - Daily at 9:00 AM:    0 9 * * *"
echo "  - Daily at 6:00 AM:    0 6 * * *"
echo "  - Every 12 hours:      0 */12 * * *"
echo "  - Every 6 hours:       0 */6 * * *"
echo "  - Weekdays at 9:00 AM: 0 9 * * 1-5"
echo ""
echo "======================================================================="
echo "TESTING"
echo "======================================================================="
echo ""
echo "Test the script manually before setting up cron:"
echo "  ${YELLOW}$VENV_PYTHON $SCRIPT_PATH --days 1${NC}"
echo ""
echo "View recent simulations:"
echo "  ${YELLOW}$VENV_PYTHON $SCRIPT_PATH --summary-only${NC}"
echo ""
