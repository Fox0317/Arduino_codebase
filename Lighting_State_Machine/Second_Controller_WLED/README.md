# Second Controller Setup with WLED

This directory contains the configuration and setup instructions for the second ESP32 controller that will handle LEDs 1001-2000.

## Hardware Requirements

- ESP32 development board (Nano ESP32, ESP32 DevKit, etc.)
- Power supply capable of handling 1000 LEDs
- WS2812B LED strips (or compatible)

## Software Setup

### 1. Install WLED

1. Download the latest WLED binary from [WLED Releases](https://github.com/Aircoookie/WLED/releases)
2. Flash it to your second ESP32 using the WLED web installer or esptool

### 2. Configure WLED

1. Power on the second ESP32
2. Connect to the WLED WiFi network (usually "WLED-AP")
3. Open a web browser and go to `http://4.3.2.1`
4. Configure your WiFi settings
5. Note the IP address assigned to the second controller

### 3. LED Configuration

1. In WLED settings, set the number of LEDs to **2000** (total for both strips)
2. Set LED type to WS2812B
3. Configure **two LED pins**:
   - **LED Pin 1**: Usually GPIO 2 (for first 1000 LEDs)
   - **LED Pin 2**: Usually GPIO 4 (for second 1000 LEDs)
4. Set color order to RGB
5. Configure power management if needed
6. **Enable Multi-Strip Support**:
   - Go to WLED Settings → LED Preferences
   - Set "Max Segments" to 2 or higher
   - Ensure "Multi-Strip" is enabled

### 4. Update Main Controller

1. Open `Lighting_State_Machine_ESP32_LIFX.ino`
2. Update the `wledIP` variable with your second controller's IP address
3. Update WiFi credentials (`ssid` and `password`)

## Wiring Diagram

```
Main ESP32 (LEDs 1-1000)     Second ESP32 (LEDs 1001-2000)
     |                                |
     |                                |
  LED_PIN1 (GPIO 10)              LED_PIN1 (GPIO 2)
     |                                |
  LED_PIN2 (GPIO 18)              LED_PIN2 (GPIO 4)
     |                                |
     |                                |
  [LED Strip 1-1000]            [LED Strip 1001-2000]
```

**Note**: The second ESP32 now controls both LED strips (1001-2000) using two pins for multi-strip support.

## Performance Benefits

- **Before**: 2000 LEDs controlled by 1 ESP32 = Slow refresh rate
- **After**: 1000 LEDs per ESP32 = 2x faster refresh rate
- **Estimated improvement**: 30-50% faster animations and smoother effects

## Troubleshooting

1. **Second controller not responding**: Check IP address and WiFi connection
2. **LEDs not syncing**: Verify both controllers are on the same network
3. **Performance still slow**: Check power supply and LED strip quality

## Advanced Configuration

- Enable UDP sync for even better performance
- Configure custom effects in WLED
- Set up power management for large installations
