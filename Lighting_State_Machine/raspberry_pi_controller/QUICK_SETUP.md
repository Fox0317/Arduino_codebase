# Quick Setup Guide - LED Controller Auto-Start

Follow these steps to set up `run_led_controller.sh` to automatically update and run on boot.

## Step-by-Step Setup

### Step 1: Navigate to Directory

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
```

### Step 2: Make Script Executable

```bash
chmod +x run_led_controller.sh
chmod +x led_controller.py
```

### Step 3: Verify GitHub Repository

Check that line 9 in `run_led_controller.sh` has your correct GitHub username:

```bash
grep GITHUB_REPO run_led_controller.sh
```

Should show: `GITHUB_REPO="Fox0317/Arduino_codebase"`

### Step 4: Verify Service File Paths

Check that paths in `led-controller.service` match your installation:

```bash
grep -E "WorkingDirectory|ExecStart|User" led-controller.service
```

Should show:
- `WorkingDirectory=/home/Fox0317/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller`
- `ExecStart=/bin/bash /home/Fox0317/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/run_led_controller.sh`
- `User=Fox0317`

If paths are wrong, edit the service file:
```bash
nano led-controller.service
```

### Step 5: Install the Service

```bash
sudo cp led-controller.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### Step 6: Enable Auto-Start on Boot

```bash
sudo systemctl enable led-controller.service
```

**This is the key step** - it makes the service start automatically on every boot.

### Step 7: Start the Service Now (Optional)

```bash
sudo systemctl start led-controller.service
```

### Step 8: Verify It's Working

```bash
sudo systemctl status led-controller.service
```

You should see `active (running)` in green.

## Verify Auto-Start is Enabled

```bash
systemctl is-enabled led-controller.service
```

Should return `enabled`. If it says `disabled`, run:
```bash
sudo systemctl enable led-controller.service
```

## Check Logs

```bash
# View systemd logs
sudo journalctl -u led-controller.service -f

# View controller log file
tail -f ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log
```

## Test on Reboot

Reboot to test:
```bash
sudo reboot
```

After reboot, check if it started:
```bash
sudo systemctl status led-controller.service
```

## What Happens on Boot

1. ✅ Systemd starts `led-controller.service`
2. ✅ Service runs `run_led_controller.sh`
3. ✅ Script checks if this is a fresh boot
4. ✅ If fresh boot: Downloads latest `led_controller.py` from GitHub
5. ✅ If service restart: Skips update (already updated on boot)
6. ✅ Runs `led_controller.py` continuously

## Troubleshooting

### Service Not Starting

```bash
# Check status
sudo systemctl status led-controller.service

# Check logs
sudo journalctl -u led-controller.service -n 50

# Check controller log
cat ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log
```

### Service Not Enabled

```bash
# Check if enabled
systemctl is-enabled led-controller.service

# Enable it
sudo systemctl enable led-controller.service
```

### Test Script Manually

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
./run_led_controller.sh
```

This will show any errors.

### Permission Issues

Make sure your user is in the `gpio` group:
```bash
sudo usermod -a -G gpio Fox0317
```

Then log out and back in, or reboot.

## Useful Commands

```bash
# Restart service
sudo systemctl restart led-controller.service

# Stop service
sudo systemctl stop led-controller.service

# View live logs
sudo journalctl -u led-controller.service -f

# Disable auto-start (if needed)
sudo systemctl disable led-controller.service
```

## Summary

The essential commands are:

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
chmod +x run_led_controller.sh led_controller.py
sudo cp led-controller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable led-controller.service
sudo systemctl start led-controller.service
```

That's it! The controller will now update from GitHub and run automatically on every boot.

