# Network Configuration for LED Controller System
# Update these settings for your network

# WiFi Settings
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# ESP32 Controller IPs
# Assign static IPs to your ESP32s in your router's DHCP settings
ESP32_IPS = [
    "192.168.1.101",  # ESP32 #1 - Controls first 1000 LEDs (strip 0)
    "192.168.1.102",  # ESP32 #2 - Controls second 1000 LEDs (strip 1)  
    "192.168.1.103",  # ESP32 #3 - Controls third 1000 LEDs (strip 2)
]

# Raspberry Pi IP (optional, for reference)
RASPBERRY_PI_IP = "192.168.1.100"

# UDP Communication
UDP_PORT = 8888
SEND_INTERVAL = 0.05  # 50ms = 20 FPS

# LED Configuration
NUM_LEDS_PER_STRIP = 1000
NUM_STRIPS = 3
TOTAL_LEDS = NUM_LEDS_PER_STRIP * NUM_STRIPS

# ESP32 Pin Configuration
# Update these for each ESP32
ESP32_PINS = {
    0: 10,  # ESP32 #1 LED pin
    1: 18,  # ESP32 #2 LED pin  
    2: 19,  # ESP32 #3 LED pin
}

# Animation Settings
DEFAULT_BRIGHTNESS = 255
DEFAULT_MODE = 0  # White mode
ANIMATION_SPEED = 1.0  # Multiplier for animation speed

# Network Timeout Settings
PACKET_TIMEOUT_MS = 5000  # 5 seconds
WIFI_RECONNECT_ATTEMPTS = 20
WIFI_RECONNECT_DELAY = 500  # ms
