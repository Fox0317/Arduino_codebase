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

# Calculate system boot time (current time - uptime)
CURRENT_TIME=$(date +%s)
SYSTEM_BOOT_TIME=$((CURRENT_TIME - SYSTEM_UPTIME))

# Check if we should run update (only on fresh boot)
RUN_UPDATE=false

if [ ! -f "$BOOT_FLAG_FILE" ]; then
    # No flag file exists - this is a fresh boot
    RUN_UPDATE=true
    log "Fresh boot detected (uptime: ${SYSTEM_UPTIME}s). Will update from GitHub."
else
    # Flag file exists - check if it's from this boot or previous boot
    FLAG_MTIME=$(stat -c %Y "$BOOT_FLAG_FILE" 2>/dev/null || echo 0)
    
    # If flag file was modified before system boot time, it's from previous boot
    if [ "$FLAG_MTIME" -lt "$SYSTEM_BOOT_TIME" ]; then
        RUN_UPDATE=true
        log "Fresh boot detected (uptime: ${SYSTEM_UPTIME}s). Flag file is from previous boot. Will update from GitHub."
    else
        log "Service restart detected (uptime: ${SYSTEM_UPTIME}s). Flag file is from this boot. Skipping update."
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

# Run Python script and redirect all output to log file
# Use unbuffered Python output for real-time logging
# The script now detects non-interactive mode automatically
log "Starting Python script..."
PYTHONUNBUFFERED=1 python3 "$CONTROLLER_FILE" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
log "LED Controller exited with code: $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
    log "ERROR: Controller failed with exit code $EXIT_CODE"
    log "Last 30 lines of controller output:"
    if [ -f "$LOG_FILE" ]; then
        tail -n 30 "$LOG_FILE" | while IFS= read -r line; do
            log "  $line"
        done
    else
        log "  Log file not found at $LOG_FILE"
    fi
    
    log "Common causes:"
    log "  1. Missing Python dependencies (RPi.GPIO, etc.)"
    log "  2. GPIO permission issues"
    log "  3. File not found or path issues"
    log "  4. Network connectivity issues (ESP32 connections)"
fi

exit $EXIT_CODE

