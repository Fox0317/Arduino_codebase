# Debugging Exit Code 1

If the service shows `(code=exited, status=1/FAILURE)`, check these in order:

## 1. Check Service Logs

```bash
sudo journalctl -u led-controller.service -n 100 --no-pager
```

Look for ERROR messages or the last successful log entry.

## 2. Check Controller Log File

```bash
cat ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log
```

Or if that doesn't exist:
```bash
cat ~/led_controller.log
```

## 3. Common Causes and Fixes

### Cause: Can't Change Directory
**Error**: "Failed to change to script directory"
**Fix**: 
```bash
ls -la ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/
```
Verify the directory exists and is accessible.

### Cause: Controller File Not Found
**Error**: "Controller file not found"
**Fix**:
```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
ls -la led_controller.py
```
If missing, the update script may have failed. Run it manually:
```bash
./update_from_github.sh
```

### Cause: Python Not Found
**Error**: "python3 not found"
**Fix**:
```bash
which python3
python3 --version
```
If not found, install Python:
```bash
sudo apt update
sudo apt install python3
```

### Cause: Python Module Import Error
**Error**: Usually shows in controller log, not startup script
**Fix**: Check if RPi.GPIO is installed:
```bash
python3 -c "import RPi.GPIO; print('OK')"
```
If it fails:
```bash
pip3 install RPi.GPIO
```

### Cause: GPIO Permission Error
**Error**: "Permission denied" or GPIO access errors
**Fix**: Add user to gpio group:
```bash
sudo usermod -a -G gpio $USER
```
Then log out and back in, or reboot.

## 4. Test Startup Script Manually

Run the startup script directly to see errors:

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
./start_led_controller.sh
```

This will show you exactly where it's failing.

## 5. Check File Permissions

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
ls -la
chmod +x start_led_controller.sh
chmod +x led_controller.py
chmod +x update_from_github.sh
```

## 6. Verify Service File Paths

Check that paths in service file match your installation:

```bash
cat /etc/systemd/system/led-controller.service | grep -E "WorkingDirectory|ExecStart"
```

Compare with actual paths:
```bash
pwd
which python3
```

## 7. Test Python Script Directly

Try running the controller directly:

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
python3 led_controller.py
```

This will show any Python errors.

## 8. Check System Resources

```bash
df -h  # Check disk space
free -h  # Check memory
```

## 9. Enable More Verbose Logging

The startup script now logs extensively. Check:
- Systemd journal: `sudo journalctl -u led-controller.service -f`
- Controller log: `tail -f ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log`

## 10. Run Diagnostic Script

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
chmod +x check_service.sh
./check_service.sh
```

This will check all common issues automatically.

