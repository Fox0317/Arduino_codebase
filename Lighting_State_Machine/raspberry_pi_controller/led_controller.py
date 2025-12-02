#!/usr/bin/env python3
"""
Raspberry Pi LED Controller
Calculates LED pixel values and sends data to four ESP32 controllers
Each ESP32 controls 243 LEDs (1275 total) #
"""

import socket
import json
import time
import math
import random
import threading
from typing import List, Tuple
import RPi.GPIO as GPIO

# LED Configuration
NUM_LEDS_PER_STRIP = [243, 332, 282, 369]  # 243 LEDs per strip (732 bytes per packet)
NUM_STRIPS = 4
TOTAL_LEDS = sum(NUM_LEDS_PER_STRIP)


# ESP32 Controller IPs (update these with your actual IPs)
ESP32_IPS = [
    "192.168.8.100",  # ESP32 #0 - Receiver 00 (243 LEDs)
    "192.168.8.101",  # ESP32 #1 - Receiver 01 (243 LEDs) - Static IP
    "192.168.8.102",  # ESP32 #2 - Receiver 02 (243 LEDs)
    "192.168.8.103",  # ESP32 #3 - Receiver 03 (243 LEDs) - Update with actual IP
]

# Communication settings
UDP_PORT = 8888
SEND_INTERVAL = 0.05  # Send data every 50ms (20 FPS)

# KY-040 Encoder Configuration (matching ESP32 setup)
ENCODER_CLK_PIN = 17  # GPIO 17 (D2 equivalent)
ENCODER_DT_PIN = 18   # GPIO 18 (D3 equivalent) 
ENCODER_SW_PIN = 27   # GPIO 27 (D4 equivalent)

# SPDT Switch Configuration
SPDT_PIN_A = 22  # GPIO 22 - First switch position
SPDT_PIN_B = 23  # GPIO 23 - Second switch position




# Animation state
class AnimationState:
    def __init__(self):
        self.current_mode = 9
        self.brightness = 255
        self.hue = 0
        self.animation_step = 0
        
        # Initialize arrays for each strip with different lengths
        self.fire_heat = [[0] * count for count in NUM_LEDS_PER_STRIP]
        self.twinkle_state = [[random.randint(0, 255) for _ in range(count)] for count in NUM_LEDS_PER_STRIP]
        self.aurora_intensity = [[0] * count for count in NUM_LEDS_PER_STRIP]
        self.aurora_phase = 0
        self.aurora_hue = 96
        

# LED modes
class LEDModes:
    WHITE = 0
    RED = 1
    YELLOW = 2
    GREEN = 3
    CYAN = 4
    BLUE = 5
    MAGENTA = 6
    SOLID_COLOR = 7
    RAINBOW = 8
    FIRE = 9
    AURORA = 10
    TWINKLE = 11




