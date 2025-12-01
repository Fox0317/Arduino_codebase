#!/bin/bash
# Startup script for LED Controller
# Updates from GitHub, then launches the controller

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTROLLER_FILE="$SCRIPT_DIR/led_controller.py"
UPDATE_SCRIPT="$SCRIPT_DIR/update_from_github.sh"
LOG_FILE="/var/log/led_controller.log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "Starting LED Controller startup script"

# Change to script directory
cd "$SCRIPT_DIR" || exit 1

# Run update script first
if [ -f "$UPDATE_SCRIPT" ]; then
    log_message "Running update script..."
    bash "$UPDATE_SCRIPT"
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
python3 "$CONTROLLER_FILE" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
log_message "LED Controller exited with code: $EXIT_CODE"

exit $EXIT_CODE

