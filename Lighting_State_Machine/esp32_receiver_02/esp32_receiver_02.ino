#include "FastLED.h"
#include <WiFi.h>
#include <WiFiUdp.h>

// LED Configuration
#define NUM_LEDS 282
#define LED_PIN 5  // First LED strip pin
#define LED_PIN_2 7  // Second LED strip pin
#define STRIP_ID 2  //Change this for each ESP32 (0, 1, 2, 3)

// WiFi Configuration
const char* ssid = "LightingHUB";
const char* password = "JpopKpop";
const char* newHostname = "LED_RECEIVER_02";

// Static IP Configuration
IPAddress local_IP(192, 168, 8, 102);
IPAddress gateway(192, 168, 8, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);
IPAddress secondaryDNS(8, 8, 4, 4);

// UDP Configuration
WiFiUDP udp;
const int udpPort = 8888;
const int packetSize = 3 + (NUM_LEDS * 3); // strip_id + brightness + spdt_status + LED data

// LED strips
CRGB leds[NUM_LEDS];
CRGB leds2[NUM_LEDS];

// Network variables
bool wifiConnected = false;
unsigned long lastPacketTime = 0;
const unsigned long timeoutMs = 5000; // 5 second timeout
unsigned long lastStatusCheck = 0;
const unsigned long statusCheckInterval = 10000; // Check every 10 seconds

// SPDT Switch status
uint8_t currentSpdtStatus = 0; // 0=None/Center, 1=Position A, 2=Position B
uint8_t lastSpdtStatus = 0;

// Strip control based on SPDT status
bool strip1Active = true;  // Strip 1 (LED_PIN) active state
bool strip2Active = true;  // Strip 2 (LED_PIN_2) active state

// Packet buffering
#define BUFFER_SIZE 5  // Buffer up to 5 packets
struct PacketBuffer {
  uint8_t data[packetSize];
  bool valid;
  unsigned long timestamp;
};
PacketBuffer packetBuffer[BUFFER_SIZE];
int bufferWriteIndex = 0;
int bufferReadIndex = 0;
int bufferCount = 0;

void setupWiFi();
void handleIncomingPacket();
void handleSpdtSwitch(uint8_t spdtStatus);
void updateStripControl(uint8_t spdtStatus);
bool addPacketToBuffer(uint8_t* packetData, int packetLength);
bool getPacketFromBuffer(uint8_t* packetData, int* packetLength);
void processBufferedPackets();

// Packet structure: [strip_id][brightness][spdt_status][R][G][B][R][G][B]...
// strip_id: 1 byte (0-3)
// brightness: 1 byte (0-255)
// spdt_status: 1 byte (0=None/Center, 1=Position A, 2=Position B)
// LED data: 3 bytes per LED (RGB)

void setup() {
  Serial.begin(115200);
  delay(1000); // Give time for serial to initialize
  
  Serial.println("ESP32 LED Receiver Starting...");
  Serial.print("Running on Core: ");
  Serial.println(xPortGetCoreID());
  
  // Initialize LED strips
  FastLED.addLeds<WS2812, LED_PIN, RGB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.addLeds<WS2812, LED_PIN_2, RGB>(leds2, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(255);
  FastLED.clear();
  FastLED.show();
  
  // Set WiFi hostname
  WiFi.setHostname(newHostname);
  
  // Setup WiFi
  setupWiFi();
  
  // Initialize UDP if WiFi is connected
  if (wifiConnected) {
    udp.begin(udpPort);
    Serial.print("UDP server started on port ");
    Serial.println(udpPort);
  }
  
  Serial.println("ESP32 LED Receiver Ready - Dual Strip Mode (Single Core)");
}

void loop() {
  // Process UDP packets with buffering for smooth animations
  if (wifiConnected) {
    int packetLength = udp.parsePacket();
    if (packetLength > 0) {
      uint8_t packetData[packetSize];
      int bytesRead = udp.read(packetData, packetSize);
      if (bytesRead > 0) {
        addPacketToBuffer(packetData, bytesRead);
        lastPacketTime = millis();
      }
    }
    
    // Process buffered packets at consistent rate
    processBufferedPackets();
  }
  
  // Check for timeout - turn off LEDs if no data received
  if (millis() - lastPacketTime > timeoutMs) {
    if (lastPacketTime > 0) { // Only if we've received data before
      FastLED.clear(); // This clears both strips since they're both added to FastLED
      FastLED.show();
      Serial.println("Timeout - Both LED strips turned off");
      lastPacketTime = 0; // Reset to prevent repeated messages
    }
  }
  
  // Check WiFi status periodically
  if (millis() - lastStatusCheck >= statusCheckInterval) {
    lastStatusCheck = millis();
    
    if (WiFi.status() != WL_CONNECTED) {
      if (wifiConnected) {
        wifiConnected = false;
        Serial.println("WiFi Disconnected! Attempting to reconnect...");
      }
      setupWiFi();
      if (wifiConnected) {
        udp.begin(udpPort);
        Serial.print("UDP server restarted on port ");
        Serial.println(udpPort);
      }
    }
  }
  
  // Minimal delay for smooth operation
  delay(1);
}

void setupWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  // Configure static IP
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("Static IP configuration failed!");
  }
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println();
    Serial.print("WiFi connected! Static IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    wifiConnected = false;
  }
}

