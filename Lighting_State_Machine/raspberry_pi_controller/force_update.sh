#!/bin/bash
# Force update led_controller.py from GitHub immediately
# This bypasses the boot detection logic

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

CONTROLLER_FILE="$SCRIPT_DIR/led_controller.py"
GITHUB_REPO="Fox0317/Arduino_codebase"
GITHUB_BRANCH="main"
GITHUB_FILE_PATH="Lighting_State_Machine/raspberry_pi_controller/led_controller.py"

echo "Forcing update of led_controller.py from GitHub..."
echo "Repository: $GITHUB_REPO"
echo "Branch: $GITHUB_BRANCH"
echo "File: $GITHUB_FILE_PATH"
echo ""

# Check internet connectivity
if ! ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
    echo "ERROR: No internet connection. Cannot update."
    exit 1
fi

GITHUB_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/${GITHUB_FILE_PATH}"
echo "Downloading from: $GITHUB_URL"

if curl -s -f -L -o "${CONTROLLER_FILE}.tmp" "$GITHUB_URL" 2>&1; then
    # Verify it's valid Python
    if python3 -m py_compile "${CONTROLLER_FILE}.tmp" 2>/dev/null; then
        mv "${CONTROLLER_FILE}.tmp" "$CONTROLLER_FILE"
        chmod +x "$CONTROLLER_FILE"
        echo "✓ Successfully updated led_controller.py from GitHub"
        echo ""
        echo "The service will automatically restart with the new version."
        echo "Or restart manually with: sudo systemctl restart led-controller.service"
        exit 0
    else
        echo "ERROR: Downloaded file is not valid Python. Update failed."
        rm -f "${CONTROLLER_FILE}.tmp"
        exit 1
    fi
else
    CURL_ERROR=$?
    echo "ERROR: Failed to download from GitHub (exit code: $CURL_ERROR)."
    rm -f "${CONTROLLER_FILE}.tmp"
    exit 1
fi

