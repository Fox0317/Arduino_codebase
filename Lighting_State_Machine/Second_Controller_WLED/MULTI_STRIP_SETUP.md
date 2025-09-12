# WLED Multi-Strip Setup Guide

This guide explains how to configure WLED to support multiple LED strips, enabling the switch to control all 2000 LEDs across both controllers.

## Overview

With multi-strip support, your WLED controller can handle two separate LED strips:
- **Strip 1**: LEDs 1001-1500 (connected to GPIO 2)
- **Strip 2**: LEDs 1501-2000 (connected to GPIO 4)

This allows the main switch to control the entire lighting system seamlessly.

## Hardware Requirements

- **ESP32 Development Board**: Nano ESP32, ESP32 DevKit, etc.
- **Two LED Strips**: WS2812B or compatible (500 LEDs each)
- **Power Supply**: Capable of handling 1000 LEDs total
- **Wiring**: Connections for two data pins and power

## Wiring Configuration

```
ESP32 GPIO 2 ──── [LED Strip 1: LEDs 1001-1500]
ESP32 GPIO 4 ──── [LED Strip 2: LEDs 1501-2000]
ESP32 5V ──────── [Power Supply]
ESP32 GND ─────── [Common Ground]
```

## WLED Configuration Steps

### 1. Basic WLED Setup

1. **Flash WLED** to your ESP32
2. **Connect to WLED WiFi** network
3. **Access WLED interface** at `http://4.3.2.1`
4. **Configure WiFi** settings

### 2. LED Configuration

1. **Go to Config → LED Preferences**
2. **Set Total LED Count**: 2000
3. **Enable Multi-Strip Support**:
   - Set "Max Segments" to 2 or higher
   - Enable "Multi-Strip" option
4. **Configure LED Pin 1**:
   - Set to GPIO 2
   - LED count: 1000
   - Start: 0
   - Stop: 1000
5. **Configure LED Pin 2**:
   - Set to GPIO 4
   - LED count: 1000
   - Start: 1000
   - Stop: 2000

### 3. Segment Configuration

1. **Segment 0** (First Strip):
   - Start: 0
   - Stop: 1000
   - Pin: GPIO 2
   - Effects: All available
   
2. **Segment 1** (Second Strip):
   - Start: 1000
   - Stop: 2000
   - Pin: GPIO 4
   - Effects: All available

### 4. Power Management

1. **Current Limiting**: Enable if needed
2. **Maximum Brightness**: Set to 255
3. **Power Supply Voltage**: Configure for your setup
4. **Power Injection**: Consider for long strips

## Switch Integration

### Switch Behavior with Multi-Strip

| Switch Position | Main ESP32 | WLED Controller | Total LEDs |
|----------------|------------|-----------------|------------|
| 1 (Left)       | LEDs 1-1000 | LEDs 1001-1500 | 1500 LEDs |
| 2 (Center)     | LEDs 1-1000 | LEDs 1001-2000 | 2000 LEDs |
| 3 (Right)      | LEDs 501-1000 | LEDs 1501-2000 | 1500 LEDs |

### JSON Configuration

The main controller sends JSON commands like this:

```json
{
  "on": true,
  "bri": 255,
  "seg": [
    {
      "id": 0,
      "start": 0,
      "stop": 1000,
      "on": true,
      "bri": 255,
      "fx": 0
    },
    {
      "id": 1,
      "start": 1000,
      "stop": 2000,
      "on": true,
      "bri": 255,
      "fx": 0
    }
  ]
}
```

## Testing Multi-Strip Setup

### 1. Individual Strip Test

1. **Test Strip 1**: Set segment 0 to solid color
2. **Test Strip 2**: Set segment 1 to solid color
3. **Verify**: Each strip responds independently

### 2. Combined Test

1. **Set both segments** to same effect
2. **Verify synchronization** between strips
3. **Check performance** and smoothness

### 3. Switch Integration Test

1. **Move switch** to different positions
2. **Monitor Serial output** for status
3. **Verify LED response** matches switch position

## Troubleshooting

### Common Issues

1. **Only one strip working**:
   - Check GPIO pin assignments
   - Verify segment configuration
   - Check power supply capacity

2. **Strips not syncing**:
   - Verify segment start/stop values
   - Check effect synchronization
   - Monitor network latency

3. **Performance issues**:
   - Check power supply quality
   - Verify LED strip specifications
   - Monitor ESP32 temperature

### Debug Steps

1. **WLED Interface**:
   - Check segment configuration
   - Monitor power consumption
   - Verify pin assignments

2. **Serial Monitor**:
   - Check switch status messages
   - Monitor WLED communication
   - Look for error messages

3. **Network Testing**:
   - Ping WLED controller
   - Test HTTP requests
   - Check WiFi signal strength

## Advanced Configuration

### 1. Custom Effects

- Create custom effects in WLED
- Synchronize effects across segments
- Implement pattern sharing

### 2. Power Management

- Implement automatic brightness adjustment
- Add temperature monitoring
- Create power-saving modes

### 3. Network Optimization

- Use static IP addresses
- Enable UDP sync for better performance
- Configure QoS settings

## Performance Benefits

### Before (Single Controller)
- 2000 LEDs on 1 ESP32
- Slow refresh rate
- Limited effects complexity

### After (Multi-Strip WLED)
- 1000 LEDs per strip
- 2x faster refresh rate
- Independent strip control
- Switch-based power management

## Maintenance

### Regular Tasks
- Monitor power consumption
- Check LED strip connections
- Clean LED strips and connections
- Update WLED firmware

### Performance Monitoring
- Track refresh rates
- Monitor power usage
- Check synchronization quality
- Measure effect smoothness

## Conclusion

The multi-strip WLED configuration provides:
- **Complete Control**: Switch controls all 2000 LEDs
- **Better Performance**: Faster refresh rates
- **Flexible Power Management**: Selective strip activation
- **Professional Quality**: Smooth, synchronized animations

This setup transforms your lighting system into a professional-grade installation with full control and optimal performance.
