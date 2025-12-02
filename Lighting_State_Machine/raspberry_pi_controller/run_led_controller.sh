#!/bin/bash
# Simple script to update and run LED controller on boot
# This script updates led_controller.py from GitHub, then runs it

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONTROLLER_FILE="$SCRIPT_DIR/led_controller.py"
GITHUB_REPO="Fox0317/Arduino_codebase"
GITHUB_BRANCH="main"
GITHUB_FILE_PATH="Lighting_State_Machine/raspberry_pi_controller/led_controller.py"
LOG_FILE="$SCRIPT_DIR/led_controller.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "LED Controller Startup"
log "=========================================="

# Step 1: Update from GitHub
log "Updating led_controller.py from GitHub..."

GITHUB_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/${GITHUB_FILE_PATH}"

if curl -s -f -L -o "${CONTROLLER_FILE}.tmp" "$GITHUB_URL"; then
    # Verify it's valid Python
    if python3 -m py_compile "${CONTROLLER_FILE}.tmp" 2>/dev/null; then
        mv "${CONTROLLER_FILE}.tmp" "$CONTROLLER_FILE"
        chmod +x "$CONTROLLER_FILE"
        log "Successfully updated led_controller.py from GitHub"
    else
        log "ERROR: Downloaded file is not valid Python. Using existing file."
        rm -f "${CONTROLLER_FILE}.tmp"
    fi
else
    log "WARNING: Failed to download from GitHub. Using existing file."
    rm -f "${CONTROLLER_FILE}.tmp"
fi

# Step 2: Run the controller
log "Starting LED Controller..."

if [ ! -f "$CONTROLLER_FILE" ]; then
    log "ERROR: Controller file not found!"
    exit 1
fi

# Run Python script and redirect all output to log file
python3 "$CONTROLLER_FILE" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
log "LED Controller exited with code: $EXIT_CODE"
exit $EXIT_CODE

