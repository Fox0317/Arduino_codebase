# LIFX LAN Protocol Controller

A clean, focused implementation of the LIFX LAN protocol for ESP32, based on the official LIFX LAN documentation at https://lan.developer.lifx.com/docs/communicating-with-device.

## Overview

This script implements direct communication with LIFX smart bulbs using the LIFX LAN protocol over UDP on port 56700. It provides a complete solution for discovering, controlling, and monitoring LIFX devices on your local network.

## Features

- **Device Discovery**: Automatically finds LIFX bulbs on your network
- **Power Control**: Turn bulbs on/off
- **Color Control**: Set custom colors using HSB values
- **White Light**: Set bulbs to white light with adjustable brightness
- **Connection Testing**: Echo requests to verify device connectivity
- **Real-time Status**: Monitor device state and connection status
- **Serial Interface**: Easy-to-use command interface

## Hardware Requirements

- ESP32 development board
- WiFi network with LIFX bulbs connected
- USB cable for programming and serial communication

## Software Requirements

- Arduino IDE with ESP32 board support
- Required libraries:
  - `WiFi.h` (included with ESP32)
  - `WiFiUdp.h` (included with ESP32)
  - `ArduinoJson.h` (install via Library Manager)

## Installation

1. **Install ESP32 Board Support**:
   - Open Arduino IDE
   - Go to File → Preferences
   - Add `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json` to Additional Board Manager URLs
   - Go to Tools → Board → Boards Manager
   - Search for "ESP32" and install "ESP32 by Espressif Systems"

2. **Install Required Libraries**:
   - Go to Tools → Manage Libraries
   - Search for "ArduinoJson" and install "ArduinoJson by Benoit Blanchon"

3. **Configure WiFi Settings**:
   - Open `LIFX_LAN_Controller.ino`
   - Update the WiFi credentials:
     ```cpp
     const char* ssid = "YOUR_WIFI_SSID";
     const char* password = "YOUR_WIFI_PASSWORD";
     ```

4. **Upload the Code**:
   - Select your ESP32 board from Tools → Board
   - Select the correct port from Tools → Port
   - Click Upload

## Usage

### Initial Setup

1. **Power on your ESP32** with the uploaded code
2. **Open the Serial Monitor** (Tools → Serial Monitor)
3. **Set baud rate to 115200**
4. **Wait for initialization** - you should see:
   ```
   === LIFX LAN Protocol Controller ===
   Based on official LIFX LAN documentation
   https://lan.developer.lifx.com/docs/communicating-with-device
   
   Connecting to WiFi: YOUR_WIFI_SSID
   WiFi connected! IP: 192.168.1.XXX
   
   === Discovering LIFX Devices ===
   Sending LIFX discovery broadcast...
   Listening for device responses...
   Discovery complete. Found X devices.
   ```

### Available Commands

The controller provides a simple serial command interface:

#### 1. Device Discovery
```
discover
```
- Rediscover all LIFX devices on the network
- Resets the device list and performs a fresh discovery

#### 2. List Devices
```
list
```
- Display all discovered devices with their current state
- Shows device index, label, IP, power state, and color values

#### 3. Test Connection
```
echo <device_index>
```
- Send an echo request to test device connectivity
- Example: `echo 0` tests connection to device #0

#### 4. Power Control
```
power <device_index> <on/off>
```
- Turn a device on or off
- Examples:
  - `power 0 on` - Turn device #0 on
  - `power 1 off` - Turn device #1 off

#### 5. Color Control
```
color <device_index> <hue> <sat> <bright>
```
- Set custom color using HSB values
- Hue: 0-65535 (0=red, 10923=green, 21845=blue, 32768=purple, 43691=orange, 54613=pink)
- Saturation: 0-65535 (0=white, 65535=full color)
- Brightness: 0-65535 (0=off, 65535=full brightness)
- Examples:
  - `color 0 0 65535 32768` - Red at 50% brightness
  - `color 1 10923 65535 65535` - Green at full brightness
  - `color 2 21845 32768 49152` - Blue at 75% brightness

