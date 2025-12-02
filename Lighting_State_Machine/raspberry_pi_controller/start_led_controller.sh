#!/bin/bash
# Startup script for LED Controller
# Updates from GitHub, then launches the controller

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTROLLER_FILE="$SCRIPT_DIR/led_controller.py"
UPDATE_SCRIPT="$SCRIPT_DIR/update_from_github.sh"
# Use log file in script directory (user has write permissions here)
LOG_FILE="$SCRIPT_DIR/led_controller.log"

# Create log file if it doesn't exist
touch "$LOG_FILE" 2>/dev/null || {
    # Fallback to home directory if script directory is not writable
    LOG_FILE="$HOME/led_controller.log"
    touch "$LOG_FILE"
}

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "Starting LED Controller startup script"

# Change to script directory
cd "$SCRIPT_DIR" || exit 1

# Only run update on system boot, not on service restarts
# Use a flag file to track if update has run for current boot
BOOT_FLAG_FILE="$SCRIPT_DIR/.update_on_boot_flag"
SYSTEM_UPTIME=$(awk '{print int($1)}' /proc/uptime)  # Uptime in seconds

# Check if we should run update (only on fresh boot)
if [ -f "$UPDATE_SCRIPT" ]; then
    RUN_UPDATE=false
    
    if [ ! -f "$BOOT_FLAG_FILE" ]; then
        # No flag file exists - this is likely a fresh boot
        RUN_UPDATE=true
        log_message "No update flag found. Fresh boot detected (uptime: ${SYSTEM_UPTIME}s)."
    else
        # Flag file exists - check if it's from previous boot
        FLAG_MTIME=$(stat -c %Y "$BOOT_FLAG_FILE" 2>/dev/null || echo 0)
        CURRENT_TIME=$(date +%s)
        FLAG_AGE=$((CURRENT_TIME - FLAG_MTIME))
        
        # If flag file is older than system uptime, it's from previous boot
        if [ "$FLAG_AGE" -gt "$SYSTEM_UPTIME" ]; then
            RUN_UPDATE=true
            log_message "Update flag is from previous boot. Fresh boot detected (uptime: ${SYSTEM_UPTIME}s, flag age: ${FLAG_AGE}s)."
        else
            log_message "Update already ran for this boot (uptime: ${SYSTEM_UPTIME}s). Skipping update."
        fi
    fi
    
    if [ "$RUN_UPDATE" = true ]; then
        log_message "Running update script..."
        bash "$UPDATE_SCRIPT"
        # Create/update flag file to mark update has run for this boot
        touch "$BOOT_FLAG_FILE"
    fi
else
    log_message "WARNING: Update script not found at $UPDATE_SCRIPT"
fi

# Wait a moment for any file system operations to complete
sleep 1

# Check if controller file exists
if [ ! -f "$CONTROLLER_FILE" ]; then
    log_message "ERROR: Controller file not found at $CONTROLLER_FILE"
    exit 1
fi

# Make sure controller file is executable
chmod +x "$CONTROLLER_FILE"

# Launch the controller
log_message "Launching LED Controller..."
log_message "Python path: $(which python3)"
log_message "Controller file: $CONTROLLER_FILE"
log_message "Working directory: $(pwd)"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log_message "ERROR: python3 not found in PATH"
    exit 1
fi

# Launch the controller with explicit Python path
/usr/bin/python3 "$CONTROLLER_FILE" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
log_message "LED Controller exited with code: $EXIT_CODE"

# If exit code is non-zero, log it for debugging
if [ $EXIT_CODE -ne 0 ]; then
    log_message "ERROR: Controller exited with error code $EXIT_CODE"
    log_message "Last 20 lines of controller output:"
    tail -n 20 "$LOG_FILE" | while read line; do
        log_message "  $line"
    done
fi

exit $EXIT_CODE

