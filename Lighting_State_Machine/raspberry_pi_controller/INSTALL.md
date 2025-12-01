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
WorkingDirectory=/home/pi/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
ExecStart=/home/pi/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/start_led_controller.sh
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
cat /var/log/led_controller_update.log
```

### 5. Test the Startup Script

Test the startup script manually:

```bash
./start_led_controller.sh
```

Press Ctrl+C to stop it. Check the log:

```bash
cat /var/log/led_controller.log
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

1. **On Startup**: The `start_led_controller.sh` script runs first
2. **Update Check**: It executes `update_from_github.sh`
3. **GitHub Download**: Downloads latest `led_controller.py` from GitHub
4. **Validation**: Verifies the downloaded file is valid Python
5. **Backup**: Creates a backup of the old file before replacing
6. **Launch**: Starts the LED controller with the updated file

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
cat /var/log/led_controller_update.log
```

### View Controller Logs
```bash
cat /var/log/led_controller.log
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

1. Check service status:
   ```bash
   sudo systemctl status led-controller.service
   ```

2. Check logs:
   ```bash
   sudo journalctl -u led-controller.service -n 50
   ```

3. Verify file paths in service file match your installation

4. Check file permissions:
   ```bash
   ls -la ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/
   ```

### Update Fails

1. Check internet connectivity:
   ```bash
   ping -c 3 8.8.8.8
   ```

2. Verify GitHub URL is correct in `update_from_github.sh`

3. Check update log:
   ```bash
   cat /var/log/led_controller_update.log
   ```

4. Test update script manually:
   ```bash
   ./update_from_github.sh
   ```

### Controller Crashes

1. Check controller logs:
   ```bash
   cat /var/log/led_controller.log
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

To manually trigger an update without restarting:

```bash
cd ~/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller
./update_from_github.sh
sudo systemctl restart led-controller.service
```

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
0 3 * * * /home/pi/Arduino_codebase/Lighting_State_Machine/raspberry_pi_controller/update_from_github.sh && sudo systemctl restart led-controller.service
```

This updates daily at 3 AM.

### Change Log Locations

Edit the log file paths in:
- `update_from_github.sh`: `LOG_FILE` variable
- `start_led_controller.sh`: `LOG_FILE` variable

### Change Service User

Edit `led-controller.service` and change:
```ini
User=pi
```

To your desired user.

## Support

For issues or questions:
1. Check the log files
2. Verify all paths are correct
3. Ensure internet connectivity
4. Verify GitHub repository is accessible