#### 6. White Light
```
white <device_index> <bright>
```
- Set device to white light with specified brightness
- Brightness: 0-65535
- Examples:
  - `white 0 32768` - White light at 50% brightness
  - `white 1 65535` - White light at full brightness

## LIFX LAN Protocol Implementation

This implementation follows the official LIFX LAN protocol specification:

### Packet Structure
- **Frame Header** (16 bytes): Protocol version, source, addressing info
- **Frame Address** (16 bytes): Target MAC, response flags, sequence
- **Protocol Header** (12 bytes): Message type and reserved fields
- **Payload** (variable): Message-specific data

### Message Types
- `GetService` (2): Device discovery
- `StateService` (3): Device service response
- `SetPower` (21): Power control
- `SetColor` (102): Color control
- `EchoRequest` (58): Connection testing
- `StateLight` (107): Light state response

### Communication Flow
1. **Discovery**: Broadcast `GetService` with `tagged=1`
2. **Device Response**: Receive `StateService` with device info
3. **Control**: Send directed messages to specific device IP
4. **Status**: Receive state messages for current device status

## Troubleshooting

### Common Issues

#### 1. No Devices Found
**Symptoms**: Discovery finds 0 devices
**Solutions**:
- Ensure LIFX bulbs are powered on and connected to WiFi
- Check that ESP32 and bulbs are on the same network
- Verify WiFi credentials are correct
- Try running `discover` command multiple times

#### 2. Devices Found But Not Responding
**Symptoms**: Devices listed but commands don't work
**Solutions**:
- Use `echo <device_index>` to test connectivity
- Check if router blocks UDP broadcast packets
- Ensure bulbs are not in sleep mode
- Try power cycling the bulbs

#### 3. WiFi Connection Issues
**Symptoms**: "WiFi connection failed!"
**Solutions**:
- Verify SSID and password are correct
- Check WiFi signal strength
- Ensure network supports 2.4GHz (LIFX bulbs don't support 5GHz)
- Try moving ESP32 closer to router

#### 4. Serial Communication Issues
**Symptoms**: No response to commands
**Solutions**:
- Verify baud rate is set to 115200
- Check that correct port is selected
- Ensure line ending is set to "Newline" or "Both NL & CR"
- Try resetting the ESP32

### Debug Information

The script provides detailed debug output:
- Packet transmission status
- Received packet information
- Device state updates
- Network diagnostics

### Network Requirements

- **UDP Port 56700**: Must be open for LIFX communication
- **Broadcast Support**: Router must allow UDP broadcast packets
- **Local Network**: All devices must be on same subnet
- **WiFi Security**: WPA2 recommended (WPA3 may cause issues)

## Advanced Usage

### Custom Color Values

LIFX uses 16-bit color values (0-65535):

| Color | Hue Value |
|-------|-----------|
| Red | 0 |
| Orange | 5461 |
| Yellow | 10923 |
| Green | 16384 |
| Cyan | 21845 |
| Blue | 32768 |
| Purple | 38291 |
| Pink | 43691 |

### Integration with Other Projects

This controller can be integrated into larger projects:
- Home automation systems
- IoT lighting controllers
- Smart home hubs
- Custom lighting effects

### Extending Functionality

The modular design allows easy extension:
- Add new message types
- Implement additional device controls
- Create custom lighting patterns
- Add web interface

## Technical Details

### Memory Usage
- Packet buffer: 1024 bytes
- Device list: 10 devices × ~50 bytes each
- Total RAM usage: ~1.5KB

### Network Traffic
- Discovery: ~44 bytes per broadcast
- Control messages: ~50-100 bytes each
- State responses: ~50-200 bytes each

### Performance
- Discovery time: ~5 seconds
- Command response: <100ms
- Status updates: Every 30 seconds

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## References

- [LIFX LAN Protocol Documentation](https://lan.developer.lifx.com/docs/communicating-with-device)
- [LIFX Developer Portal](https://lan.developer.lifx.com/)
- [ESP32 WiFi Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html) 