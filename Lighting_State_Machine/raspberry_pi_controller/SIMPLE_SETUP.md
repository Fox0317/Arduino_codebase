# Simple Setup - Auto-Start LED Controller on Boot

This guide will set up your Raspberry Pi to:
1. **Update** `led_controller.py` from GitHub on every reboot
2. **Run** the controller automatically without user input

## Step-by-Step Instructions

### Step 1: Navigate to the Directory

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
```

### Step 2: Make Scripts Executable

```bash
chmod +x run_led_controller.sh led_controller.py
```

### Step 3: Verify GitHub Repository

Make sure line 9 in `run_led_controller.sh` has your correct GitHub username:
```bash
grep GITHUB_REPO run_led_controller.sh
```

It should show: `GITHUB_REPO="Fox0317/Arduino_codebase"`

### Step 4: Verify Service File Paths

Check that the paths in `led-controller.service` match your installation:
```bash
grep -E "WorkingDirectory|ExecStart|User" led-controller.service
```

If your username or paths are different, edit the service file:
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

### Step 7: Start the Service Now

```bash
sudo systemctl start led-controller.service
```

### Step 8: Verify It's Working

```bash
sudo systemctl status led-controller.service
```

You should see `active (running)` in green.

### Step 9: Check Logs

```bash
# View systemd logs
sudo journalctl -u led-controller.service -f

# View controller log file
tail -f ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log
```

## Test on Reboot

Reboot your Raspberry Pi:
```bash
sudo reboot
```

After reboot, check if it started:
```bash
sudo systemctl status led-controller.service
```

## What Happens on Boot

1. Systemd starts the `led-controller.service`
2. Service runs `run_led_controller.sh`
3. Script downloads latest `led_controller.py` from GitHub
4. Script runs `led_controller.py` (non-interactive mode)
5. Controller runs continuously, responding to encoder/switch inputs

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

# If disabled, enable it
sudo systemctl enable led-controller.service
```

### Permission Issues

Make sure your user is in the `gpio` group:
```bash
sudo usermod -a -G gpio Fox0317
```

Then log out and back in, or reboot.

### Test Script Manually

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
./run_led_controller.sh
```

This will show you any errors.

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

The key commands are:
1. `sudo cp led-controller.service /etc/systemd/system/`
2. `sudo systemctl daemon-reload`
3. `sudo systemctl enable led-controller.service`
4. `sudo systemctl start led-controller.service`

That's it! The controller will now update and run automatically on every boot.

