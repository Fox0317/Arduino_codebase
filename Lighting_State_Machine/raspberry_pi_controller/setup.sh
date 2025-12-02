#!/bin/bash
# Quick setup script for LED Controller auto-update and startup
# Run this script to set up everything automatically

set -e  # Exit on error

echo "=========================================="
echo "LED Controller Setup Script"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "ERROR: Please do not run this script as root/sudo"
   echo "The service will run as your user, but installation requires sudo for systemd"
   exit 1
fi

# Get current user
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)

echo "Detected user: $CURRENT_USER"
echo "Home directory: $CURRENT_HOME"
echo ""

# Prompt for GitHub repository
echo "Please enter your GitHub repository information:"
read -p "GitHub username/organization: " GITHUB_USER
read -p "Repository name [Arduino_codebase]: " GITHUB_REPO
GITHUB_REPO=${GITHUB_REPO:-Arduino_codebase}
read -p "Branch name [main]: " GITHUB_BRANCH
GITHUB_BRANCH=${GITHUB_BRANCH:-main}

echo ""
echo "Updating configuration files..."

# Update update_from_github.sh
sed -i "s|GITHUB_REPO=\"YOUR_GITHUB_USERNAME/Arduino_codebase\"|GITHUB_REPO=\"$GITHUB_USER/$GITHUB_REPO\"|g" update_from_github.sh
sed -i "s|GITHUB_BRANCH=\"main\"|GITHUB_BRANCH=\"$GITHUB_BRANCH\"|g" update_from_github.sh

# Update service file with actual paths
FULL_PATH="$SCRIPT_DIR"
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$FULL_PATH|g" led-controller.service
sed -i "s|ExecStart=.*|ExecStart=$FULL_PATH/start_led_controller.sh|g" led-controller.service
sed -i "s|User=Fox0317|User=$CURRENT_USER|g" led-controller.service

echo "Configuration updated!"
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x update_from_github.sh
chmod +x start_led_controller.sh
chmod +x led_controller.py
echo "Done!"
echo ""

# Test update script
echo "Testing update script..."
if ./update_from_github.sh; then
    echo "Update script test: SUCCESS"
else
    echo "Update script test: FAILED (this is OK if no internet or file doesn't exist on GitHub yet)"
fi
echo ""

# Install systemd service
echo "Installing systemd service..."
echo "This requires sudo privileges..."
sudo cp led-controller.service /etc/systemd/system/
sudo systemctl daemon-reload
echo "Service installed!"
echo ""

# Ask if user wants to enable and start service
read -p "Enable service to start on boot? (y/n): " ENABLE_SERVICE
if [[ $ENABLE_SERVICE =~ ^[Yy]$ ]]; then
    sudo systemctl enable led-controller.service
    echo "Service enabled for startup!"
fi

read -p "Start service now? (y/n): " START_SERVICE
if [[ $START_SERVICE =~ ^[Yy]$ ]]; then
    sudo systemctl start led-controller.service
    echo "Service started!"
    echo ""
    echo "Checking service status..."
    sleep 2
    sudo systemctl status led-controller.service --no-pager
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  View service status: sudo systemctl status led-controller.service"
echo "  View service logs:   sudo journalctl -u led-controller.service -f"
echo "  Restart service:      sudo systemctl restart led-controller.service"
echo "  Stop service:        sudo systemctl stop led-controller.service"
echo ""
echo "Log files (in script directory):"
echo "  Update log:  $FULL_PATH/led_controller_update.log"
echo "  Controller:  $FULL_PATH/led_controller.log"
echo ""

