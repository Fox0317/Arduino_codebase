# Lighting State Machine with KY-040 Encoder

A comprehensive Arduino project that creates a state machine for controlling LED lighting patterns using a KY-040 rotary encoder. The system cycles through multiple lighting modes and includes both manual and automatic mode switching.

## Features

- **18 Different Lighting Modes**: From simple solid colors to complex animations
- **KY-040 Encoder Control**: Rotate to change modes, press button for auto mode
- **Auto Mode**: Automatically cycles through all lighting patterns
- **Smooth Transitions**: Interrupt-driven encoder handling for responsive control
- **Serial Debug Output**: Monitor mode changes and system status

## Hardware Requirements

- Arduino Uno (or compatible)
- WS2812B LED strip (60 LEDs)
- KY-040 Rotary Encoder Module
- 5V Power Supply (for LED strip)
- Breadboard and jumper wires

## Wiring Diagram

### KY-040 Encoder Connections
```
KY-040    Arduino
CLK   →   Pin 2
DT    →   Pin 3
SW    →   Pin 4
VCC   →   5V
GND   →   GND
```

### WS2812B LED Strip Connections
```
LED Strip    Arduino
Data     →   Pin 7
VCC      →   5V (external power supply)
GND      →   GND (shared with Arduino)
```

## Lighting Modes

1. **OFF** - All LEDs turned off
2. **Solid Color** - Single color that slowly changes hue
3. **Rainbow** - Full spectrum rainbow pattern
4. **Fire** - Realistic fire simulation with heat diffusion
5. **Twinkle** - Random twinkling stars effect
6. **Wave** - Sine wave pattern with color variation
7. **Chase** - Moving light that follows the strip
8. **Breathing** - Smooth brightness pulsing
9. **Rainbow Chase** - Multiple rainbow lights moving
10. **Comet** - Single light with trailing effect

## Controls

### Encoder Rotation
- **Clockwise**: Next lighting mode
- **Counter-clockwise**: Previous lighting mode
- Modes wrap around (last mode → first mode)

### Encoder Button
- **Press**: Toggle auto mode on/off
- **Auto Mode**: Automatically cycles through all modes every 10 seconds

## Configuration

### LED Configuration
```cpp
#define NUM_LEDS 60        // Number of LEDs in your strip
#define LED_PIN 7          // Arduino pin connected to LED data
```

## Lighting Modes

1. **OFF** - All LEDs turned off
2. **White** - Solid white color
3. **Solid Color** - Single color that slowly changes hue
4. **Red** - Solid red color
5. **Yellow** - Solid yellow color
6. **Green** - Solid green color
7. **Cyan** - Solid cyan color
8. **Blue** - Solid blue color
9. **Magenta** - Solid magenta color
10. **Aurora** - Aurora borealis with flowing green and purple hues
11. **Rainbow** - Full spectrum rainbow pattern
12. **Fire** - Realistic fire simulation with heat diffusion
13. **Twinkle** - Random twinkling stars effect
14. **Wave** - Sine wave pattern with color variation
15. **Chase** - Moving light that follows the strip
16. **Breathing** - Smooth brightness pulsing
17. **Rainbow Chase** - Multiple rainbow lights moving
18. **Comet** - Single light with trailing effect

### Encoder Configuration
```cpp
#define ENCODER_CLK 2      // Encoder CLK pin
#define ENCODER_DT 3       // Encoder DT pin  
#define ENCODER_SW 4       // Encoder button pin
```

### Auto Mode Settings
```cpp
unsigned long modeChangeInterval = 10000; // 10 seconds between auto mode changes
```

## Installation

1. **Install Required Libraries**
   - FastLED library (available in Arduino Library Manager)

2. **Upload the Code**
   - Open `Lighting_State_Machine.ino` in Arduino IDE
   - Select your board and port
   - Upload the code

3. **Connect Hardware**
   - Wire the KY-040 encoder according to the diagram above
   - Connect the LED strip to the specified pins
   - Power the LED strip with an external 5V supply

4. **Test the System**
   - Open Serial Monitor (9600 baud) to see debug output
   - Rotate the encoder to change modes
   - Press the encoder button to toggle auto mode

## Troubleshooting

### Encoder Issues
- **Erratic behavior**: Check wiring and ensure proper pull-up resistors
- **Missing steps**: Verify interrupt pins are correctly configured
- **Button not responding**: Check button wiring and debounce settings

### LED Issues
- **No lights**: Verify power supply and data pin connection
- **Wrong colors**: Check LED strip type (WS2812B vs other variants)
- **Flickering**: Ensure adequate power supply for LED count

### Performance Issues
- **Slow animations**: Reduce `NUM_LEDS` or increase delay in loop
- **Memory issues**: Optimize animation arrays for smaller LED counts

## Customization

### Adding New Modes
1. Add new mode to the `LightingMode` enum
2. Create a new mode function (e.g., `modeCustom()`)
3. Add case to the switch statement in `updateLightingMode()`
4. Update `NUM_MODES` constant

### Modifying Animation Speed
- Adjust `EVERY_N_MILLISECONDS()` values in mode functions
- Change the main loop delay (currently 20ms for 50 FPS)

### Changing LED Count
- Update `NUM_LEDS` define
- Modify animation arrays if needed
- Adjust power supply requirements

## Technical Details

### Interrupt Handling
- Uses hardware interrupts for encoder CLK and SW pins
- Debouncing implemented to prevent false triggers
- Non-blocking design for smooth animations

### Memory Usage
- Static arrays for fire heat and twinkle states
- Efficient FastLED library for LED control
- Minimal RAM usage for smooth operation

### Power Requirements
- Arduino: 5V via USB or external supply
- LED Strip: 5V external supply (60mA per LED at full brightness)
- Encoder: Minimal power draw

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this project. 