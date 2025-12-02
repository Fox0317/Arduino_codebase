# LED Controller Auto-Update and Startup Setup

This guide explains how to set up automatic updates from GitHub and launch the LED controller on Raspberry Pi startup.

## Prerequisites

- Raspberry Pi with Raspberry Pi OS
- Python 3 installed
- `curl` installed (usually pre-installed)
- Git repository access
- Internet connectivity

## Installation Steps

### 1. Update Configuration

Edit `update_from_github.sh` and update the GitHub repository information:

```bash
GITHUB_REPO="YOUR_GITHUB_USERNAME/Arduino_codebase"
GITHUB_BRANCH="main"
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

### 2. Update Service File Path

Edit `led-controller.service` and update the paths to match your installation:

```ini
WorkingDirectory=/home/Fox0317/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
ExecStart=/home/Fox0317/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/start_led_controller.sh
```

Adjust these paths to match where you've installed the files on your Raspberry Pi.

### 3. Make Scripts Executable

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
chmod +x update_from_github.sh
chmod +x start_led_controller.sh
chmod +x led_controller.py
```

### 4. Test the Update Script

Test the update script manually first:

```bash
./update_from_github.sh
```

Check the log file to verify it works:

```bash
cat led_controller_update.log
```

### 5. Test the Startup Script

Test the startup script manually:

```bash
./start_led_controller.sh
```

Press Ctrl+C to stop it. Check the log:

```bash
cat led_controller.log
```

### 6. Install Systemd Service

Copy the service file to systemd directory:

```bash
sudo cp led-controller.service /etc/systemd/system/
```

Reload systemd to recognize the new service:

```bash
sudo systemctl daemon-reload
```

### 7. Enable and Start the Service

Enable the service to start on boot:

```bash
sudo systemctl enable led-controller.service
```

Start the service immediately:

```bash
sudo systemctl start led-controller.service
```

### 8. Check Service Status

Verify the service is running:

```bash
sudo systemctl status led-controller.service
```

View recent logs:

```bash
sudo journalctl -u led-controller.service -f
```

## How It Works

### Update Process

**Important**: Updates only run on system boot, not on service restarts. This prevents constant update checks.

1. **On Boot**: The `start_led_controller.sh` script runs first
2. **Boot Detection**: Checks system uptime to determine if this is a fresh boot
3. **Update Check**: Only executes `update_from_github.sh` if it's a fresh boot
4. **GitHub Download**: Downloads latest `led_controller.py` from GitHub
5. **Validation**: Verifies the downloaded file is valid Python
6. **Backup**: Creates a backup of the old file before replacing
7. **Flag Creation**: Creates a flag file to prevent updates on service restarts
8. **Launch**: Starts the LED controller with the updated file

**Note**: If you manually restart the service (`sudo systemctl restart`), the update will NOT run. Updates only occur on actual system reboots.

### Service Management

The systemd service:
- **Auto-starts** on boot
- **Auto-restarts** if the script crashes
- **Waits for network** before starting
- **Logs output** to systemd journal

## Useful Commands

### View Service Status
```bash
sudo systemctl status led-controller.service
```

### View Service Logs
```bash
sudo journalctl -u led-controller.service -f
```

### View Update Logs
```bash
# Log file is in the script directory
cat ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller_update.log
```

### View Controller Logs
```bash
# Log file is in the script directory
cat ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log
```

### Stop the Service
```bash
sudo systemctl stop led-controller.service
```

### Restart the Service
```bash
sudo systemctl restart led-controller.service
```

### Disable Auto-Start
```bash
sudo systemctl disable led-controller.service
```

## Troubleshooting

### Service Won't Start

**First, run the diagnostic script:**
```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
chmod +x check_service.sh
./check_service.sh
```

**Manual troubleshooting steps:**

1. Check service status:
   ```bash
   sudo systemctl status led-controller.service
   ```

2. Check detailed logs:
   ```bash
   sudo journalctl -u led-controller.service -n 50 -l
   ```

3. Verify service is enabled:
   ```bash
   systemctl is-enabled led-controller.service
   ```
   If not enabled, run: `sudo systemctl enable led-controller.service`

4. Check file permissions:
   ```bash
   cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
   ls -la
   chmod +x start_led_controller.sh
   chmod +x led_controller.py
   chmod +x update_from_github.sh
   ```

5. Verify user is in gpio group (required for GPIO access):
   ```bash
   groups
   ```
   If `gpio` is not listed, add it:
   ```bash
   sudo usermod -a -G gpio $USER
   ```
   Then log out and back in, or reboot.

6. Test startup script manually:
   ```bash
   cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
   ./start_led_controller.sh
   ```
   This will show any errors that occur during startup.

7. Verify Python dependencies:
   ```bash
   python3 -c "import RPi.GPIO; print('GPIO OK')"
   ```
   If this fails, install: `pip3 install RPi.GPIO`

8. Reload systemd after making changes:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart led-controller.service
   ```

### Update Fails

1. Check internet connectivity:
   ```bash
   ping -c 3 8.8.8.8
   ```

2. Verify GitHub URL is correct in `update_from_github.sh`

3. Check update log:
   ```bash
   cat ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller_update.log
   ```

4. Test update script manually:
   ```bash
   ./update_from_github.sh
   ```

### Controller Crashes

1. Check controller logs:
   ```bash
   cat ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log
   ```

2. Check systemd logs:
   ```bash
   sudo journalctl -u led-controller.service -n 100
   ```

3. Verify Python dependencies are installed:
   ```bash
   pip3 list | grep -i rpi
   ```

### Network Issues

The service waits for network connectivity before starting. If your network is slow to connect:

1. Check network status:
   ```bash
   systemctl status NetworkManager
   ```

2. Increase wait time in service file (add to `[Service]` section):
   ```ini
   ExecStartPre=/bin/sleep 30
   ```

## Manual Update

To manually trigger an update without restarting (bypasses boot-only restriction):

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
./update_from_github.sh
sudo systemctl restart led-controller.service
```

**Alternative**: To force an update on the next service restart (without running update script manually), delete the boot flag file:

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
rm -f .update_on_boot_flag
sudo systemctl restart led-controller.service
```

This will make the system think it's a fresh boot and run the update automatically.

## Backup Files

The update script creates backups before updating. Backups are stored in the same directory as `led_controller.py` with names like:

```
led_controller.py.backup.20240101_120000
```

Only the last 5 backups are kept automatically.

## Security Considerations

- The service runs as the `pi` user (change in service file if needed)
- Update script validates downloaded files before replacing
- Backups are created before any updates
- Logs are stored in `/var/log/` for monitoring

## Customization

### Change Update Frequency

Currently updates only on restart. To add periodic updates, create a cron job:

```bash
crontab -e
```

Add:
```
0 3 * * * /home/Fox0317/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/update_from_github.sh && sudo systemctl restart led-controller.service
```

This updates daily at 3 AM.

### Change Log Locations

Log files are stored in the script directory by default (where the user has write permissions). To change log locations, edit the log file paths in:
- `update_from_github.sh`: `LOG_FILE` variable
- `start_led_controller.sh`: `LOG_FILE` variable

By default, logs are stored in:
- `~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller_update.log`
- `~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/led_controller.log`

### Change Service User

Edit `led-controller.service` and change:
```ini
User=Fox0317
```

To your desired user.

## Support

For issues or questions:
1. Check the log files
2. Verify all paths are correct
3. Ensure internet connectivity
4. Verify GitHub repository is accessible

