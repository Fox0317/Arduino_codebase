# Dual Controller Setup Guide

This guide will help you implement a dual-controller solution to improve the refresh rate of your 2000 LED setup by splitting control between two ESP32 controllers.

## Overview

**Problem**: Single ESP32 controlling 2000 LEDs results in slow refresh rates due to the time required to write data to all strips.

**Solution**: Split control between two ESP32 controllers:
- **Main Controller**: Handles LEDs 1-1000 and coordinates the system
- **Secondary Controller**: Runs WLED and handles LEDs 1001-2000

**Expected Results**: 30-50% improvement in refresh rate and smoother animations.

## Hardware Requirements

### Main Controller
- ESP32 development board (your existing one)
- Power supply for 1000 LEDs
- WS2812B LED strips (LEDs 1-1000)

### Secondary Controller
- ESP32 development board (Nano ESP32, ESP32 DevKit, etc.)
- Power supply for 1000 LEDs
- WS2812B LED strips (LEDs 1001-2000)
- Micro USB cable for programming

## Software Setup

### Step 1: Prepare Secondary ESP32 with WLED

1. **Download WLED**
   - Go to [WLED Releases](https://github.com/Aircoookie/WLED/releases)
   - Download the latest `.bin` file for ESP32

2. **Flash WLED**
   - Use the [WLED Web Installer](https://install.wled.me) or esptool
   - Connect your secondary ESP32 via USB
   - Flash the WLED binary

3. **Initial WLED Configuration**
   - Power on the secondary ESP32
   - Connect to the "WLED-AP" WiFi network
   - Open a web browser and go to `http://4.3.2.1`
   - Configure your WiFi settings
   - Note the IP address assigned to the controller

### Step 2: Configure WLED Settings

1. **LED Configuration**
   - Set number of LEDs to 1000
   - Set LED type to WS2812B
   - Configure LED pin (usually GPIO 2)
   - Set color order to RGB

2. **Power Management**
   - Enable current limiting if needed
   - Set maximum brightness to 255
   - Configure power supply voltage

3. **Network Settings**
   - Ensure both controllers are on the same WiFi network
   - Note the IP address for the main controller

### Step 3: Update Main Controller Code

1. **Modify the main Arduino sketch**:
   ```cpp
   // Update these variables in your main controller
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* wledIP = "192.168.1.100";  // Your WLED controller's IP
   ```

2. **Install required libraries**:
   - WiFi (built into ESP32)
   - HTTPClient (built into ESP32)
   - ArduinoJson (already included)

### Step 4: Test Communication

1. **Run the test script**:
   ```bash
   python test_communication.py
   ```

2. **Verify connectivity**:
   - Both controllers should be on the same network
   - Main controller should be able to reach WLED controller
   - Test basic commands and effects

## Wiring Diagram

```
Power Supply 1 (LEDs 1-1000)     Power Supply 2 (LEDs 1001-2000)
           |                                |
           |                                |
    Main ESP32                        Secondary ESP32
    (GPIO 10, 18)                    (GPIO 2)
           |                                |
           |                                |
    [LED Strip 1-1000]              [LED Strip 1001-2000]
```

## Performance Optimization

### 1. Network Optimization
- Use 5GHz WiFi if available
- Ensure both controllers have strong WiFi signal
- Consider using static IP addresses

### 2. LED Strip Optimization
- Use high-quality power supplies
- Minimize voltage drop with proper wire gauge
- Consider using power injection for long strips

### 3. Code Optimization
- Update second controller every 100ms (already configured)
- Use efficient JSON payloads
- Implement error handling for network issues

## Troubleshooting

### Common Issues

1. **Second controller not responding**
   - Check WiFi connection
   - Verify IP address
   - Ensure WLED is running properly

2. **LEDs not syncing**
   - Check network latency
   - Verify both controllers are on same network
   - Test with simple effects first

3. **Performance still slow**
   - Check power supply quality
   - Verify LED strip specifications
   - Monitor network performance

### Debug Steps

1. **Serial Monitor Output**
   - Check for WiFi connection status
   - Monitor second controller communication
   - Look for error messages

2. **Network Testing**
   - Ping between controllers
   - Test HTTP requests manually
   - Check WiFi signal strength

3. **LED Testing**
   - Test each controller independently
   - Verify power supply voltage
   - Check for loose connections

## Advanced Features

### 1. UDP Sync (Optional)
- Enable UDP sync in WLED for even better performance
- Configure main controller to send UDP packets
- Reduces HTTP overhead

### 2. Custom Effects
- Create custom effects in WLED
- Synchronize complex animations
- Implement pattern sharing

### 3. Power Management
- Implement automatic brightness adjustment
- Add motion sensors for automatic control
- Create scheduling features

## Expected Results

After implementing this dual-controller solution:

- **Refresh Rate**: 30-50% improvement
- **Animation Smoothness**: Significantly smoother
- **System Responsiveness**: Faster mode changes
- **Overall Performance**: More professional lighting system

## Maintenance

### Regular Tasks
- Monitor WiFi signal strength
- Check for firmware updates
- Clean LED strips and connections
- Verify power supply voltages

### Updates
- Keep WLED updated to latest version
- Monitor for Arduino library updates
- Test new features before deployment

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all connections and settings
3. Test each controller independently
4. Check network connectivity
5. Review error messages in Serial Monitor

## Conclusion

This dual-controller solution should significantly improve your LED system's performance. The investment in a second ESP32 and the time to set it up will be well worth it for the improved refresh rate and smoother animations.

Remember to test thoroughly at each step and don't hesitate to start with simple effects before moving to complex animations.
