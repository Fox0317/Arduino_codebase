#!/usr/bin/env python3
"""
Raspberry Pi LED Controller
Calculates LED pixel values and sends data to three ESP32 controllers
Each ESP32 controls 1000 LEDs (3000 total)
"""

import socket
import json
import time
import math
import random
import threading
from typing import List, Tuple
import numpy as np
import RPi.GPIO as GPIO
import pyaudio
import wave
from scipy.fft import fft, fftfreq
from collections import deque

# LED Configuration
NUM_LEDS_PER_STRIP = [800, 900, 1000]  # Different lengths for each strip
NUM_STRIPS = 3
TOTAL_LEDS = sum(NUM_LEDS_PER_STRIP)

# Music Mode Frequency Section Configuration
# Each strip is divided into 3 sections: High, Mid, Bass
# Values are percentages of total strip length
FREQUENCY_SECTION_PERCENTAGES = {
    'high_start': 0.0,      # Start of high frequency section (0%)
    'high_end': 0.125,      # End of high frequency section (12.5%)
    'mid_start': 0.125,     # Start of mid frequency section (12.5%)
    'mid_end': 0.25,        # End of mid frequency section (25%)
    'bass_start': 0.25,     # Start of bass section (25%)
    'bass_end': 0.75,       # End of bass section (75%)
    'mid2_start': 0.75,     # Start of second mid section (75%)
    'mid2_end': 0.875,      # End of second mid section (87.5%)
    'high2_start': 0.875,   # Start of second high section (87.5%)
    'high2_end': 1.0        # End of second high section (100%)
}

# ESP32 Controller IPs (update these with your actual IPs)
ESP32_IPS = [
    "192.168.1.101",  # ESP32 #1 - First 800 LEDs
    "192.168.1.102",  # ESP32 #2 - Second 900 LEDs  
    "192.168.1.103",  # ESP32 #3 - Third 1000 LEDs
]

# Communication settings
UDP_PORT = 8888
SEND_INTERVAL = 0.05  # Send data every 50ms (20 FPS)

# KY-040 Encoder Configuration (matching ESP32 setup)
ENCODER_CLK_PIN = 18  # GPIO 18 (D2 equivalent)
ENCODER_DT_PIN = 19   # GPIO 19 (D3 equivalent) 
ENCODER_SW_PIN = 20   # GPIO 20 (D4 equivalent)

# Audio Configuration
SAMPLE_RATE = 44100  # Audio sample rate
CHUNK_SIZE = 1024    # Audio chunk size for processing
NUM_FREQUENCY_BANDS = 8  # Number of frequency bands for analysis
AUDIO_BUFFER_SIZE = 10   # Number of audio chunks to buffer

# Animation state
class AnimationState:
    def __init__(self):
        self.current_mode = 0
        self.brightness = 255
        self.hue = 0
        self.animation_step = 0
        # Initialize arrays for each strip with different lengths
        self.fire_heat = [[0] * count for count in NUM_LEDS_PER_STRIP]
        self.twinkle_state = [[random.randint(0, 255) for _ in range(count)] for count in NUM_LEDS_PER_STRIP]
        self.aurora_intensity = [[0] * count for count in NUM_LEDS_PER_STRIP]
        self.aurora_phase = 0
        self.aurora_hue = 96
        
        # Audio analysis data
        self.frequency_bands = [0.0] * NUM_FREQUENCY_BANDS
        self.audio_level = 0.0
        self.bass_level = 0.0
        self.mid_level = 0.0
        self.high_level = 0.0

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
    RAINBOW_CHASE = 11
    COMET = 12
    TWINKLE = 13
    WAVE = 14
    CHASE = 15
    BREATHING = 16

