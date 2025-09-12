`# ESP32 OTA (Over-The-Air) Update Setup

This guide explains how to set up automatic firmware updates from GitHub for your ESP32 lighting controller.

## Overview

The ESP32 version of the lighting state machine can automatically download and install firmware updates from your GitHub repository. This allows you to:

- **Update firmware remotely** without physical access
- **Deploy new features** automatically on restart
- **Fix bugs** without manual intervention
- **Version control** your firmware through GitHub releases

## Prerequisites

### Required Libraries
Install these libraries in Arduino IDE:
- **FastLED** - For LED control
- **ArduinoJson** - For parsing GitHub API responses
- **WiFi** - Built into ESP32 core
- **HTTPClient** - Built into ESP32 core
- **Update** - Built into ESP32 core

### Hardware Requirements
- Arduino Nano ESP32
- WS2812B LED strip
- KY-040 Rotary Encoder
- WiFi network access

## Setup Instructions

### 1. Configure WiFi Settings

Edit the WiFi configuration in `Lighting_State_Machine_ESP32.ino`:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```

### 2. Configure GitHub Repository

Update the GitHub repository settings:

```cpp
// GitHub OTA Configuration
const char* githubRepo = "YOUR_GITHUB_USERNAME/Arduino_codebase";
const char* githubBranch = "main";
const char* firmwareFile = "Lighting_State_Machine/Lighting_State_Machine_ESP32.ino.bin";
```

### 3. Create GitHub Releases

To enable OTA updates, you need to create GitHub releases with compiled firmware:

#### Option A: Manual Release Creation
1. Compile the ESP32 sketch in Arduino IDE
2. Find the `.bin` file in the temporary build folder
3. Create a new GitHub release
4. Upload the `.bin` file as a release asset
5. Tag the release (e.g., "v1.0.1")

#### Option B: Automated Release (Recommended)
Create a GitHub Action to automatically build and release firmware:

```yaml
# .github/workflows/build-firmware.yml
name: Build ESP32 Firmware

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Arduino CLI
      uses: arduino/setup-arduino-cli@v1
      
    - name: Build ESP32 Firmware
      run: |
        arduino-cli core install esp32:esp32
        arduino-cli compile --fqbn esp32:esp32:esp32s3 Lighting_State_Machine/Lighting_State_Machine_ESP32.ino
        
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: Lighting_State_Machine/Lighting_State_Machine_ESP32.ino.bin
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 4. Update Version Number

When you want to release a new version:

1. **Update the version in code:**
```cpp
String currentVersion = "1.0.1"; // Change this
```

2. **Create a new Git tag:**
```bash
git tag v1.0.1
git push origin v1.0.1
```

3. **The GitHub Action will automatically:**
   - Build the new firmware
   - Create a release with the `.bin` file
   - Tag it with the version number

## How OTA Updates Work

### Update Process
1. **Startup Check**: ESP32 checks for updates when it boots
2. **Periodic Checks**: Checks every 5 minutes while running
3. **Version Comparison**: Compares current version with latest GitHub release
4. **Download**: Downloads the new firmware if available
5. **Install**: Installs the firmware using ESP32's Update library
6. **Restart**: Automatically reboots with the new firmware

### Update Flow
```
ESP32 Boot → Connect WiFi → Check GitHub API → Compare Versions
     ↓
New Version? → Download .bin → Install → Restart
     ↓
No Update → Continue Normal Operation
```

## Configuration Options

### Update Settings
```cpp
// OTA Update Settings
bool checkForUpdates = true;                    // Enable/disable OTA
unsigned long UPDATE_CHECK_INTERVAL = 300000;   // Check every 5 minutes
String currentVersion = "1.0.0";               // Current firmware version
```

### Customization
- **Disable OTA**: Set `checkForUpdates = false`
- **Change check interval**: Modify `UPDATE_CHECK_INTERVAL`
- **Manual updates only**: Set interval to a very large number

## Troubleshooting

### Common Issues

#### 1. WiFi Connection Fails
- **Symptom**: "Failed to connect to WiFi"
- **Solution**: Check SSID/password and network availability

#### 2. GitHub API Errors
- **Symptom**: "HTTP request failed"
- **Solution**: Verify repository name and internet connection

#### 3. Update Fails
- **Symptom**: "Update failed!"
- **Solution**: Check firmware file size and ESP32 memory

#### 4. Version Mismatch
- **Symptom**: Updates not detected
- **Solution**: Ensure version strings match exactly

### Debug Information
The ESP32 outputs detailed debug information via Serial:
```
Lighting State Machine ESP32 Starting...
Connecting to WiFi.....
Connected to WiFi. IP: 192.168.1.100
Checking for firmware updates...
Latest version: v1.0.1
Current version: 1.0.0
New version available! Downloading...
Downloading 1234567 bytes...
Update successful! Rebooting...
```

## Security Considerations

### Public Repository
- Anyone can download your firmware
- Consider making repository private for sensitive projects

### Authentication
- GitHub releases are public by default
- Use private repositories for secure deployments

### Version Control
- Always test firmware before releasing
- Use semantic versioning (e.g., v1.0.1, v1.1.0, v2.0.0)

## Advanced Features

### Multiple Device Support
You can deploy the same firmware to multiple ESP32 devices:
- All devices check the same GitHub repository
- Updates are applied to all devices automatically
- Each device maintains its own version tracking

### Rollback Capability
To implement rollback functionality:
1. Store previous firmware version
2. Add rollback trigger (e.g., long button press)
3. Implement firmware validation

### Custom Update Server
For enterprise deployments, you can modify the code to use a custom update server instead of GitHub.

## Best Practices

1. **Test thoroughly** before releasing new versions
2. **Use semantic versioning** for clear version tracking
3. **Document changes** in release notes
4. **Monitor update success** via Serial output
5. **Keep backup firmware** for emergency recovery
6. **Validate firmware** before installation

## Example Workflow

1. **Develop new feature** in Arduino IDE
2. **Test locally** on ESP32
3. **Update version number** in code
4. **Commit and push** to GitHub
5. **Create new tag** for release
6. **GitHub Action** builds and releases firmware
7. **ESP32 devices** automatically update on next restart

This system provides a robust, automated way to keep your ESP32 lighting controllers up-to-date with the latest firmware! 