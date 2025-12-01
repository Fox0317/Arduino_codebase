#include <WiFi.h>

// WiFi credentials - Replace with your network details
const char* ssid = "CaptainMajestic";
const char* password = "GoFuckYourself";

// Connection status variables
bool wifiConnected = false;
unsigned long lastStatusCheck = 0;
const unsigned long statusCheckInterval = 5000; // Check every 5 seconds

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("ESP32-S3 WiFi Connection Test");
  Serial.println("=============================");
  
  // Initialize WiFi
  WiFi.mode(WIFI_STA);
  WiFi.setHostname("ESP32_RX_00");
  WiFi.begin(ssid, password);
  
  Serial.print("Connecting to WiFi");
  
  // Wait for connection with timeout
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("WiFi Connected Successfully!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal Strength (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    Serial.print("MAC Address: ");
    Serial.println(WiFi.macAddress());
  } else {
    Serial.println("Failed to connect to WiFi!");
    Serial.println("Please check your credentials and try again.");
  }
  
  Serial.println("Setup complete. Starting main loop...");
  Serial.println();
}

void loop() {
  // Check WiFi status periodically
  if (millis() - lastStatusCheck >= statusCheckInterval) {
    lastStatusCheck = millis();
    
    if (WiFi.status() == WL_CONNECTED) {
      if (!wifiConnected) {
        // Just reconnected
        wifiConnected = true;
        Serial.println("WiFi Reconnected!");
        Serial.print("New IP Address: ");
        Serial.println(WiFi.localIP());
      }
      
      // Print connection status
      Serial.print("WiFi Status: CONNECTED | ");
      Serial.print("IP: ");
      Serial.print(WiFi.localIP());
      Serial.print(" | RSSI: ");
      Serial.print(WiFi.RSSI());
      Serial.println(" dBm");
      
    } else {
      if (wifiConnected) {
        // Just disconnected
        wifiConnected = false;
        Serial.println("WiFi Disconnected! Attempting to reconnect...");
        WiFi.reconnect();
      }
      
      Serial.println("WiFi Status: DISCONNECTED");
      
      // Attempt to reconnect every 10 seconds
      static unsigned long lastReconnectAttempt = 0;
      if (millis() - lastReconnectAttempt >= 10000) {
        lastReconnectAttempt = millis();
        Serial.println("Attempting to reconnect...");
        WiFi.begin(ssid, password);
      }
    }
  }
  
  // Small delay to prevent overwhelming the serial output
  delay(100);
}
