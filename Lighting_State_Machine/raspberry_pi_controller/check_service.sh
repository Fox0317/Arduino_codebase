#!/bin/bash
# Diagnostic script to check LED Controller service setup

echo "=========================================="
echo "LED Controller Service Diagnostic"
echo "=========================================="
echo ""

# Check if service file exists
SERVICE_FILE="/etc/systemd/system/led-controller.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "✓ Service file exists: $SERVICE_FILE"
else
    echo "✗ Service file NOT found: $SERVICE_FILE"
    echo "  Run: sudo cp led-controller.service /etc/systemd/system/"
fi
echo ""

# Check service status
echo "Service Status:"
sudo systemctl status led-controller.service --no-pager -l | head -n 20
echo ""

# Check if service is enabled
if systemctl is-enabled led-controller.service &>/dev/null; then
    echo "✓ Service is enabled for startup"
else
    echo "✗ Service is NOT enabled for startup"
    echo "  Run: sudo systemctl enable led-controller.service"
fi
echo ""

# Check paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Checking paths:"
echo "  Script directory: $SCRIPT_DIR"

START_SCRIPT="$SCRIPT_DIR/start_led_controller.sh"
if [ -f "$START_SCRIPT" ]; then
    echo "  ✓ Startup script exists: $START_SCRIPT"
    if [ -x "$START_SCRIPT" ]; then
        echo "  ✓ Startup script is executable"
    else
        echo "  ✗ Startup script is NOT executable"
        echo "    Run: chmod +x $START_SCRIPT"
    fi
else
    echo "  ✗ Startup script NOT found: $START_SCRIPT"
fi

CONTROLLER_FILE="$SCRIPT_DIR/led_controller.py"
if [ -f "$CONTROLLER_FILE" ]; then
    echo "  ✓ Controller file exists: $CONTROLLER_FILE"
    if [ -x "$CONTROLLER_FILE" ]; then
        echo "  ✓ Controller file is executable"
    else
        echo "  ✗ Controller file is NOT executable"
        echo "    Run: chmod +x $CONTROLLER_FILE"
    fi
else
    echo "  ✗ Controller file NOT found: $CONTROLLER_FILE"
fi
echo ""

# Check Python
echo "Checking Python:"
if command -v python3 &> /dev/null; then
    PYTHON_PATH=$(which python3)
    PYTHON_VERSION=$(python3 --version)
    echo "  ✓ Python3 found: $PYTHON_PATH"
    echo "  ✓ Version: $PYTHON_VERSION"
else
    echo "  ✗ Python3 NOT found in PATH"
fi
echo ""

# Check user
echo "Checking user:"
CURRENT_USER=$(whoami)
echo "  Current user: $CURRENT_USER"
if id "$CURRENT_USER" &>/dev/null; then
    echo "  ✓ User exists"
else
    echo "  ✗ User does NOT exist"
fi

# Check if user is in gpio group
if groups | grep -q gpio; then
    echo "  ✓ User is in 'gpio' group"
else
    echo "  ✗ User is NOT in 'gpio' group"
    echo "    Run: sudo usermod -a -G gpio $CURRENT_USER"
    echo "    Then log out and back in"
fi
echo ""

# Check logs
echo "Recent service logs:"
sudo journalctl -u led-controller.service -n 30 --no-pager
echo ""

# Check log files
echo "Log files:"
if [ -f "$SCRIPT_DIR/led_controller.log" ]; then
    echo "  Controller log exists: $SCRIPT_DIR/led_controller.log"
    echo "  Last 10 lines:"
    tail -n 10 "$SCRIPT_DIR/led_controller.log" | sed 's/^/    /'
else
    echo "  ✗ Controller log NOT found"
fi

if [ -f "$SCRIPT_DIR/led_controller_update.log" ]; then
    echo "  Update log exists: $SCRIPT_DIR/led_controller_update.log"
    echo "  Last 10 lines:"
    tail -n 10 "$SCRIPT_DIR/led_controller_update.log" | sed 's/^/    /'
else
    echo "  Update log not found (this is OK if update hasn't run)"
fi
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="

