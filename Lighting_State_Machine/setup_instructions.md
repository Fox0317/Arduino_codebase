# LED Controller System Setup Instructions

This system uses a Raspberry Pi to calculate LED animations and sends data to three ESP32 controllers, each controlling 1000 LEDs.

## System Architecture

```
Raspberry Pi (Main Controller)
├── Calculates LED animations
├── Sends data via UDP to ESP32s
└── Controls 3 ESP32s simultaneously

ESP32 #1 (Strip 0)
├── Receives data from Pi
├── Controls LEDs 1-1000
└── Connected to GPIO 10

ESP32 #2 (Strip 1)  
├── Receives data from Pi
├── Controls LEDs 1001-2000
└── Connected to GPIO 18

ESP32 #3 (Strip 2)
├── Receives data from Pi  
├── Controls LEDs 2001-3000
└── Connected to GPIO 19
```

## Hardware Requirements

### Raspberry Pi
- Raspberry Pi 4 (recommended) or Pi 3B+
- WiFi connection
- Python 3.7+
- Required Python packages: `numpy`

### ESP32 Controllers (3x)
- ESP32 development boards
- FastLED library installed
- WiFi connection
- LED strips: WS2812B (NeoPixel) compatible

### LED Strips
- 3x WS2812B LED strips (1000 LEDs each)
- Total: 3000 LEDs
- Power: ~180W at full brightness (5V, 60mA per LED)

## Software Setup

### 1. Raspberry Pi Setup

1. Install required packages:
```bash
sudo apt update
sudo apt install python3-pip
pip3 install numpy
```

2. Configure network settings:
```bash
# Edit the config file
nano config/network_config.py
# Update WiFi credentials and ESP32 IP addresses
```

3. Run the controller:
```bash
python3 raspberry_pi_controller/led_controller.py
```

### 2. ESP32 Setup

For each ESP32 (you'll need 3):

1. Install FastLED library in Arduino IDE
2. Copy `esp32_config.h` and modify for each ESP32:
   - ESP32 #1: `STRIP_ID=0`, `LED_PIN=10`
   - ESP32 #2: `STRIP_ID=1`, `LED_PIN=18`  
   - ESP32 #3: `STRIP_ID=2`, `LED_PIN=19`
3. Update WiFi credentials in the config
4. Upload the code to each ESP32

### 3. Network Configuration

1. Assign static IPs to ESP32s in your router:
   - ESP32 #1: 192.168.1.101
   - ESP32 #2: 192.168.1.102
   - ESP32 #3: 192.168.1.103
   - Raspberry Pi: 192.168.1.100

2. Ensure all devices are on the same WiFi network

## Usage

### Starting the System

1. Power on all ESP32s
2. Wait for them to connect to WiFi
3. Start the Raspberry Pi controller:
```bash
python3 led_controller.py
```

### Control Commands

Once running, you can use these commands:
- `m <mode>` - Set LED mode (0-16)
- `b <brightness>` - Set brightness (0-255)
- `s <strip> <on/off>` - Control individual strips
- `q` - Quit

### LED Modes

- 0: White
- 1: Red
- 2: Yellow
- 3: Green
- 4: Cyan
- 5: Blue
- 6: Magenta
- 7: Solid Color (cycling)
- 8: Rainbow
- 9: Fire
- 10: Aurora
- 11: Rainbow Chase
- 12: Comet
- 13: Twinkle
- 14: Wave
- 15: Chase
- 16: Breathing

## Troubleshooting

### ESP32 Not Receiving Data
- Check WiFi connection
- Verify IP address assignment
- Check UDP port 8888 is not blocked
- Ensure strip ID matches configuration

### Raspberry Pi Connection Issues
- Verify all ESP32s are on the same network
- Check IP addresses in config file
- Test with `ping` command to each ESP32

### LED Strip Issues
- Check power supply (5V, sufficient amperage)
- Verify data pin connections
- Check for loose connections
- Test with simple FastLED examples first

### Performance Issues
- Reduce animation complexity
- Increase `SEND_INTERVAL` in config
- Check network latency
- Ensure stable WiFi connection

## Power Requirements

- **Per LED**: 5V, 60mA (at full brightness)
- **Per Strip (1000 LEDs)**: 5V, 60A
- **Total System**: 5V, 180A

**Important**: Use appropriate power supplies and consider power injection for long strips.

## Safety Notes

- Use proper power supplies with adequate current capacity
- Implement fuses or circuit breakers
- Ensure good ventilation for power supplies
- Use appropriate wire gauge for high current
- Consider power injection points for long strips

## Customization

### Adding New Animations
1. Add new mode to `LEDModes` class in `led_controller.py`
2. Implement animation function
3. Add case to `calculate_led_data()` method

### Changing LED Count
1. Update `NUM_LEDS_PER_STRIP` in config files
2. Modify packet size calculations
3. Update ESP32 code accordingly

### Network Optimization
- Use wired Ethernet for Raspberry Pi if possible
- Consider dedicated WiFi network for LED system
- Monitor network bandwidth usage