class EncoderHandler:
    """Handles KY-040 rotary encoder input for mode selection and brightness control"""
    
    def __init__(self):
        # Encoder state tracking
        self.last_clk_state = None
        self.last_dt_state = None
        self.encoder_position = 0
        
        # Button state tracking
        self.button_pressed = False
        self.button_hold_start = None
        self.button_hold_duration = 0
        self.rotation_during_hold = False
        
        # Actions to return
        self.pending_actions = []
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ENCODER_CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENCODER_DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENCODER_SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Initialize encoder states
        self.last_clk_state = GPIO.input(ENCODER_CLK_PIN)
        self.last_dt_state = GPIO.input(ENCODER_DT_PIN)
        
        # Add event detection with reduced debounce for faster response
        GPIO.add_event_detect(ENCODER_CLK_PIN, GPIO.BOTH, callback=self._on_clk_change, bouncetime=1)
        GPIO.add_event_detect(ENCODER_SW_PIN, GPIO.BOTH, callback=self._on_button_change, bouncetime=25)
        
        print("Encoder handler initialized")
    
    def _on_clk_change(self, channel):
        """Called when CLK pin changes state"""
        current_clk = GPIO.input(ENCODER_CLK_PIN)
        current_dt = GPIO.input(ENCODER_DT_PIN)
        
        # Only process if CLK state actually changed
        if current_clk != self.last_clk_state:
            # Determine rotation direction based on DT state when CLK changes
            if current_dt != current_clk:
                # Clockwise rotation
                self.encoder_position += 1
                self.pending_actions.append("rotate_cw")
            else:
                # Counter-clockwise rotation
                self.encoder_position -= 1
                self.pending_actions.append("rotate_ccw")
            
            # Track rotation during button hold
            if self.button_pressed:
                self.rotation_during_hold = True
            
            # Update state
            self.last_clk_state = current_clk
            self.last_dt_state = current_dt
    
    def _on_button_change(self, channel):
        """Called when button state changes"""
        current_button = GPIO.input(ENCODER_SW_PIN)
        
        if current_button == 0 and not self.button_pressed:  # Button pressed (active low)
            self.button_pressed = True
            self.button_hold_start = time.time()
            self.rotation_during_hold = False
            print("Button pressed")
            
        elif current_button == 1 and self.button_pressed:  # Button released
            self.button_pressed = False
            if self.button_hold_start:
                self.button_hold_duration = time.time() - self.button_hold_start
                self.button_hold_start = None
                
                # Check if it was a button-only press (no rotation during hold)
                if not self.rotation_during_hold and self.button_hold_duration > 0.1:  # At least 100ms
                    self.pending_actions.append("button_press_only")
                
                self.rotation_during_hold = False
            print("Button released")
    
    def get_encoder_action(self):
        """Get the latest encoder action"""
        if not self.pending_actions:
            return None
        
        action = self.pending_actions.pop(0)
        
        if action == "rotate_cw":
            if self.button_pressed:
                return "brightness_up"
            else:
                # Only increment mode every 2 steps
                if self.encoder_position % 2 == 0:
                    return "mode_up"
        elif action == "rotate_ccw":
            if self.button_pressed:
                return "brightness_down"
            else:
                # Only decrement mode every 2 steps
                if self.encoder_position % 2 == 0:
                    return "mode_down"
        elif action == "button_press_only":
            return "button_press_only"
        
        return None
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        GPIO.cleanup()


