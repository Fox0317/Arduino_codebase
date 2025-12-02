# Enable LED Controller Auto-Start on Boot

Follow these steps to make `led_controller.py` launch automatically when your Raspberry Pi reboots.

## Quick Setup (Recommended)

Run the automated setup script:

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
chmod +x setup.sh
./setup.sh
```

The script will guide you through the setup process.

## Manual Setup

If you prefer to set it up manually, follow these steps:

### Step 1: Make Scripts Executable

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
chmod +x start_led_controller.sh
chmod +x update_from_github.sh
chmod +x led_controller.py
```

### Step 2: Verify Paths in Service File

Check that the paths in `led-controller.service` match your installation:

```bash
cat led-controller.service | grep -E "WorkingDirectory|ExecStart|User"
```

The paths should be:
- `WorkingDirectory=/home/Fox0317/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller`
- `ExecStart=/bin/bash /home/Fox0317/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/start_led_controller.sh`
- `User=Fox0317`

If they don't match, edit the service file:
```bash
nano led-controller.service
```

### Step 3: Install the Service

```bash
sudo cp led-controller.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### Step 4: Enable Service to Start on Boot

```bash
sudo systemctl enable led-controller.service
```

This creates a symlink so the service starts automatically on boot.

### Step 5: Start the Service Now (Optional)

```bash
sudo systemctl start led-controller.service
```

### Step 6: Verify It's Working

Check the service status:
```bash
sudo systemctl status led-controller.service
```

You should see `active (running)` if it's working.

## Verify Auto-Start is Enabled

Check if the service is enabled:
```bash
systemctl is-enabled led-controller.service
```

This should return `enabled`. If it returns `disabled`, run:
```bash
sudo systemctl enable led-controller.service
```

## Test on Next Boot

To test that it works on boot:
```bash
sudo reboot
```

After reboot, check if the service started:
```bash
sudo systemctl status led-controller.service
```

## Troubleshooting

### Service Not Starting

1. **Check service status:**
   ```bash
   sudo systemctl status led-controller.service
   ```

2. **Check logs:**
   ```bash
   sudo journalctl -u led-controller.service -n 50
   ```

3. **Check controller log:**
   ```bash
   cat ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log
   ```

4. **Test startup script manually:**
   ```bash
   cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
   ./start_led_controller.sh
   ```

### Service Enabled But Not Starting on Boot

1. **Verify service is enabled:**
   ```bash
   systemctl is-enabled led-controller.service
   ```

2. **Check if service file exists:**
   ```bash
   ls -la /etc/systemd/system/led-controller.service
   ```

3. **Reload systemd:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable led-controller.service
   ```

### Permission Issues

Make sure your user is in the `gpio` group:
```bash
groups
```

If `gpio` is not listed:
```bash
sudo usermod -a -G gpio Fox0317
```

Then log out and back in, or reboot.

### Path Issues

If paths are wrong, update the service file:
```bash
sudo nano /etc/systemd/system/led-controller.service
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart led-controller.service
```

## Useful Commands

```bash
# Check service status
sudo systemctl status led-controller.service

# View live logs
sudo journalctl -u led-controller.service -f

# Restart service
sudo systemctl restart led-controller.service

# Stop service
sudo systemctl stop led-controller.service

# Disable auto-start (if needed)
sudo systemctl disable led-controller.service

# Check if enabled
systemctl is-enabled led-controller.service
```

## Summary

The key steps are:
1. ✅ Make scripts executable
2. ✅ Install service file to `/etc/systemd/system/`
3. ✅ Run `sudo systemctl daemon-reload`
4. ✅ Run `sudo systemctl enable led-controller.service`
5. ✅ Reboot to test

Once enabled, the service will automatically start on every boot!

