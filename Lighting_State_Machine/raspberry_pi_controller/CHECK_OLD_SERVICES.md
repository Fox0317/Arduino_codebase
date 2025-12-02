# Check and Disable Old Services

If you've installed services before, you should check for and disable any old ones to prevent conflicts.

## Check for Existing Services

### List All LED Controller Related Services

```bash
# Check for any services with "led" or "controller" in the name
systemctl list-unit-files | grep -i "led\|controller"

# Check for the specific service
systemctl list-unit-files | grep led-controller
```

### Check Service Status

```bash
# Check if led-controller.service is already installed
sudo systemctl status led-controller.service

# Check if it's enabled
systemctl is-enabled led-controller.service
```

## Disable Old Services

### If led-controller.service Already Exists

If you see the service is already installed and enabled:

```bash
# Stop the old service
sudo systemctl stop led-controller.service

# Disable it (remove from auto-start)
sudo systemctl disable led-controller.service

# Remove the old service file (optional, will be replaced)
sudo rm /etc/systemd/system/led-controller.service

# Reload systemd
sudo systemctl daemon-reload
```

### Check for Other Service Names

Sometimes services might be named differently. Check for:

```bash
# Check all systemd services
systemctl list-units --type=service --all | grep -i "led\|controller\|lighting"

# Check service files
ls -la /etc/systemd/system/ | grep -i "led\|controller"
```

## Clean Setup Process

To ensure a clean setup:

```bash
# 1. Stop any existing service
sudo systemctl stop led-controller.service 2>/dev/null

# 2. Disable any existing service
sudo systemctl disable led-controller.service 2>/dev/null

# 3. Remove old service file
sudo rm -f /etc/systemd/system/led-controller.service

# 4. Reload systemd
sudo systemctl daemon-reload

# 5. Reset failed service states (if any)
sudo systemctl reset-failed

# 6. Now install the new service
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
sudo cp led-controller.service /etc/systemd/system/
sudo systemctl daemon-reload

# 7. Enable and start
sudo systemctl enable led-controller.service
sudo systemctl start led-controller.service
```

## Verify Clean State

After cleaning up:

```bash
# Check service status
sudo systemctl status led-controller.service

# Verify only one service file exists
ls -la /etc/systemd/system/led-controller.service

# Check if enabled
systemctl is-enabled led-controller.service
```

## Common Issues

### Multiple Service Files

If you see multiple service files:
```bash
# List all service files
ls -la /etc/systemd/system/ | grep led

# Remove duplicates (keep only the correct one)
sudo rm /etc/systemd/system/led-controller.service.old  # or similar
sudo systemctl daemon-reload
```

### Service Won't Stop

If the service won't stop:
```bash
# Force stop
sudo systemctl stop led-controller.service --force

# Kill any remaining processes
sudo pkill -f led_controller.py
```

## Summary

**Yes, you should disable old services** to prevent conflicts. Run:

```bash
sudo systemctl stop led-controller.service
sudo systemctl disable led-controller.service
sudo systemctl daemon-reload
```

Then proceed with the new setup.