class SPDTSwitchHandler:
    """Handles SPDT switch input monitoring"""
    
    def __init__(self):
        # Switch state tracking
        self.switch_position = None  # 'A', 'B', or None (invalid/transition)
        self.last_position = None
        self.position_changed = False
        
        # Setup GPIO pins as inputs with internal pullup resistors
        GPIO.setup(SPDT_PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(SPDT_PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Add event detection for both pins
        GPIO.add_event_detect(SPDT_PIN_A, GPIO.BOTH, callback=self._on_switch_change, bouncetime=50)
        GPIO.add_event_detect(SPDT_PIN_B, GPIO.BOTH, callback=self._on_switch_change, bouncetime=50)
        
        # Read initial state
        self._update_switch_position()
        
        print(f"SPDT Switch handler initialized - Current position: {self.switch_position}")
    
    def _on_switch_change(self, channel):
        """Called when either switch pin changes state"""
        self._update_switch_position()
    
    def _update_switch_position(self):
        """Update the current switch position based on GPIO readings"""
        pin_a_state = GPIO.input(SPDT_PIN_A)
        pin_b_state = GPIO.input(SPDT_PIN_B)
        
        # Determine switch position based on GPIO states
        # With pullup resistors, pins read HIGH (1) when not connected
        # and LOW (0) when connected to ground through the switch
        
        if pin_a_state == 0 and pin_b_state == 1:
            # Pin A is LOW (connected), Pin B is HIGH (not connected)
            new_position = 'A'
        elif pin_a_state == 1 and pin_b_state == 0:
            # Pin A is HIGH (not connected), Pin B is LOW (connected)
            new_position = 'B'
        elif pin_a_state == 1 and pin_b_state == 1:
            # Both pins HIGH - switch in center position or not connected
            new_position = None
        else:
            # Both pins LOW - invalid state (shouldn't happen with SPDT)
            new_position = None
        
        # Check if position changed
        if new_position != self.switch_position:
            self.last_position = self.switch_position
            self.switch_position = new_position
            self.position_changed = True
            print(f"SPDT Switch position changed: {self.last_position} -> {self.switch_position}")
    
    def get_switch_position(self):
        """Get current switch position"""
        return self.switch_position
    
    def has_position_changed(self):
        """Check if switch position has changed since last check"""
        if self.position_changed:
            self.position_changed = False
            return True
        return False
    
    def get_position_change(self):
        """Get the last position change (returns tuple of (old, new))"""
        if self.position_changed:
            self.position_changed = False
            return (self.last_position, self.switch_position)
        return None
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        GPIO.remove_event_detect(SPDT_PIN_A)
        GPIO.remove_event_detect(SPDT_PIN_B)


class LEDController:
    def __init__(self):
        self.state = AnimationState()
        self.sockets = []
        self.running = False
        self.strip_active = [True, True, True, True]  # All strips active by default
        self.encoder = EncoderHandler()  # Initialize encoder handler
        self.spdt_switch = SPDTSwitchHandler()  # Initialize SPDT switch handler
        
        # Initialize UDP sockets for each ESP32
        for i, ip in enumerate(ESP32_IPS):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1.0)
                self.sockets.append(sock)
                print(f"Initialized socket for ESP32 #{i+1} at {ip}")
            except Exception as e:
                print(f"Failed to initialize socket for ESP32 #{i+1}: {e}")
                self.sockets.append(None)

    def rgb_to_bytes(self, r: int, g: int, b: int) -> bytes:
        """Convert RGB values to bytes for transmission"""
        return bytes([r, g, b])
    
    

    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB"""
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
            
        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

    def mode_white(self, strip_index: int) -> List[bytes]:
        """White mode"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        for i in range(led_count):
            pixels.append(self.rgb_to_bytes(255, 255, 255))
        
        return pixels

    def mode_solid_color(self, strip_index: int) -> List[bytes]:
        """Solid color mode with cycling hue"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        r, g, b = self.hsv_to_rgb(self.state.hue, 1.0, 1.0)
        
        for i in range(led_count):
            pixels.append(self.rgb_to_bytes(r, g, b))
        
        return pixels

    def mode_rainbow(self, strip_index: int) -> List[bytes]:
        """Rainbow mode"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        for i in range(led_count):
            hue = (self.state.hue + i * 360 / led_count) % 360
            r, g, b = self.hsv_to_rgb(hue, 1.0, 1.0)
            pixels.append(self.rgb_to_bytes(r, g, b))
        return pixels

    def mode_fire(self, strip_index: int) -> List[bytes]:
        """Fire animation mode - more dynamic with better yellow/orange colors"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        # Cool down every cell (increased cooldown to prevent overheating)
        for i in range(led_count):
            self.state.fire_heat[strip_index][i] = max(0, self.state.fire_heat[strip_index][i] - random.randint(2, 4))
        
        # Heat diffusion (improved spreading with heat loss to prevent accumulation)
        new_heat = [0] * led_count
        for i in range(led_count):
            left_heat = self.state.fire_heat[strip_index][i-1] if i > 0 else 0
            right_heat = self.state.fire_heat[strip_index][i+1] if i < led_count-1 else 0
            current_heat = self.state.fire_heat[strip_index][i]
            
            # Weighted average with heat loss to prevent overheating
            new_heat[i] = (left_heat * 0.25 + current_heat * 0.4 + right_heat * 0.25)
            
            # Add more dynamic randomness with cooling bias
            if random.randint(0, 255) < 60:
                fluctuation = random.randint(-8, 8)  # Balanced heating/cooling
                new_heat[i] = max(0, min(200, new_heat[i] + fluctuation))  # Cap at 200 to prevent white
        
        self.state.fire_heat[strip_index] = new_heat
        
        # Add sparks with reduced intensity to prevent overheating
        if random.randint(0, 255) < 100:  # Reduced spark frequency
            spark_pos = random.randint(0, led_count-1)
            self.state.fire_heat[strip_index][spark_pos] = min(200, self.state.fire_heat[strip_index][spark_pos] + random.randint(80, 120))
        
        # Add multiple smaller sparks for more dynamic fire
        if random.randint(0, 255) < 80:  # Reduced frequency
            for _ in range(2):  # Add 2 smaller sparks
                spark_pos = random.randint(0, led_count-1)
                self.state.fire_heat[strip_index][spark_pos] = min(200, self.state.fire_heat[strip_index][spark_pos] + random.randint(40, 80))
        
        # Convert heat to colors (prevent white, focus on yellow/orange)
        for i in range(led_count):
            heat = self.state.fire_heat[strip_index][i]
            if heat < 50:
                # Black to red transition
                r = min(255, heat * 5)
                g = 0
                b = 0
            elif heat < 100:
                # Red to orange transition
                r = 255
                g = min(255, (heat - 50) * 5)
                b = 0
            elif heat < 150:
                # Orange to yellow transition (extended yellow range)
                r = 255
                g = 255
                b = min(100, (heat - 100) * 2)  # Limited blue to prevent white
            else:
                # Yellow to bright yellow (no white)
                r = 255
                g = 255
                b = min(150, 100 + (heat - 150) * 1)  # Cap blue to prevent white
            
            pixels.append(self.rgb_to_bytes(int(r), int(g), int(b)))
        
        return pixels

    def mode_aurora(self, strip_index: int) -> List[bytes]:
        """Aurora borealis animation"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        for i in range(led_count):
            # Create wave patterns
            wave1 = int(127 * (1 + math.sin((self.state.aurora_phase + i * 2) * math.pi / 128)))
            wave2 = int(127 * (1 + math.sin((self.state.aurora_phase * 0.6 + i * 3) * math.pi / 128)))
            wave3 = int(127 * (1 + math.sin((self.state.aurora_phase * 0.3 + i * 1) * math.pi / 128)))
            
            combined_wave = (wave1 * 2 + wave2 + wave3) // 4
            self.state.aurora_intensity[strip_index][i] = combined_wave
            
            # Aurora colors (fully saturated purple, green, magenta)
            aurora_colors = [(160, 32, 240), (0, 255, 0), (255, 0, 255)]
            color_position = combined_wave / 255.0
            color_index = int(color_position * (len(aurora_colors) - 1))
            
            if color_index < len(aurora_colors) - 1:
                blend_factor = color_position * (len(aurora_colors) - 1) - color_index
                c1 = aurora_colors[color_index]
                c2 = aurora_colors[color_index + 1]
                r = int(c1[0] + (c2[0] - c1[0]) * blend_factor)
                g = int(c1[1] + (c2[1] - c1[1]) * blend_factor)
                b = int(c1[2] + (c2[2] - c1[2]) * blend_factor)
            else:
                r, g, b = aurora_colors[color_index]
            
            # Add variation
            r += random.randint(-12, 12)
            g += random.randint(-12, 12)
            b += random.randint(-12, 12)
            
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            pixels.append(self.rgb_to_bytes(r, g, b))
        
        return pixels

    def mode_twinkle(self, strip_index: int) -> List[bytes]:
        """Twinkle animation"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        for i in range(led_count):
            if random.randint(0, 255) < 20:
                self.state.twinkle_state[strip_index][i] = random.randint(0, 255)
                hue = random.randint(0, 360)
                r, g, b = self.hsv_to_rgb(hue, 1.0, 1.0)
                pixels.append(self.rgb_to_bytes(r, g, b))
            else:
                # Fade existing twinkles
                if self.state.twinkle_state[strip_index][i] > 0:
                    self.state.twinkle_state[strip_index][i] = max(0, self.state.twinkle_state[strip_index][i] - 20)
                    brightness = self.state.twinkle_state[strip_index][i] / 255.0
                    r, g, b = self.hsv_to_rgb(0, 0, brightness)
                    pixels.append(self.rgb_to_bytes(int(r), int(g), int(b)))
                else:
                    pixels.append(self.rgb_to_bytes(0, 0, 0))
        
        return pixels


    def mode_color(self, strip_index: int, r_base: int, g_base: int, b_base: int) -> List[bytes]:
        """Color mode with fixed brightness"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        for i in range(led_count):
            pixels.append(self.rgb_to_bytes(r_base, g_base, b_base))
        
        return pixels

    def calculate_led_data(self, strip_index: int) -> List[bytes]:
        """Calculate LED data for a specific strip"""
        if not self.strip_active[strip_index]:
            return [self.rgb_to_bytes(0, 0, 0) for _ in range(NUM_LEDS_PER_STRIP[strip_index])]
        
        mode = self.state.current_mode
        
        if mode == LEDModes.WHITE:
            return self.mode_white(strip_index)
        elif mode == LEDModes.RED:
            return self.mode_color(strip_index, 255, 0, 0)  # Red
        elif mode == LEDModes.YELLOW:
            return self.mode_color(strip_index, 255, 255, 0)  # Yellow
        elif mode == LEDModes.GREEN:
            return self.mode_color(strip_index, 0, 255, 0)  # Green
        elif mode == LEDModes.CYAN:
            return self.mode_color(strip_index, 0, 255, 255)  # Cyan
        elif mode == LEDModes.BLUE:
            return self.mode_color(strip_index, 0, 0, 255)  # Blue
        elif mode == LEDModes.MAGENTA:
            return self.mode_color(strip_index, 255, 0, 255)  # Magenta
        elif mode == LEDModes.SOLID_COLOR:
            return self.mode_solid_color(strip_index)
        elif mode == LEDModes.RAINBOW:
            return self.mode_rainbow(strip_index)
        elif mode == LEDModes.FIRE:
            return self.mode_fire(strip_index)
        elif mode == LEDModes.AURORA:
            return self.mode_aurora(strip_index)
        elif mode == LEDModes.TWINKLE:
            return self.mode_twinkle(strip_index)
        else:
            return self.mode_white(strip_index)

    def send_data_to_esp32(self, strip_index: int, led_data: List[bytes]):
        """Send LED data to specific ESP32"""
        if strip_index >= len(self.sockets) or self.sockets[strip_index] is None:
            return False
        
        try:
            # Get SPDT switch status
            spdt_position = self.spdt_switch.get_switch_position()
            spdt_status = 0  # Default: no position
            if spdt_position == 'A':
                spdt_status = 1  # Position A
            elif spdt_position == 'B':
                spdt_status = 2  # Position B
            
            # Special case: ESP32_receiver_01 (strip_index 1) has backwards SPDT switch
            if strip_index == 1:
                if spdt_position == 'A':
                    spdt_status = 2  # Position A mapped to 2 for ESP32_01
                elif spdt_position == 'B':
                    spdt_status = 1  # Position B mapped to 1 for ESP32_01
            
            # Create packet: [strip_index, brightness, spdt_status, led_data...]
            # spdt_status: 0=None/Center, 1=Position A, 2=Position B
            packet = bytearray()
            packet.append(strip_index)
            packet.append(self.state.brightness)
            packet.append(spdt_status)  # Add SPDT switch status
            
            for pixel in led_data:
                packet.extend(pixel)
            
            # Send to ESP32
            self.sockets[strip_index].sendto(packet, (ESP32_IPS[strip_index], UDP_PORT))
            
            # Debug: Print SPDT status occasionally (every 100 packets to avoid spam)
            if hasattr(self, '_packet_count'):
                self._packet_count += 1
            else:
                self._packet_count = 1
            
            if self._packet_count % 100 == 0:
                print(f"ESP32 #{strip_index + 1}: SPDT status = {spdt_status} ({spdt_position})")
            
            return True
        except Exception as e:
            print(f"Failed to send data to ESP32 #{strip_index + 1}: {e}")
            return False

    def update_animation_state(self):
        """Update animation state variables"""
        self.state.animation_step += 1
        
        # Update hue for color cycling
        if self.state.current_mode in [LEDModes.SOLID_COLOR, LEDModes.RAINBOW]:
            self.state.hue = (self.state.hue + 1) % 360
        
        # Update aurora phase
        if self.state.current_mode == LEDModes.AURORA:
            self.state.aurora_phase = (self.state.aurora_phase + 1) % 1000
        

    def run_animation_loop(self):
        """Main animation loop"""
        print("Starting LED animation loop...")
        self.running = True
        
        # Diagnostic variables
        frame_count = 0
        packet_count = 0
        last_diag_time = time.time()
        
        while self.running:
            start_time = time.time()
            
            # Handle encoder input
            self.handle_encoder_input()
            
            # Handle SPDT switch input
            self.handle_spdt_switch_input()
            
            # Calculate and send data for each strip
            for strip_index in range(NUM_STRIPS):
                led_data = self.calculate_led_data(strip_index)
                if self.send_data_to_esp32(strip_index, led_data):
                    packet_count += 1
            
            # Update animation state
            self.update_animation_state()
            
            # Count frames
            frame_count += 1
            
            # Print diagnostics every second
            current_time = time.time()
            if current_time - last_diag_time >= 1.0:
                print(f"Pi Stats - Frames/sec: {frame_count}, Packets/sec: {packet_count}")
                frame_count = 0
                packet_count = 0
                last_diag_time = current_time
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, SEND_INTERVAL - elapsed)
            time.sleep(sleep_time)

    def handle_encoder_input(self):
        """Handle encoder input for mode selection and brightness control"""
        action = self.encoder.get_encoder_action()
        
        if action == "mode_up":
            self.state.current_mode = (self.state.current_mode + 1) % 12
            print(f"Mode changed to: {self.state.current_mode}")
        elif action == "mode_down":
            self.state.current_mode = (self.state.current_mode - 1) % 12
            print(f"Mode changed to: {self.state.current_mode}")
        elif action == "brightness_up":
            self.state.brightness = min(255, self.state.brightness + 12)
            print(f"Brightness increased to: {self.state.brightness}")
        elif action == "brightness_down":
            self.state.brightness = max(0, self.state.brightness - 12)
            print(f"Brightness decreased to: {self.state.brightness}")
        elif action == "button_press_only":
            # Button press only - no action for now
            print("Button pressed")

    def handle_spdt_switch_input(self):
        """Handle SPDT switch input"""
        if self.spdt_switch.has_position_changed():
            position_change = self.spdt_switch.get_position_change()
            if position_change:
                old_pos, new_pos = position_change
                print(f"SPDT Switch: {old_pos} -> {new_pos}")
                
                # Add functionality based on switch position here
                # For example, you could:
                # - Change LED modes based on switch position
                # - Enable/disable certain features
                # - Control different LED strips
                
                if new_pos == 'A':
                    print("SPDT Switch in position A - Feature A enabled")
                    # Add your functionality for position A here
                elif new_pos == 'B':
                    print("SPDT Switch in position B - Feature B enabled")
                    # Add your functionality for position B here
                elif new_pos is None:
                    print("SPDT Switch in center position - No specific feature")

    def set_mode(self, mode: int):
        """Set LED mode"""
        self.state.current_mode = mode
        print(f"Mode changed to: {mode}")

    def set_brightness(self, brightness: int):
        """Set brightness (0-255)"""
        self.state.brightness = max(0, min(255, brightness))
        print(f"Brightness set to: {self.state.brightness}")

    def set_strip_active(self, strip_index: int, active: bool):
        """Set strip active state"""
        if 0 <= strip_index < NUM_STRIPS:
            self.strip_active[strip_index] = active
            print(f"Strip {strip_index + 1} {'activated' if active else 'deactivated'}")
    

    def stop(self):
        """Stop the animation loop"""
        self.running = False
        for sock in self.sockets:
            if sock:
                sock.close()
        self.encoder.cleanup()  # Cleanup encoder GPIO resources
        self.spdt_switch.cleanup()  # Cleanup SPDT switch GPIO resources

