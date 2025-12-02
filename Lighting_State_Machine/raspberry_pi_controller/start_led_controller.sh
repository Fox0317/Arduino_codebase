#!/bin/bash
# Startup script for LED Controller
# Updates from GitHub, then launches the controller
# Note: We don't use 'set -e' so we can handle errors gracefully and log them

# Get script directory
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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE" || echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Also log to stderr for systemd journal
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
    log_message "ERROR: $1"
}

log_message "=========================================="
log_message "Starting LED Controller startup script"
log_message "Script directory: $SCRIPT_DIR"
log_message "User: $(whoami)"
log_message "Home: $HOME"
log_message "PATH: $PATH"

# Change to script directory
if ! cd "$SCRIPT_DIR"; then
    log_error "Failed to change to script directory: $SCRIPT_DIR"
    exit 1
fi
log_message "Changed to directory: $(pwd)"

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
        if bash "$UPDATE_SCRIPT"; then
            log_message "Update script completed successfully"
        else
            UPDATE_EXIT=$?
            log_error "Update script failed with exit code $UPDATE_EXIT, but continuing anyway"
        fi
        # Create/update flag file to mark update has run for this boot (even if it failed)
        touch "$BOOT_FLAG_FILE"
    fi
else
    log_message "WARNING: Update script not found at $UPDATE_SCRIPT"
fi

# Wait a moment for any file system operations to complete
sleep 1

# Check if controller file exists
if [ ! -f "$CONTROLLER_FILE" ]; then
    log_error "Controller file not found at $CONTROLLER_FILE"
    log_error "Current directory: $(pwd)"
    log_error "Files in directory: $(ls -la)"
    exit 1
fi

log_message "Controller file found: $CONTROLLER_FILE"

# Make sure controller file is executable
if ! chmod +x "$CONTROLLER_FILE" 2>/dev/null; then
    log_error "Failed to make controller file executable"
    exit 1
fi
log_message "Controller file is executable"

# Pre-launch checks complete
log_message "All pre-launch checks passed"

# Check if Python is available
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD=$(which python3)
elif [ -f "/usr/bin/python3" ]; then
    PYTHON_CMD="/usr/bin/python3"
elif [ -f "/usr/local/bin/python3" ]; then
    PYTHON_CMD="/usr/local/bin/python3"
else
    log_error "python3 not found in PATH or standard locations"
    log_error "Searched: $(which python3 2>&1 || echo 'not found')"
    exit 1
fi

log_message "Using Python: $PYTHON_CMD"
log_message "Python version: $($PYTHON_CMD --version 2>&1)"

# Check if Python can import required modules
log_message "Checking Python dependencies..."
if ! $PYTHON_CMD -c "import sys; print('Python OK')" 2>&1; then
    log_error "Python is not working correctly"
    exit 1
fi

# Launch the controller
log_message "Launching LED Controller with: $PYTHON_CMD $CONTROLLER_FILE"
$PYTHON_CMD "$CONTROLLER_FILE" >> "$LOG_FILE" 2>&1

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