class AudioProcessor:
    """Handles USB microphone input and FFT frequency analysis"""
    
    def __init__(self):
        self.audio = None
        self.stream = None
        self.running = False
        self.audio_thread = None
        self.audio_buffer = deque(maxlen=AUDIO_BUFFER_SIZE)
        self.latest_frequency_data = [0.0] * NUM_FREQUENCY_BANDS
        self.latest_audio_level = 0.0
        
        # Frequency band ranges (Hz)
        self.frequency_ranges = [
            (20, 60),      # Sub-bass
            (60, 250),     # Bass
            (250, 500),    # Low mid
            (500, 2000),   # Mid
            (2000, 4000),  # High mid
            (4000, 6000),  # Presence
            (6000, 20000), # Brilliance
            (20000, 22050) # Air
        ]
        
        self.init_audio()
    
    def init_audio(self):
        """Initialize PyAudio for microphone input"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Find default input device
            device_info = self.audio.get_default_input_device_info()
            print(f"Using audio device: {device_info['name']}")
            
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.audio_callback
            )
            
            print("Audio processor initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize audio: {e}")
            self.audio = None
            self.stream = None
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback for real-time processing"""
        if status:
            print(f"Audio callback status: {status}")
        
        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Add to buffer
        self.audio_buffer.append(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
    def start_audio_processing(self):
        """Start audio processing thread"""
        if self.stream and not self.running:
            self.running = True
            self.stream.start_stream()
            self.audio_thread = threading.Thread(target=self.process_audio_loop)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            print("Audio processing started")
    
    def stop_audio_processing(self):
        """Stop audio processing"""
        self.running = False
        if self.stream:
            self.stream.stop_stream()
        if self.audio_thread:
            self.audio_thread.join()
        print("Audio processing stopped")
    
    def process_audio_loop(self):
        """Main audio processing loop"""
        while self.running:
            if len(self.audio_buffer) > 0:
                # Get latest audio chunk
                audio_chunk = self.audio_buffer[-1]
                
                # Perform FFT analysis
                self.analyze_frequency_bands(audio_chunk)
            
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage
    
    def analyze_frequency_bands(self, audio_data):
        """Perform FFT analysis and extract frequency bands"""
        try:
            # Apply window function to reduce spectral leakage
            windowed_data = audio_data * np.hanning(len(audio_data))
            
            # Perform FFT
            fft_data = fft(windowed_data)
            fft_magnitude = np.abs(fft_data[:len(fft_data)//2])
            
            # Get frequency bins
            freqs = fftfreq(len(audio_data), 1/SAMPLE_RATE)[:len(fft_data)//2]
            
            # Calculate overall audio level
            self.latest_audio_level = np.sqrt(np.mean(audio_data**2)) / 32768.0
            
            # Extract frequency bands
            for i, (low_freq, high_freq) in enumerate(self.frequency_ranges):
                # Find frequency bin indices
                low_idx = np.argmin(np.abs(freqs - low_freq))
                high_idx = np.argmin(np.abs(freqs - high_freq))
                
                # Calculate average magnitude for this band
                band_magnitude = np.mean(fft_magnitude[low_idx:high_idx+1])
                
                # Normalize and apply smoothing
                normalized_magnitude = band_magnitude / 32768.0
                self.latest_frequency_data[i] = normalized_magnitude
            
            # Calculate bass, mid, and high levels
            self.latest_frequency_data[0] = np.mean(self.latest_frequency_data[0:2])  # Bass
            self.latest_frequency_data[1] = np.mean(self.latest_frequency_data[2:4])  # Mid
            self.latest_frequency_data[2] = np.mean(self.latest_frequency_data[4:6])  # High
            
        except Exception as e:
            print(f"Error in frequency analysis: {e}")
    
    def get_frequency_data(self):
        """Get latest frequency analysis data"""
        return self.latest_frequency_data.copy()
    
    def get_audio_level(self):
        """Get latest audio level"""
        return self.latest_audio_level
    
    def cleanup(self):
        """Cleanup audio resources"""
        self.stop_audio_processing()
        if self.stream:
            self.stream.close()
        if self.audio:
            self.audio.terminate()

class EncoderHandler:
    """Handles KY-040 rotary encoder input for mode selection and brightness control"""
    
    def __init__(self):
        self.encoder_value = 0
        self.last_encoder_value = 0
        self.encoder_button_pressed = False
        self.last_button_press = 0
        self.button_state = False
        self.button_held = False
        self.encoder_step_counter = 0
        self.last_interrupt_time = 0
        self.last_button_interrupt_time = 0
        
        # Button press/release tracking for global toggle
        self.button_press_start_time = 0
        self.button_press_duration = 0
        self.rotation_during_press = False
        self.button_released = False
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ENCODER_CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENCODER_DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENCODER_SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Add event detection
        GPIO.add_event_detect(ENCODER_CLK_PIN, GPIO.BOTH, callback=self._encoder_callback, bouncetime=5)
        GPIO.add_event_detect(ENCODER_SW_PIN, GPIO.FALLING, callback=self._button_callback, bouncetime=200)
        
        print("Encoder handler initialized")
    
    def _encoder_callback(self, channel):
        """Encoder rotation callback"""
        current_time = time.time() * 1000  # Convert to milliseconds
        
        if current_time - self.last_interrupt_time > 5:  # Debounce
            clk_state = GPIO.input(ENCODER_CLK_PIN)
            dt_state = GPIO.input(ENCODER_DT_PIN)
            
            if clk_state != dt_state:
                self.encoder_step_counter += 1
            else:
                self.encoder_step_counter -= 1
            
            # Check if button is held for brightness adjustment
            button_currently_held = not GPIO.input(ENCODER_SW_PIN)  # Button is active low
            
            # Track rotation during button press
            if button_currently_held and self.button_press_start_time > 0:
                self.rotation_during_press = True
            
            if button_currently_held:
                # Button is held - adjust brightness
                if self.encoder_step_counter >= 1:
                    self.encoder_step_counter = 0
                    return "brightness_up"
                elif self.encoder_step_counter <= -1:
                    self.encoder_step_counter = 0
                    return "brightness_down"
            else:
                # Button not held - change mode (exclude music mode from cycling)
                if self.encoder_step_counter >= 2:
                    self.encoder_value += 1
                    if self.encoder_value >= 17:  # Exclude music mode (17) from cycling
                        self.encoder_value = 0
                    self.encoder_step_counter = 0
                    return "mode_up"
                elif self.encoder_step_counter <= -2:
                    self.encoder_value -= 1
                    if self.encoder_value < 0:
                        self.encoder_value = 16  # Exclude music mode (17) from cycling
                    self.encoder_step_counter = 0
                    return "mode_down"
        
        self.last_interrupt_time = current_time
        return None
    
    def _button_callback(self, channel):
        """Button press callback"""
        current_time = time.time() * 1000  # Convert to milliseconds
        
        if current_time - self.last_button_interrupt_time > 200:  # Debounce
            button_currently_pressed = not GPIO.input(ENCODER_SW_PIN)  # Button is active low
            
            if button_currently_pressed:
                # Button pressed - start timing
                self.button_press_start_time = current_time
                self.rotation_during_press = False
                self.button_released = False
                self.encoder_button_pressed = True
                print("Encoder button pressed")
            else:
                # Button released - check for toggle
                if self.button_press_start_time > 0:
                    self.button_press_duration = current_time - self.button_press_start_time
                    self.button_released = True
                    print("Encoder button released")
        
        self.last_button_interrupt_time = current_time
    
    def get_encoder_action(self):
        """Get the latest encoder action"""
        # Check for button-only press (no rotation during press)
        if self.button_released and self.button_press_start_time > 0:
            # Reset button tracking
            self.button_released = False
            self.button_press_start_time = 0
            
            # Check if it was a button-only press (no rotation during press)
            if not self.rotation_during_press and self.button_press_duration > 100:  # At least 100ms press
                self.rotation_during_press = False
                return "toggle_music_mode"
        
        # Check for regular button press
        if self.encoder_button_pressed:
            self.encoder_button_pressed = False
            return "button_press"
        
        # Check for rotation
        action = self._encoder_callback(None)
        return action
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        GPIO.cleanup()

class LEDController:
    def __init__(self):
        self.state = AnimationState()
        self.sockets = []
        self.running = False
        self.strip_active = [True, True, True]  # All strips active by default
        self.encoder = EncoderHandler()  # Initialize encoder handler
        self.audio_processor = AudioProcessor()  # Initialize audio processor
        self.music_mode_enabled = False  # Music mode boolean variable that toggles on button press/release
        
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
    
    def get_frequency_sections(self, strip_index: int) -> dict:
        """Calculate LED ranges for each frequency section based on strip length"""
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        sections = {}
        for key, percentage in FREQUENCY_SECTION_PERCENTAGES.items():
            sections[key] = int(led_count * percentage)
        
        return sections
    
    def get_frequency_brightness(self, strip_index: int, led_index: int) -> float:
        """Calculate brightness for a specific LED with feathering between frequency sections"""
        sections = self.get_frequency_sections(strip_index)
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        # Define feathering zone size (5% of total LEDs)
        feather_zone = max(1, int(led_count * 0.05))
        
        # Determine which frequency section this LED primarily belongs to
        if led_index < sections['high_end'] or led_index >= sections['high2_start']:
            primary_frequency = 'high'
            primary_level = self.state.high_level
        elif led_index < sections['mid_end'] or (led_index >= sections['mid2_start'] and led_index < sections['mid2_end']):
            primary_frequency = 'mid'
            primary_level = self.state.mid_level
        else:
            primary_frequency = 'bass'
            primary_level = self.state.bass_level
        
        # Calculate base brightness
        base_brightness = 0.3
        brightness = base_brightness + (primary_level * 0.7)
        
        # Apply feathering at section boundaries
        if led_index >= sections['high_end'] - feather_zone and led_index < sections['high_end'] + feather_zone:
            # Transition between high and mid (first boundary)
            distance = led_index - (sections['high_end'] - feather_zone)
            feather_factor = distance / (feather_zone * 2)
            mid_brightness = base_brightness + (self.state.mid_level * 0.7)
            brightness = brightness * (1 - feather_factor) + mid_brightness * feather_factor
            
        elif led_index >= sections['mid_end'] - feather_zone and led_index < sections['mid_end'] + feather_zone:
            # Transition between mid and bass (second boundary)
            distance = led_index - (sections['mid_end'] - feather_zone)
            feather_factor = distance / (feather_zone * 2)
            bass_brightness = base_brightness + (self.state.bass_level * 0.7)
            brightness = brightness * (1 - feather_factor) + bass_brightness * feather_factor
            
        elif led_index >= sections['bass_end'] - feather_zone and led_index < sections['bass_end'] + feather_zone:
            # Transition between bass and mid (third boundary)
            distance = led_index - (sections['bass_end'] - feather_zone)
            feather_factor = distance / (feather_zone * 2)
            mid_brightness = base_brightness + (self.state.mid_level * 0.7)
            brightness = brightness * (1 - feather_factor) + mid_brightness * feather_factor
            
        elif led_index >= sections['mid2_end'] - feather_zone and led_index < sections['mid2_end'] + feather_zone:
            # Transition between mid and high (fourth boundary)
            distance = led_index - (sections['mid2_end'] - feather_zone)
            feather_factor = distance / (feather_zone * 2)
            high_brightness = base_brightness + (self.state.high_level * 0.7)
            brightness = brightness * (1 - feather_factor) + high_brightness * feather_factor
        
        return min(1.0, brightness)

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
        """White mode, optionally music reactive"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        if self.music_mode_enabled:
            # Music reactive white mode with frequency sections and feathering
            frequency_data = self.audio_processor.get_frequency_data()
            audio_level = self.audio_processor.get_audio_level()
            
            # Update state with latest audio data
            self.state.frequency_bands = frequency_data
            self.state.audio_level = audio_level
            self.state.bass_level = frequency_data[0] if len(frequency_data) > 0 else 0.0
            self.state.mid_level = frequency_data[1] if len(frequency_data) > 1 else 0.0
            self.state.high_level = frequency_data[2] if len(frequency_data) > 2 else 0.0
            
            for i in range(led_count):
                # Get feathered brightness for this LED
                brightness = self.get_frequency_brightness(strip_index, i)
                brightness_value = int(255 * brightness)
                
                pixels.append(self.rgb_to_bytes(brightness_value, brightness_value, brightness_value))
        else:
            # Normal white mode
            for i in range(led_count):
                pixels.append(self.rgb_to_bytes(255, 255, 255))
        
        return pixels

    def mode_solid_color(self, strip_index: int) -> List[bytes]:
        """Solid color mode with cycling hue, optionally music reactive"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        if self.music_mode_enabled:
            # Music reactive solid color mode with frequency sections and feathering
            frequency_data = self.audio_processor.get_frequency_data()
            audio_level = self.audio_processor.get_audio_level()
            
            # Update state with latest audio data
            self.state.frequency_bands = frequency_data
            self.state.audio_level = audio_level
            self.state.bass_level = frequency_data[0] if len(frequency_data) > 0 else 0.0
            self.state.mid_level = frequency_data[1] if len(frequency_data) > 1 else 0.0
            self.state.high_level = frequency_data[2] if len(frequency_data) > 2 else 0.0
            
            # Get base color from current hue
            r_base, g_base, b_base = self.hsv_to_rgb(self.state.hue, 1.0, 1.0)
            
            for i in range(led_count):
                # Get feathered brightness for this LED
                brightness = self.get_frequency_brightness(strip_index, i)
                
                # Apply brightness to base color
                r = int(r_base * brightness)
                g = int(g_base * brightness)
                b = int(b_base * brightness)
                
                pixels.append(self.rgb_to_bytes(r, g, b))
        else:
            # Normal solid color mode
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
        """Fire animation mode"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        # Cool down every cell
        for i in range(led_count):
            self.state.fire_heat[strip_index][i] = max(0, self.state.fire_heat[strip_index][i] - random.randint(0, 2))
        
        # Heat diffusion
        new_heat = [0] * led_count
        for i in range(led_count):
            left_heat = self.state.fire_heat[strip_index][i-1] if i > 0 else 0
            right_heat = self.state.fire_heat[strip_index][i+1] if i < led_count-1 else 0
            current_heat = self.state.fire_heat[strip_index][i]
            new_heat[i] = (left_heat + current_heat + right_heat) // 3
            
            # Add randomness
            if random.randint(0, 255) < 50:
                new_heat[i] = min(255, new_heat[i] + random.randint(0, 10))
        
        self.state.fire_heat[strip_index] = new_heat
        
        # Add sparks
        if random.randint(0, 255) < 120:
            spark_pos = random.randint(0, led_count-1)
            self.state.fire_heat[strip_index][spark_pos] = min(255, self.state.fire_heat[strip_index][spark_pos] + random.randint(160, 255))
        
        # Convert heat to colors
        for i in range(led_count):
            heat = self.state.fire_heat[strip_index][i]
            if heat < 85:
                r = heat * 3
                g = 0
                b = 0
            elif heat < 170:
                r = 255
                g = (heat - 85) * 3
                b = 0
            else:
                r = 255
                g = 255
                b = (heat - 170) * 3
            
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
            
            # Aurora colors (green, purple, pink)
            aurora_colors = [(96, 200, 120), (192, 100, 200), (224, 100, 150)]
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

    def mode_wave(self, strip_index: int) -> List[bytes]:
        """Wave animation"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        for i in range(led_count):
            wave = int(127 * (1 + math.sin((self.state.animation_step + i * 8) * math.pi / 128)))
            hue = (self.state.hue + i * 2) % 360
            r, g, b = self.hsv_to_rgb(hue, 1.0, wave / 255.0)
            pixels.append(self.rgb_to_bytes(r, g, b))
        
        return pixels

    def mode_chase(self, strip_index: int) -> List[bytes]:
        """Chase animation"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        for i in range(led_count):
            pos = (self.state.animation_step // 2) % led_count
            if i == pos:
                r, g, b = self.hsv_to_rgb(self.state.hue, 1.0, 1.0)
                pixels.append(self.rgb_to_bytes(r, g, b))
            elif i == (pos + 1) % led_count:
                r, g, b = self.hsv_to_rgb(self.state.hue, 1.0, 0.5)
                pixels.append(self.rgb_to_bytes(r, g, b))
            elif i == (pos + 2) % led_count:
                r, g, b = self.hsv_to_rgb(self.state.hue, 1.0, 0.25)
                pixels.append(self.rgb_to_bytes(r, g, b))
            else:
                pixels.append(self.rgb_to_bytes(0, 0, 0))
        
        return pixels

    def mode_breathing(self, strip_index: int) -> List[bytes]:
        """Breathing animation"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        breath = int(127 * (1 + math.sin(self.state.animation_step * math.pi / 128)))
        r, g, b = self.hsv_to_rgb(self.state.hue, 1.0, breath / 255.0)
        
        for i in range(led_count):
            pixels.append(self.rgb_to_bytes(r, g, b))
        
        return pixels

    def mode_color_reactive(self, strip_index: int, r_base: int, g_base: int, b_base: int) -> List[bytes]:
        """Color mode that reacts to music when enabled"""
        pixels = []
        led_count = NUM_LEDS_PER_STRIP[strip_index]
        
        if self.music_mode_enabled:
            # Music reactive color mode with frequency sections and feathering
            frequency_data = self.audio_processor.get_frequency_data()
            audio_level = self.audio_processor.get_audio_level()
            
            # Update state with latest audio data
            self.state.frequency_bands = frequency_data
            self.state.audio_level = audio_level
            self.state.bass_level = frequency_data[0] if len(frequency_data) > 0 else 0.0
            self.state.mid_level = frequency_data[1] if len(frequency_data) > 1 else 0.0
            self.state.high_level = frequency_data[2] if len(frequency_data) > 2 else 0.0
            
            for i in range(led_count):
                # Get feathered brightness for this LED
                brightness = self.get_frequency_brightness(strip_index, i)
                
                # Apply brightness to base color
                r = int(r_base * brightness)
                g = int(g_base * brightness)
                b = int(b_base * brightness)
                
                pixels.append(self.rgb_to_bytes(r, g, b))
        else:
            # Normal color mode
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
            return self.mode_color_reactive(strip_index, 255, 0, 0)  # Red
        elif mode == LEDModes.YELLOW:
            return self.mode_color_reactive(strip_index, 255, 255, 0)  # Yellow
        elif mode == LEDModes.GREEN:
            return self.mode_color_reactive(strip_index, 0, 255, 0)  # Green
        elif mode == LEDModes.CYAN:
            return self.mode_color_reactive(strip_index, 0, 255, 255)  # Cyan
        elif mode == LEDModes.BLUE:
            return self.mode_color_reactive(strip_index, 0, 0, 255)  # Blue
        elif mode == LEDModes.MAGENTA:
            return self.mode_color_reactive(strip_index, 255, 0, 255)  # Magenta
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
        elif mode == LEDModes.WAVE:
            return self.mode_wave(strip_index)
        elif mode == LEDModes.CHASE:
            return self.mode_chase(strip_index)
        elif mode == LEDModes.BREATHING:
            return self.mode_breathing(strip_index)
        else:
            return self.mode_white(strip_index)

    def send_data_to_esp32(self, strip_index: int, led_data: List[bytes]):
        """Send LED data to specific ESP32"""
        if strip_index >= len(self.sockets) or self.sockets[strip_index] is None:
            return False
        
        try:
            # Create packet: [strip_index, brightness, led_data...]
            packet = bytearray()
            packet.append(strip_index)
            packet.append(self.state.brightness)
            
            for pixel in led_data:
                packet.extend(pixel)
            
            # Send to ESP32
            self.sockets[strip_index].sendto(packet, (ESP32_IPS[strip_index], UDP_PORT))
            return True
        except Exception as e:
            print(f"Failed to send data to ESP32 #{strip_index + 1}: {e}")
            return False

    def update_animation_state(self):
        """Update animation state variables"""
        self.state.animation_step += 1
        
        # Update hue for color cycling
        if self.state.current_mode in [LEDModes.SOLID_COLOR, LEDModes.RAINBOW, LEDModes.WAVE, LEDModes.CHASE, LEDModes.BREATHING]:
            self.state.hue = (self.state.hue + 1) % 360
        
        # Update aurora phase
        if self.state.current_mode == LEDModes.AURORA:
            self.state.aurora_phase = (self.state.aurora_phase + 1) % 1000

    def run_animation_loop(self):
        """Main animation loop"""
        print("Starting LED animation loop...")
        self.running = True
        
        while self.running:
            start_time = time.time()
            
            # Handle encoder input
            self.handle_encoder_input()
            
            # Calculate and send data for each strip
            for strip_index in range(NUM_STRIPS):
                led_data = self.calculate_led_data(strip_index)
                self.send_data_to_esp32(strip_index, led_data)
            
            # Update animation state
            self.update_animation_state()
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, SEND_INTERVAL - elapsed)
            time.sleep(sleep_time)

    def handle_encoder_input(self):
        """Handle encoder input for mode selection and brightness control"""
        action = self.encoder.get_encoder_action()
        
        if action == "mode_up":
            self.state.current_mode = (self.state.current_mode + 1) % 17  # Exclude music mode from cycling
            print(f"Mode changed to: {self.state.current_mode}")
        elif action == "mode_down":
            self.state.current_mode = (self.state.current_mode - 1) % 17  # Exclude music mode from cycling
            print(f"Mode changed to: {self.state.current_mode}")
        elif action == "brightness_up":
            self.state.brightness = min(255, self.state.brightness + 12)
            print(f"Brightness increased to: {self.state.brightness}")
        elif action == "brightness_down":
            self.state.brightness = max(0, self.state.brightness - 12)
            print(f"Brightness decreased to: {self.state.brightness}")
        elif action == "toggle_music_mode":
            self.toggle_music_mode()
        elif action == "button_press":
            # Button press functionality can be added here if needed
            print("Encoder button pressed")

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

    def get_music_mode_enabled(self) -> bool:
        """Get the current state of the music mode enabled variable"""
        return self.music_mode_enabled

    def toggle_music_mode(self):
        """Toggle the music mode enabled boolean variable"""
        self.music_mode_enabled = not self.music_mode_enabled
        if self.music_mode_enabled:
            self.audio_processor.start_audio_processing()
            print("Music mode enabled - Audio processing started")
        else:
            self.audio_processor.stop_audio_processing()
            print("Music mode disabled - Audio processing stopped")

    def stop(self):
        """Stop the animation loop"""
        self.running = False
        for sock in self.sockets:
            if sock:
                sock.close()
        self.encoder.cleanup()  # Cleanup encoder GPIO resources
        self.audio_processor.cleanup()  # Cleanup audio resources

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
        print("t - Toggle music mode enabled")
        print("g - Get music mode state")
        print("q - Quit")
        print("\nEncoder Controls:")
        print("- Rotate encoder: Change mode (0-16)")
        print("- Hold button + rotate: Adjust brightness")
        print("- Press and release button (without rotation): Toggle music mode")
        print("\nLED Configuration:")
        print(f"- Strip 1: {NUM_LEDS_PER_STRIP[0]} LEDs")
        print(f"- Strip 2: {NUM_LEDS_PER_STRIP[1]} LEDs")
        print(f"- Strip 3: {NUM_LEDS_PER_STRIP[2]} LEDs")
        print(f"- Total: {TOTAL_LEDS} LEDs")
        print("\nAudio Features:")
        print("- Music reactive modes: White, Red, Yellow, Green, Cyan, Blue, Magenta, Solid Color")
        print("- Real-time FFT frequency analysis")
        print("- Frequency sections per strip:")
        print(f"  * High frequency: {FREQUENCY_SECTION_PERCENTAGES['high_start']*100:.1f}%-{FREQUENCY_SECTION_PERCENTAGES['high_end']*100:.1f}% and {FREQUENCY_SECTION_PERCENTAGES['high2_start']*100:.1f}%-{FREQUENCY_SECTION_PERCENTAGES['high2_end']*100:.1f}%")
        print(f"  * Mid frequency: {FREQUENCY_SECTION_PERCENTAGES['mid_start']*100:.1f}%-{FREQUENCY_SECTION_PERCENTAGES['mid_end']*100:.1f}% and {FREQUENCY_SECTION_PERCENTAGES['mid2_start']*100:.1f}%-{FREQUENCY_SECTION_PERCENTAGES['mid2_end']*100:.1f}%")
        print(f"  * Bass frequency: {FREQUENCY_SECTION_PERCENTAGES['bass_start']*100:.1f}%-{FREQUENCY_SECTION_PERCENTAGES['bass_end']*100:.1f}%")
        print("- Each frequency section modulates brightness independently")
        print("- Smooth feathering between frequency sections (5% transition zones)")
        print("- Toggle with encoder button press/release")
        
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
                elif command[0] == 't':
                    controller.toggle_music_mode()
                elif command[0] == 'g':
                    print(f"Music mode {'enabled' if controller.get_music_mode_enabled() else 'disabled'}")
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
