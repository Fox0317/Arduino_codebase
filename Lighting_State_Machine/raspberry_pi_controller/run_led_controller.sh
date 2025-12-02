#!/bin/bash
# Simple script to update and run LED controller on boot
# This script updates led_controller.py from GitHub, then runs it

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

CONTROLLER_FILE="$SCRIPT_DIR/led_controller.py"
GITHUB_REPO="Fox0317/Arduino_codebase"
GITHUB_BRANCH="main"
GITHUB_FILE_PATH="Lighting_State_Machine/raspberry_pi_controller/led_controller.py"
LOG_FILE="$SCRIPT_DIR/led_controller.log"

# Create log file
touch "$LOG_FILE" 2>/dev/null || LOG_FILE="$HOME/led_controller.log"
touch "$LOG_FILE"

# Logging function - also output to stderr for systemd journal
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE" >&2
}

log "=========================================="
log "LED Controller Startup"
log "Script directory: $SCRIPT_DIR"
log "User: $(whoami)"
log "Python: $(which python3 2>/dev/null || echo 'NOT FOUND')"
log "=========================================="

# Step 1: Update from GitHub ONLY on system boot, not on service restarts
BOOT_FLAG_FILE="$SCRIPT_DIR/.update_on_boot_flag"
SYSTEM_UPTIME=$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo 0)

# Check if we should run update (only on fresh boot)
RUN_UPDATE=false

if [ ! -f "$BOOT_FLAG_FILE" ]; then
    # No flag file exists - this is likely a fresh boot
    RUN_UPDATE=true
    log "Fresh boot detected (uptime: ${SYSTEM_UPTIME}s). Will update from GitHub."
else
    # Flag file exists - check if it's from previous boot
    FLAG_MTIME=$(stat -c %Y "$BOOT_FLAG_FILE" 2>/dev/null || echo 0)
    CURRENT_TIME=$(date +%s)
    FLAG_AGE=$((CURRENT_TIME - FLAG_MTIME))
    
    # If flag file is older than system uptime, it's from previous boot
    if [ "$FLAG_AGE" -gt "$SYSTEM_UPTIME" ]; then
        RUN_UPDATE=true
        log "Fresh boot detected (uptime: ${SYSTEM_UPTIME}s, flag age: ${FLAG_AGE}s). Will update from GitHub."
    else
        log "Service restart detected (uptime: ${SYSTEM_UPTIME}s). Skipping update - already updated on boot."
    fi
fi

if [ "$RUN_UPDATE" = true ]; then
    log "Updating led_controller.py from GitHub..."
    
    # Check internet connectivity
    if ! ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
        log "WARNING: No internet connection. Skipping update, using existing file."
    else
        GITHUB_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/${GITHUB_FILE_PATH}"
        log "Downloading from: $GITHUB_URL"
        
        if curl -s -f -L -o "${CONTROLLER_FILE}.tmp" "$GITHUB_URL" 2>&1; then
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
            CURL_ERROR=$?
            log "WARNING: Failed to download from GitHub (exit code: $CURL_ERROR). Using existing file."
            rm -f "${CONTROLLER_FILE}.tmp"
        fi
    fi
    
    # Create/update flag file to mark update has run for this boot
    touch "$BOOT_FLAG_FILE"
    log "Update flag created. Future restarts will skip update until next boot."
fi

# Step 2: Run the controller
log "Starting LED Controller..."

if [ ! -f "$CONTROLLER_FILE" ]; then
    log "ERROR: Controller file not found at $CONTROLLER_FILE"
    log "Current directory: $(pwd)"
    log "Files in directory: $(ls -la 2>&1 | head -10)"
    exit 1
fi

# Check Python availability
if ! command -v python3 > /dev/null 2>&1; then
    log "ERROR: python3 not found in PATH"
    exit 1
fi

log "Running: python3 $CONTROLLER_FILE"
log "Output will be logged to: $LOG_FILE"
log "NOTE: If led_controller.py uses input(), it may fail when run as a service"

# Run Python script and redirect all output to log file
# Use unbuffered Python output for real-time logging
# Note: If the Python script calls input(), it will raise EOFError when stdin is not available
PYTHONUNBUFFERED=1 python3 "$CONTROLLER_FILE" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
log "LED Controller exited with code: $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
    log "ERROR: Controller failed. Last 20 lines of output:"
    tail -n 20 "$LOG_FILE" | while IFS= read -r line; do
        log "  $line"
    done
fi

exit $EXIT_CODE

