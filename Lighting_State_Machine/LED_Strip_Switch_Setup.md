# LED Strip Switch Setup

This document explains how to add an on-off-on switch to control which LED strips are active on your main controller.

## Overview

The switch allows you to selectively control which LED strips are powered across **both controllers**:
- **Position 1**: Only first LED strips active (Main ESP32: LEDs 1-1000, WLED: LEDs 1001-1500)
- **Position 2 (Center)**: All LED strips active (Main ESP32: LEDs 1-1000, WLED: LEDs 1001-2000)
- **Position 3**: Only second LED strips active (Main ESP32: LEDs 501-1000, WLED: LEDs 1501-2000)

## Hardware Requirements

- **On-Off-On Switch**: SPDT (Single Pole Double Throw) switch
- **Resistors**: 2x 10kΩ pull-up resistors (optional, since we use INPUT_PULLUP)
- **Wiring**: Jumper wires or breadboard connections

## Wiring Diagram

```
ESP32 GPIO 5 ────┐
                 │
ESP32 GPIO 6 ────┤─── On-Off-On Switch
                 │
ESP32 GND ───────┘
```

### Switch Pinout

```
Switch Position 1 (Left):  GPIO 5 connected to GND
Switch Position 2 (Center): Both GPIO 5 and GPIO 6 floating (HIGH due to INPUT_PULLUP)
Switch Position 3 (Right): GPIO 6 connected to GND
```

## Switch Behavior

| Switch Position | GPIO 5 | GPIO 6 | Active Strips | Description |
|----------------|--------|--------|---------------|-------------|
| 1 (Left)       | LOW    | HIGH   | First strips  | Main: LEDs 1-1000, WLED: LEDs 1001-1500 |
| 2 (Center)     | HIGH   | HIGH   | All strips    | Main: LEDs 1-1000, WLED: LEDs 1001-2000 |
| 3 (Right)      | HIGH   | LOW    | Second strips | Main: LEDs 501-1000, WLED: LEDs 1501-2000 |

## Code Implementation

The system automatically detects switch changes and reconfigures the LED strips:

```cpp
// Switch pins configured with INPUT_PULLUP
#define STRIP1_SWITCH_PIN 5  // GPIO 5
#define STRIP2_SWITCH_PIN 6  // GPIO 6

// Switch states are checked every 50ms
void checkLEDStripSwitches() {
  bool switch1Low = !digitalRead(STRIP1_SWITCH_PIN);
  bool switch2Low = !digitalRead(STRIP2_SWITCH_PIN);
  
  // Configure strips based on switch position
  if (switch1Low && !switch2Low) {
    // Position 1: Strip 1 only
    strip1Active = true;
    strip2Active = false;
  } else if (!switch1Low && switch2Low) {
    // Position 3: Strip 2 only
    strip1Active = false;
    strip2Active = true;
  } else {
    // Position 2: Both strips
    strip1Active = true;
    strip2Active = true;
  }
}
```

## Installation Steps

1. **Connect the switch**:
   - Connect one terminal to ESP32 GPIO 5
   - Connect another terminal to ESP32 GPIO 6
   - Connect the common terminal to ESP32 GND

2. **Upload the modified code**:
   - The switch pins are automatically configured
   - Switch detection starts immediately

3. **Test the switch**:
   - Move switch to different positions
   - Check Serial Monitor for status messages
   - Verify LED strips respond correctly

## Troubleshooting

### Switch not responding
- Check wiring connections
- Verify switch is properly grounded
- Check Serial Monitor for error messages

### LEDs not updating
- Ensure switch is making good contact
- Check GPIO pin assignments
- Verify INPUT_PULLUP configuration

### Unexpected behavior
- Check switch type (should be SPDT on-off-on)
- Verify switch is properly mounted
- Check for loose connections

## Advanced Configuration

### Custom Pin Assignment
You can change the GPIO pins by modifying these lines:
```cpp
#define STRIP1_SWITCH_PIN 5  // Change to desired GPIO
#define STRIP2_SWITCH_PIN 6  // Change to desired GPIO
```

### Switch Debouncing
The current implementation checks switches every 50ms. You can adjust this timing:
```cpp
if (millis() - lastSwitchCheck > 50) { // Change 50 to desired delay
  checkLEDStripSwitches();
  lastSwitchCheck = millis();
}
```

### Multiple Switches
You can add more switches by following the same pattern:
```cpp
#define STRIP3_SWITCH_PIN 7  // Additional switch pin
bool strip3Active = true;    // Additional strip state
```

## Safety Considerations

- **Power Management**: Ensure your power supply can handle the current draw
- **Switch Rating**: Use a switch rated for your voltage/current requirements
- **Grounding**: Proper grounding is essential for reliable operation
- **Heat Dissipation**: LED strips can generate heat; ensure proper ventilation

## Performance Impact

- **Switch Detection**: Minimal impact (checks every 50ms)
- **LED Reconfiguration**: Only occurs when switch position changes
- **Memory Usage**: Negligible additional memory usage
- **Processing**: Minimal additional processing overhead

## Integration with Dual Controller

This switch system works alongside the dual-controller setup with **multi-strip support**:
- **Main Controller**: Switch controls local LED strips (1-1000)
- **WLED Controller**: Switch controls both WLED strips (1001-2000) using multi-strip functionality
- **Synchronization**: Both controllers remain in sync regardless of switch position
- **Multi-Strip Control**: The switch now controls **all 2000 LEDs** across both controllers

### Multi-Strip WLED Configuration

The WLED controller is configured with two LED strips:
- **Strip 1**: LEDs 1001-1500 (controlled by switch position 1 and 2)
- **Strip 2**: LEDs 1501-2000 (controlled by switch position 2 and 3)

This provides seamless control over your entire lighting system from a single switch.

## Conclusion

The LED strip switch provides flexible control over your lighting system while maintaining all existing functionality. The automatic detection and reconfiguration ensure seamless operation without manual intervention.
