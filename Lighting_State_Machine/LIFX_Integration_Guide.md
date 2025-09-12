# LIFX Integration Guide

This guide explains how to set up LIFX bulb synchronization with your ESP32 lighting controller. The system will automatically sync your LED strip patterns with your LIFX bulbs over WiFi.

## Overview

The LIFX integration allows your ESP32 to:
- **Discover LIFX devices** automatically on startup
- **Sync colors** between LED strips and LIFX bulbs
- **Match brightness** levels across all devices
- **Turn off/on** LIFX bulbs with LED strip modes
- **Create unified lighting** experiences

## Prerequisites

### Required Hardware
- Arduino Nano ESP32
- WS2812B LED strip
- KY-040 Rotary Encoder
- LIFX bulbs (any model)
- WiFi network

### Required Libraries
- FastLED
- ArduinoJson
- WiFi (built-in)
- HTTPClient (built-in)

## Setup Instructions

### 1. Get LIFX API Token

1. **Visit LIFX Cloud**: Go to https://cloud.lifx.com/settings/tokens
2. **Create Token**: Click "Create New Token"
3. **Name Token**: Give it a descriptive name (e.g., "ESP32 Lighting Controller")
4. **Copy Token**: Save the generated token securely

### 2. Configure ESP32 Settings

Edit the configuration in `Lighting_State_Machine_ESP32_LIFX.ino`:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// LIFX Configuration
const char* lifxToken = "YOUR_LIFX_TOKEN"; // Paste your token here
const char* lifxApiUrl = "https://api.lifx.com/v1";
bool lifxEnabled = true;
bool lifxSyncEnabled = true;
```

### 3. Upload and Test

1. **Upload the sketch** to your ESP32
2. **Open Serial Monitor** (115200 baud)
3. **Check for LIFX discovery** messages
4. **Test mode changes** to see LIFX sync

## How LIFX Sync Works

### Device Discovery
```
ESP32 Boot → Connect WiFi → Discover LIFX Devices → Store Device Info
```

### Color Synchronization
```
LED Strip Update → Calculate Average Color → Convert to HSBK → Update LIFX
```

### Sync Process
1. **Average LED Color**: Calculates average color from all LEDs
2. **Color Conversion**: Converts RGB to LIFX HSBK format
3. **API Call**: Sends HTTP PUT request to LIFX API
4. **Device Update**: Updates all connected LIFX bulbs

## Configuration Options

### LIFX Settings
```cpp
bool lifxEnabled = true;           // Enable/disable LIFX integration
bool lifxSyncEnabled = true;       // Enable/disable color sync
unsigned long LIFX_SYNC_INTERVAL = 1000; // Sync every second
#define MAX_LIFX_DEVICES 10        // Maximum number of LIFX devices
```

### Customization Options
- **Disable LIFX**: Set `lifxEnabled = false`
- **Disable Sync**: Set `lifxSyncEnabled = false`
- **Change sync frequency**: Modify `LIFX_SYNC_INTERVAL`
- **Increase device limit**: Change `MAX_LIFX_DEVICES`

## LIFX API Integration

### Device Discovery
The ESP32 automatically discovers LIFX devices using the LIFX API:
```
GET https://api.lifx.com/v1/lights/all
Authorization: Bearer YOUR_TOKEN
```

### Color Updates
Updates LIFX bulb colors using:
```
PUT https://api.lifx.com/v1/lights/id:DEVICE_ID/state
{
  "color": "hue:32768 saturation:100 brightness:50 kelvin:3500",
  "power": "on"
}
```

### Power Control
Turns LIFX bulbs on/off:
```
PUT https://api.lifx.com/v1/lights/id:DEVICE_ID/state
{
  "power": "off"
}
```

## Color Conversion

### RGB to HSBK
The system converts LED strip RGB colors to LIFX HSBK format:

- **Hue**: 0-65535 (16-bit precision)
- **Saturation**: 0-100%
- **Brightness**: 0-100%
- **Kelvin**: 2500-9000K (warm to cool white)

### Conversion Functions
```cpp
uint16_t rgbToHue(CRGB color);      // RGB to LIFX hue
uint8_t rgbToSaturation(CRGB color); // RGB to LIFX saturation
```

## Mode-Specific Behavior

### Solid Color Modes
- **White, Red, Yellow, etc.**: Direct color mapping
- **LIFX bulbs**: Match exact LED strip colors
- **Brightness**: Synchronized across all devices

### Animation Modes
- **Rainbow, Aurora, Fire**: Average color calculation
- **LIFX bulbs**: Follow the average color of LED strip
- **Smooth transitions**: Color changes are smoothed

### Special Modes
- **OFF Mode**: Turns off all LIFX bulbs
- **Breathing Mode**: LIFX bulbs follow brightness changes
- **Twinkle Mode**: LIFX bulbs follow average twinkle color

## Troubleshooting

### Common Issues

#### 1. LIFX Devices Not Found
- **Symptom**: "Failed to discover LIFX devices"
- **Solutions**:
  - Check LIFX token is correct
  - Verify WiFi connection
  - Ensure LIFX bulbs are online
  - Check LIFX API status

#### 2. Color Sync Issues
- **Symptom**: LIFX colors don't match LED strip
- **Solutions**:
  - Check color conversion functions
  - Verify LIFX bulb compatibility
  - Adjust color distance threshold

#### 3. API Rate Limits
- **Symptom**: "HTTP request failed"
- **Solutions**:
  - Increase sync interval
  - Reduce number of devices
  - Check LIFX API limits

#### 4. WiFi Connection Issues
- **Symptom**: "WiFi not connected"
- **Solutions**:
  - Check SSID/password
  - Verify network availability
  - Check ESP32 WiFi capabilities

### Debug Information
The ESP32 outputs detailed debug information:
```
Lighting State Machine ESP32 with LIFX Starting...
Connecting to WiFi.....
Connected to WiFi. IP: 192.168.1.100
Discovering LIFX devices...
Found LIFX device: Living Room
Found LIFX device: Bedroom
Total LIFX devices found: 2
Mode changed to: 3
Syncing LIFX devices...
```

## Advanced Features

### Multiple Device Support
- **Automatic Discovery**: Finds all LIFX devices on network
- **Individual Control**: Updates each device separately
- **Connection Tracking**: Monitors device online status

### Color Optimization
- **Change Detection**: Only updates when colors change significantly
- **Smooth Transitions**: Prevents flickering
- **Brightness Mapping**: Maps LED brightness to LIFX brightness

### Error Handling
- **Connection Retry**: Automatically retries failed connections
- **Device Recovery**: Reconnects to offline devices
- **API Error Handling**: Graceful handling of API errors

## Performance Considerations

### Network Usage
- **API Calls**: ~1 call per second per device
- **Data Usage**: Minimal (JSON payloads)
- **Latency**: Depends on network speed

### Memory Usage
- **Device Storage**: ~50 bytes per device
- **JSON Parsing**: ~8KB for device discovery
- **Color Conversion**: Minimal CPU usage

### Optimization Tips
1. **Reduce sync frequency** for better performance
2. **Limit device count** if experiencing issues
3. **Use stable WiFi** connection
4. **Monitor API rate limits**

## Security Considerations

### API Token Security
- **Keep token private**: Don't share your LIFX token
- **Token permissions**: LIFX tokens have full device control
- **Token rotation**: Consider rotating tokens periodically

### Network Security
- **Use secure WiFi**: Ensure your network is secure
- **Local network**: All communication stays on local network
- **No cloud dependency**: Works without internet (except for LIFX API)

## Example Usage Scenarios

### Home Theater Setup
- **LED strip**: Behind TV for ambient lighting
- **LIFX bulbs**: Ceiling lights for room atmosphere
- **Sync effect**: Creates immersive viewing experience

### Party Mode
- **LED strip**: Wall accent lighting
- **LIFX bulbs**: Main room lighting
- **Sync effect**: Coordinated party atmosphere

### Relaxation Mode
- **LED strip**: Subtle wall lighting
- **LIFX bulbs**: Soft room illumination
- **Sync effect**: Calming, unified lighting

## Troubleshooting Checklist

- [ ] LIFX token is correct and valid
- [ ] WiFi credentials are correct
- [ ] LIFX bulbs are online and connected
- [ ] ESP32 has stable power supply
- [ ] Network allows HTTP requests
- [ ] Serial monitor shows successful discovery
- [ ] Color changes are being detected
- [ ] API calls are successful

This integration creates a seamless lighting experience across your LED strips and LIFX bulbs, allowing you to control your entire lighting setup from a single encoder! 