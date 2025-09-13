#include <Arduino.h>
#line 1 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\Lighting_State_Machine\\esp32_receiver\\esp32_receiver.ino"
#include "FastLED.h"
#include <WiFi.h>
#include <WiFiUdp.h>

// LED Configuration
#define NUM_LEDS 1000
#define LED_PIN 10  // Change this pin for each ESP32 (10, 18, 19)
#define STRIP_ID 0  // Change this for each ESP32 (0, 1, 2)

// WiFi Configuration
const char* ssid = "Captain_Majestic";
const char* password = "GoFuckYourself";

// UDP Configuration
WiFiUDP udp;
const int udpPort = 8888;
const int packetSize = 3 + (NUM_LEDS * 3); // strip_id + brightness + LED data

// LED strip
CRGB leds[NUM_LEDS];

// Network variables
bool wifiConnected = false;
unsigned long lastPacketTime = 0;
const unsigned long timeoutMs = 5000; // 5 second timeout

// Packet structure: [strip_id][brightness][R][G][B][R][G][B]...
// strip_id: 1 byte (0-2)
// brightness: 1 byte (0-255)
// LED data: 3 bytes per LED (RGB)

#line 32 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\Lighting_State_Machine\\esp32_receiver\\esp32_receiver.ino"
void setup();
#line 55 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\Lighting_State_Machine\\esp32_receiver\\esp32_receiver.ino"
void loop();
#line 87 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\Lighting_State_Machine\\esp32_receiver\\esp32_receiver.ino"
void setupWiFi();
#line 112 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\Lighting_State_Machine\\esp32_receiver\\esp32_receiver.ino"
void handleIncomingPacket();
#line 166 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\Lighting_State_Machine\\esp32_receiver\\esp32_receiver.ino"
void updateStatusLED();
#line 32 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\Lighting_State_Machine\\esp32_receiver\\esp32_receiver.ino"
void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 LED Receiver Starting...");
  
  // Initialize LED strip
  FastLED.addLeds<WS2812, LED_PIN, RGB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(255);
  FastLED.clear();
  FastLED.show();
  
  // Initialize WiFi
  setupWiFi();
  
  // Initialize UDP
  if (wifiConnected) {
    udp.begin(udpPort);
    Serial.print("UDP server started on port ");
    Serial.println(udpPort);
  }
  
  Serial.println("ESP32 LED Receiver Ready");
}

void loop() {
  if (!wifiConnected) {
    // Try to reconnect WiFi
    setupWiFi();
    if (wifiConnected) {
      udp.begin(udpPort);
    }
    delay(1000);
    return;
  }
  
  // Check for incoming packets
  int packetLength = udp.parsePacket();
  if (packetLength > 0) {
    handleIncomingPacket();
    lastPacketTime = millis();
  }
  
  // Check for timeout - turn off LEDs if no data received
  if (millis() - lastPacketTime > timeoutMs) {
    if (lastPacketTime > 0) { // Only if we've received data before
      FastLED.clear();
      FastLED.show();
      Serial.println("Timeout - LEDs turned off");
      lastPacketTime = 0; // Reset to prevent repeated messages
    }
  }
  
  // Small delay to prevent overwhelming the system
  delay(1);
}

void setupWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
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
    Serial.print("WiFi connected! IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    wifiConnected = false;
  }
}

void handleIncomingPacket() {
  // Read packet data
  uint8_t packetBuffer[packetSize];
  int len = udp.read(packetBuffer, packetSize);
  
  if (len < 3) {
    Serial.println("Packet too short");
    return;
  }
  
  // Extract packet data
  uint8_t stripId = packetBuffer[0];
  uint8_t brightness = packetBuffer[1];
  
  // Check if this packet is for this ESP32
  if (stripId != STRIP_ID) {
    return; // Not for this strip
  }
  
  // Update brightness
  FastLED.setBrightness(brightness);
  
  // Extract LED data
  int ledDataStart = 2;
  int expectedDataLength = NUM_LEDS * 3;
  int actualDataLength = len - ledDataStart;
  
  if (actualDataLength < expectedDataLength) {
    Serial.println("Incomplete LED data");
    return;
  }
  
  // Update LED colors
  for (int i = 0; i < NUM_LEDS; i++) {
    int dataIndex = ledDataStart + (i * 3);
    if (dataIndex + 2 < len) {
      uint8_t r = packetBuffer[dataIndex];
      uint8_t g = packetBuffer[dataIndex + 1];
      uint8_t b = packetBuffer[dataIndex + 2];
      leds[i] = CRGB(r, g, b);
    }
  }
  
  // Update LEDs
  FastLED.show();
  
  // Debug output (uncomment for debugging)
  // Serial.print("Updated strip ");
  // Serial.print(STRIP_ID);
  // Serial.print(" with brightness ");
  // Serial.println(brightness);
}

