// ESP32 Configuration Header
// Copy this file and modify for each ESP32

// WiFi Configuration
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// ESP32 Identification
#define STRIP_ID 0  // Change this for each ESP32: 0, 1, or 2
#define LED_PIN 10  // Change this for each ESP32: 10, 18, or 19

// LED Configuration
#define NUM_LEDS 1000
#define LED_TYPE WS2812
#define COLOR_ORDER RGB

// Network Configuration
#define UDP_PORT 8888
#define PACKET_TIMEOUT_MS 5000
#define WIFI_RECONNECT_ATTEMPTS 20
#define WIFI_RECONNECT_DELAY 500

// Debug Settings
#define SERIAL_DEBUG true
#define DEBUG_PACKET_RECEIVED false
#define DEBUG_LED_UPDATES false

// ESP32-Specific Settings
// ESP32 #1 (Strip 0): STRIP_ID=0, LED_PIN=10
// ESP32 #2 (Strip 1): STRIP_ID=1, LED_PIN=18  
// ESP32 #3 (Strip 2): STRIP_ID=2, LED_PIN=19