def main():
    """Main function"""
    controller = LEDController()
    
    try:
        # Start animation loop in separate thread
        animation_thread = threading.Thread(target=controller.run_animation_loop)
        animation_thread.daemon = True
        animation_thread.start()
        
        
        # Simple command interface
        print("LED Controller started. Commands:")
        print("m <mode> - Set mode (0-16)")
        print("b <brightness> - Set brightness (0-255)")
        print("s <strip> <on/off> - Set strip active state")
        print("sw - Check SPDT switch status")
        print("q - Quit")
        print("\nEncoder Controls:")
        print("- Rotate encoder: Change mode (0-16)")
        print("- Hold button + rotate: Adjust brightness")
        print("- Press button only: No action")
        print("\nLED Configuration:")
        print(f"- Strip 1: {NUM_LEDS_PER_STRIP[0]} LEDs")
        print(f"- Strip 2: {NUM_LEDS_PER_STRIP[1]} LEDs")
        print(f"- Strip 3: {NUM_LEDS_PER_STRIP[2]} LEDs")
        print(f"- Strip 4: {NUM_LEDS_PER_STRIP[3]} LEDs")
        print(f"- Total: {TOTAL_LEDS} LEDs")
        print("\nUDP Packet Structure:")
        print("- Byte 0: Strip index (0-3)")
        print("- Byte 1: Brightness (0-255)")
        print("- Byte 2: SPDT status (0=None, 1=Position A, 2=Position B)")
        print("- Bytes 3+: LED data (RGB per LED)")
        
        while True:
            try:
                command = input("> ").strip().split()
                if not command:
                    continue
                
                if command[0] == 'q':
                    break
                elif command[0] == 'm' and len(command) > 1:
                    controller.set_mode(int(command[1]))
                elif command[0] == 'b' and len(command) > 1:
                    controller.set_brightness(int(command[1]))
                elif command[0] == 's' and len(command) > 2:
                    strip = int(command[1]) - 1
                    active = command[2].lower() == 'on'
                    controller.set_strip_active(strip, active)
                elif command[0] == 'sw':
                    position = controller.spdt_switch.get_switch_position()
                    print(f"SPDT Switch position: {position}")
                else:
                    print("Invalid command")
            except (ValueError, IndexError):
                print("Invalid command format")
            except KeyboardInterrupt:
                break
    
    finally:
        controller.stop()
        print("LED Controller stopped")

if __name__ == "__main__":
    main()