// Optional: Add status LED to show connection state
void updateStatusLED() {
  // This could be used to show WiFi connection status
  // For example, blink LED when connected, solid when receiving data
}

#line 1 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\Lighting_State_Machine\\esp32_receiver\\esp32_led_receiver.ino"
#include "FastLED.h"
#include <WiFi.h>
#include <WiFiUdp.h>

// LED Configuration
#define NUM_LEDS 1000
#define LED_PIN 10  // Change this pin for each ESP32 (10, 18, 19)
#define STRIP_ID 0  // Change this for each ESP32 (0, 1, 2)

// WiFi Configuration
const char* ssid = "Captain_Majestic";
const char* password = "GoFuckYourself";

// UDP Configuration
WiFiUDP udp;
const int udpPort = 8888;
const int packetSize = 3 + (NUM_LEDS * 3); // strip_id + brightness + LED data

// LED strip
CRGB leds[NUM_LEDS];

// Network variables
bool wifiConnected = false;
unsigned long lastPacketTime = 0;
const unsigned long timeoutMs = 5000; // 5 second timeout

// Packet structure: [strip_id][brightness][R][G][B][R][G][B]...
// strip_id: 1 byte (0-2)
// brightness: 1 byte (0-255)
// LED data: 3 bytes per LED (RGB)

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 LED Receiver Starting...");
  
  // Initialize LED strip
  FastLED.addLeds<WS2812, LED_PIN, RGB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(255);
  FastLED.clear();
  FastLED.show();
  
  // Initialize WiFi
  setupWiFi();
  
  // Initialize UDP
  if (wifiConnected) {
    udp.begin(udpPort);
    Serial.print("UDP server started on port ");
    Serial.println(udpPort);
  }
  
  Serial.println("ESP32 LED Receiver Ready");
}

void loop() {
  if (!wifiConnected) {
    // Try to reconnect WiFi
    setupWiFi();
    if (wifiConnected) {
      udp.begin(udpPort);
    }
    delay(1000);
    return;
  }
  
  // Check for incoming packets
  int packetLength = udp.parsePacket();
  if (packetLength > 0) {
    handleIncomingPacket();
    lastPacketTime = millis();
  }
  
  // Check for timeout - turn off LEDs if no data received
  if (millis() - lastPacketTime > timeoutMs) {
    if (lastPacketTime > 0) { // Only if we've received data before
      FastLED.clear();
      FastLED.show();
      Serial.println("Timeout - LEDs turned off");
      lastPacketTime = 0; // Reset to prevent repeated messages
    }
  }
  
  // Small delay to prevent overwhelming the system
  delay(1);
}

void setupWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
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
    Serial.print("WiFi connected! IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    wifiConnected = false;
  }
}

void handleIncomingPacket() {
  // Read packet data
  uint8_t packetBuffer[packetSize];
  int len = udp.read(packetBuffer, packetSize);
  
  if (len < 3) {
    Serial.println("Packet too short");
    return;
  }
  
  // Extract packet data
  uint8_t stripId = packetBuffer[0];
  uint8_t brightness = packetBuffer[1];
  
  // Check if this packet is for this ESP32
  if (stripId != STRIP_ID) {
    return; // Not for this strip
  }
  
  // Update brightness
  FastLED.setBrightness(brightness);
  
  // Extract LED data
  int ledDataStart = 2;
  int expectedDataLength = NUM_LEDS * 3;
  int actualDataLength = len - ledDataStart;
  
  if (actualDataLength < expectedDataLength) {
    Serial.println("Incomplete LED data");
    return;
  }
  
  // Update LED colors
  for (int i = 0; i < NUM_LEDS; i++) {
    int dataIndex = ledDataStart + (i * 3);
    if (dataIndex + 2 < len) {
      uint8_t r = packetBuffer[dataIndex];
      uint8_t g = packetBuffer[dataIndex + 1];
      uint8_t b = packetBuffer[dataIndex + 2];
      leds[i] = CRGB(r, g, b);
    }
  }
  
  // Update LEDs
  FastLED.show();
  
  // Debug output (uncomment for debugging)
  // Serial.print("Updated strip ");
  // Serial.print(STRIP_ID);
  // Serial.print(" with brightness ");
  // Serial.println(brightness);
}

// Optional: Add status LED to show connection state
void updateStatusLED() {
  // This could be used to show WiFi connection status
  // For example, blink LED when connected, solid when receiving data
}