void handleIncomingPacket(uint8_t* packetData, int len) {
  
  if (len < 4) { // Updated minimum length check
    Serial.println("Packet too short");
    return;
  }
  
  // Extract packet data
  uint8_t stripId = packetData[0];
  uint8_t brightness = packetData[1];
  uint8_t spdtStatus = packetData[2]; // Extract SPDT switch status
  
  // Check if this packet is for this ESP32
  if (stripId != STRIP_ID) {
    return; // Not for this strip
  }
  
  // Update SPDT status and check for changes
  lastSpdtStatus = currentSpdtStatus;
  currentSpdtStatus = spdtStatus;
  
  // Update strip control based on SPDT status
  updateStripControl(currentSpdtStatus);
  
  // Extract LED data
  int ledDataStart = 3; // Updated start position for LED data
  int expectedDataLength = NUM_LEDS * 3;
  int actualDataLength = len - ledDataStart;
  
  if (actualDataLength < expectedDataLength) {
    Serial.println("Incomplete LED data");
    return;
  }
  
  // Update brightness immediately
  if (brightness != FastLED.getBrightness()) {
    FastLED.setBrightness(brightness);
  }
  
    // Update LED colors on active strips only
    for (int i = 0; i < NUM_LEDS; i++) {
      int dataIndex = ledDataStart + (i * 3);
      if (dataIndex + 2 < len) {
        uint8_t r = packetData[dataIndex];
        uint8_t g = packetData[dataIndex + 1];
        uint8_t b = packetData[dataIndex + 2];
        CRGB color = CRGB(r, g, b);
        
        // Update strip 1 if active
        if (strip1Active) {
          leds[i] = color;
        } else {
          leds[i] = CRGB::Black; // Turn off inactive strip
        }
        
        // Update strip 2 if active
        if (strip2Active) {
          leds2[i] = color;
        } else {
          leds2[i] = CRGB::Black; // Turn off inactive strip
        }
      }
    }
  
  // Display LEDs immediately for smooth animations
  FastLED.show();
  // Count packets and FastLED.show() calls
  static unsigned long packetCount = 0;
  static unsigned long showCount = 0;
  static unsigned long lastDiagTime = 0;
  
  packetCount++;
  showCount++;
}

bool addPacketToBuffer(uint8_t* packetData, int packetLength) {
  // Check if buffer is full
  if (bufferCount >= BUFFER_SIZE) {
    return false; // Buffer full, drop oldest packet
  }
  
  // Add packet to buffer
  memcpy(packetBuffer[bufferWriteIndex].data, packetData, packetLength);
  packetBuffer[bufferWriteIndex].valid = true;
  packetBuffer[bufferWriteIndex].timestamp = millis();
  
  bufferWriteIndex = (bufferWriteIndex + 1) % BUFFER_SIZE;
  bufferCount++;
  
  return true;
}

bool getPacketFromBuffer(uint8_t* packetData, int* packetLength) {
  // Check if buffer has data
  if (bufferCount <= 0) {
    return false;
  }
  
  // Get packet from buffer
  memcpy(packetData, packetBuffer[bufferReadIndex].data, packetSize);
  *packetLength = packetSize;
  
  packetBuffer[bufferReadIndex].valid = false;
  bufferReadIndex = (bufferReadIndex + 1) % BUFFER_SIZE;
  bufferCount--;
  
  return true;
}

void processBufferedPackets() {
  static unsigned long lastProcessTime = 0;
  const unsigned long processInterval = 50; // Process every 50ms (20 FPS)
  
  // Only process if enough time has passed
  if (millis() - lastProcessTime >= processInterval) {
    uint8_t packetData[packetSize];
    int packetLength;
    
    if (getPacketFromBuffer(packetData, &packetLength)) {
      handleIncomingPacket(packetData, packetLength);
      lastProcessTime = millis();
    }
  }
}

// Update strip control based on SPDT status
void updateStripControl(uint8_t spdtStatus) {
  switch (spdtStatus) {
    case 0: // None/Center position - Both strips on
      strip1Active = true;
      strip2Active = true;
      break;
      
    case 1: // Position A - Only strip 1 on
      strip1Active = true;
      strip2Active = false;
      break;
      
    case 2: // Position B - Only strip 2 on
      strip1Active = false;
      strip2Active = true;
      break;
      
    default:
      // Unknown status - keep current state
      break;
  }
}

// Handle SPDT switch functionality
void handleSpdtSwitch(uint8_t spdtStatus) {
  // Add your custom functionality based on SPDT switch position here
  // This function is called whenever the SPDT switch position changes
  
  switch (spdtStatus) {
    case 0: // None/Center position
      // Add functionality for center position
      break;
      
    case 1: // Position A
      // Add functionality for position A
      // For example: Different LED patterns, brightness levels, etc.
      break;
      
    case 2: // Position B
      // Add functionality for position B
      // For example: Different LED patterns, brightness levels, etc.
      break;
      
    default:

      break;
  }
}

// Optional: Add status LED to show connection state
void updateStatusLED() {
  // This could be used to show WiFi connection status
  // For example, blink LED when connected, solid when receiving data
}
