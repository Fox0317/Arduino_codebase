#!/bin/bash
# Update script for led_controller.py from GitHub
# This script ONLY updates led_controller.py from your Arduino_codebase GitHub repo
# It does NOT clone the entire repository - only downloads the single file

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTROLLER_FILE="$SCRIPT_DIR/led_controller.py"
GITHUB_REPO="Fox0317/Arduino_codebase"  # Only your repo, no cloning
GITHUB_BRANCH="main"
GITHUB_FILE_PATH="Lighting_State_Machine/raspberry_pi_controller/led_controller.py"  # Only this file
# Use log file in script directory (user has write permissions here)
LOG_FILE="$SCRIPT_DIR/led_controller_update.log"

# Create log file if it doesn't exist
touch "$LOG_FILE" 2>/dev/null || {
    # Fallback to home directory if script directory is not writable
    LOG_FILE="$HOME/led_controller_update.log"
    touch "$LOG_FILE"
}

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "Starting update check for led_controller.py"

# Check if we have internet connectivity
if ! ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
    log_message "No internet connection. Skipping update."
    exit 0
fi

# Construct GitHub raw URL (downloads only the single file, not the entire repo)
GITHUB_RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/${GITHUB_FILE_PATH}"
log_message "GitHub URL: $GITHUB_RAW_URL"
log_message "Only updating led_controller.py - no repository cloning"

# Create backup of current file
if [ -f "$CONTROLLER_FILE" ]; then
    BACKUP_FILE="${CONTROLLER_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CONTROLLER_FILE" "$BACKUP_FILE"
    log_message "Created backup: $BACKUP_FILE"
fi

# Download latest version
log_message "Downloading latest version from GitHub..."
TEMP_FILE="${CONTROLLER_FILE}.tmp"

if curl -s -f -L -o "$TEMP_FILE" "$GITHUB_RAW_URL"; then
    # Verify the downloaded file is valid Python
    if python3 -m py_compile "$TEMP_FILE" 2>/dev/null; then
        # Replace old file with new one
        mv "$TEMP_FILE" "$CONTROLLER_FILE"
        chmod +x "$CONTROLLER_FILE"
        log_message "Successfully updated led_controller.py from GitHub"
        
        # Keep only last 5 backups
        ls -t "${CONTROLLER_FILE}.backup."* 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
    else
        log_message "ERROR: Downloaded file is not valid Python. Keeping existing file."
        rm -f "$TEMP_FILE"
        exit 1
    fi
else
    log_message "ERROR: Failed to download from GitHub. Keeping existing file."
    rm -f "$TEMP_FILE"
    exit 1
fi

log_message "Update check completed"
exit 0

