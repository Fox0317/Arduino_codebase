/*
 * LIFX LAN Protocol Controller
 * Based on official LIFX LAN protocol documentation
 * https://lan.developer.lifx.com/docs/communicating-with-device
 * 
 * This script implements the LIFX LAN protocol for direct communication
 * with LIFX smart bulbs over UDP on port 56700.
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "CaptainMajestic";
const char* password = "GoFuckYourself";

// LIFX LAN Protocol Configuration
#define LIFX_PORT 56700
#define LIFX_BROADCAST_IP "255.255.255.255"
WiFiUDP lifxUdp;

// LIFX Packet Structure (based on official LAN protocol)
struct LifxPacket {
  // Frame Header (16 bytes)
  uint16_t size;           // Total size of packet
  uint16_t protocol;       // Protocol number (1024)
  uint32_t source;         // Source identifier
  uint8_t tagged;          // 1 for broadcast, 0 for directed
  uint8_t addressable;     // Always 1
  uint8_t protocol_version; // Protocol version
  uint32_t reserved;       // Reserved field
  
  // Frame Address (16 bytes)
  uint8_t target[8];       // Target MAC address (6 bytes + 2 padding)
  uint8_t reserved2[6];    // Reserved
  uint8_t res_required;    // Response required
  uint8_t ack_required;    // Acknowledgment required
  uint8_t sequence;        // Sequence number
  
  // Protocol Header (12 bytes)
  uint64_t reserved3;      // Reserved
  uint16_t type;           // Message type
  uint16_t reserved4;      // Reserved
} __attribute__((packed));

// LIFX Message Types
#define LIFX_GET_SERVICE 2
#define LIFX_STATE_SERVICE 3
#define LIFX_GET_HOST_INFO 12
#define LIFX_STATE_HOST_INFO 13
#define LIFX_GET_POWER 20
#define LIFX_SET_POWER 21
#define LIFX_STATE_POWER 22
#define LIFX_GET_LABEL 23
#define LIFX_SET_LABEL 24
#define LIFX_STATE_LABEL 25
#define LIFX_ACKNOWLEDGEMENT 45
#define LIFX_GET_LIGHT_STATE 101
#define LIFX_SET_COLOR 102
#define LIFX_STATE_LIGHT 107
#define LIFX_ECHO_REQUEST 58
#define LIFX_ECHO_RESPONSE 59

// LIFX Device Structure
struct LifxDevice {
  IPAddress ip;
  uint8_t mac[6];
  String label;
  bool power;
  uint16_t hue;
  uint16_t saturation;
  uint16_t brightness;
  uint16_t kelvin;
  bool connected;
  unsigned long lastSeen;
};

#define MAX_DEVICES 10
LifxDevice devices[MAX_DEVICES];
int deviceCount = 0;

// Communication variables
static uint8_t sequence = 0;
static uint32_t source = 0x12345678;

// Function declarations
void setupWiFi();
void discoverLifxDevices();
void sendLifxPacket(uint16_t messageType, uint8_t* payload, size_t payloadSize, bool broadcast = true);
void sendLifxPacketToDevice(uint16_t messageType, uint8_t* payload, size_t payloadSize, LifxDevice* device);
void handleLifxResponse();
void parseLifxPacket(uint8_t* buffer, int packetSize);
void handleStateService(uint8_t* payload, size_t payloadSize, IPAddress remoteIP);
void handleStateLabel(uint8_t* payload, size_t payloadSize, IPAddress remoteIP);
void handleStatePower(uint8_t* payload, size_t payloadSize, IPAddress remoteIP);
void handleStateLight(uint8_t* payload, size_t payloadSize, IPAddress remoteIP);
void handleEchoResponse(uint8_t* payload, size_t payloadSize, IPAddress remoteIP);
void setDevicePower(LifxDevice* device, bool power);
void setDeviceColor(LifxDevice* device, uint16_t hue, uint16_t saturation, uint16_t brightness, uint16_t kelvin = 3500);
void sendEchoRequest(LifxDevice* device);
void printDeviceInfo(LifxDevice* device);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=== LIFX LAN Protocol Controller ===");
  Serial.println("Based on official LIFX LAN documentation");
  Serial.println("https://lan.developer.lifx.com/docs/communicating-with-device");
  Serial.println();
  
  // Initialize WiFi
  setupWiFi();
  
  // Initialize UDP
  if (lifxUdp.begin(LIFX_PORT)) {
    Serial.println("UDP initialized on port 56700");
  } else {
    Serial.println("Failed to initialize UDP");
    return;
  }
  
  // Discover LIFX devices
  Serial.println("\n=== Discovering LIFX Devices ===");
  discoverLifxDevices();
  
  Serial.println("\n=== LIFX Controller Ready ===");
  Serial.println("Commands:");
  Serial.println("1. Send 'discover' to rediscover devices");
  Serial.println("2. Send 'list' to list discovered devices");
  Serial.println("3. Send 'echo <device_index>' to test connection");
  Serial.println("4. Send 'power <device_index> <on/off>' to control power");
  Serial.println("5. Send 'color <device_index> <hue> <sat> <bright>' to set color");
  Serial.println("6. Send 'white <device_index> <bright>' to set white light");
}

void loop() {
  // Handle incoming LIFX responses
  if (lifxUdp.parsePacket()) {
    handleLifxResponse();
  }
  
  // Handle serial commands
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    handleSerialCommand(command);
  }
  
  // Periodic device status check
  static unsigned long lastStatusCheck = 0;
  if (millis() - lastStatusCheck > 30000) { // Every 30 seconds
    checkDeviceStatus();
    lastStatusCheck = millis();
  }
  
  delay(10);
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
    Serial.println();
    Serial.print("WiFi connected! IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());
    Serial.print("Subnet: ");
    Serial.println(WiFi.subnetMask());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    Serial.println("Please check your WiFi credentials and try again.");
  }
}

void discoverLifxDevices() {
  Serial.println("Sending LIFX discovery broadcast...");
  
  // Send GetService message as broadcast
  sendLifxPacket(LIFX_GET_SERVICE, nullptr, 0, true);
  
  // Listen for responses
  Serial.println("Listening for device responses...");
  unsigned long startTime = millis();
  int responses = 0;
  
  while (millis() - startTime < 5000) { // Listen for 5 seconds
    if (lifxUdp.parsePacket()) {
      responses++;
      handleLifxResponse();
    }
    delay(10);
  }
  
  Serial.print("Discovery complete. Found ");
  Serial.print(deviceCount);
  Serial.println(" devices.");
  
  // Print discovered devices
  for (int i = 0; i < deviceCount; i++) {
    Serial.print("Device ");
    Serial.print(i);
    Serial.print(": ");
    printDeviceInfo(&devices[i]);
  }
}

void sendLifxPacket(uint16_t messageType, uint8_t* payload, size_t payloadSize, bool broadcast) {
  LifxPacket packet;
  
  // Frame Header
  packet.size = sizeof(LifxPacket) + payloadSize;
  packet.protocol = 1024; // LIFX protocol version
  packet.source = source;
  packet.tagged = broadcast ? 1 : 0;
  packet.addressable = 1;
  packet.protocol_version = 0;
  packet.reserved = 0;
  
  // Frame Address
  memset(packet.target, 0, 8); // All zeros for broadcast
  memset(packet.reserved2, 0, 6);
  packet.res_required = 1;
  packet.ack_required = 0;
  packet.sequence = sequence++;
  
  // Protocol Header
  packet.reserved3 = 0;
  packet.type = messageType;
  packet.reserved4 = 0;
  
  // Send packet
  lifxUdp.beginPacket(LIFX_BROADCAST_IP, LIFX_PORT);
  lifxUdp.write((uint8_t*)&packet, sizeof(LifxPacket));
  if (payloadSize > 0) {
    lifxUdp.write(payload, payloadSize);
  }
  bool sent = lifxUdp.endPacket();
  
  Serial.print("Sent LIFX packet type ");
  Serial.print(messageType);
  Serial.print(" (");
  Serial.print(packet.size);
  Serial.print(" bytes): ");
  Serial.println(sent ? "SUCCESS" : "FAILED");
}

void sendLifxPacketToDevice(uint16_t messageType, uint8_t* payload, size_t payloadSize, LifxDevice* device) {
  LifxPacket packet;
  
  // Frame Header
  packet.size = sizeof(LifxPacket) + payloadSize;
  packet.protocol = 1024;
  packet.source = source;
  packet.tagged = 0; // Directed message
  packet.addressable = 1;
  packet.protocol_version = 0;
  packet.reserved = 0;
  
  // Frame Address - Set target MAC
  memcpy(packet.target, device->mac, 6);
  packet.target[6] = 0;
  packet.target[7] = 0;
  memset(packet.reserved2, 0, 6);
  packet.res_required = 1;
  packet.ack_required = 0;
  packet.sequence = sequence++;
  
  // Protocol Header
  packet.reserved3 = 0;
  packet.type = messageType;
  packet.reserved4 = 0;
  
  // Send packet to device's IP
  lifxUdp.beginPacket(device->ip, LIFX_PORT);
  lifxUdp.write((uint8_t*)&packet, sizeof(LifxPacket));
  if (payloadSize > 0) {
    lifxUdp.write(payload, payloadSize);
  }
  bool sent = lifxUdp.endPacket();
  
  Serial.print("Sent to device ");
  Serial.print(device->label);
  Serial.print(" (");
  Serial.print(device->ip);
  Serial.print("): ");
  Serial.println(sent ? "SUCCESS" : "FAILED");
}

void handleLifxResponse() {
  uint8_t buffer[1024];
  int packetSize = lifxUdp.read(buffer, sizeof(buffer));
  IPAddress remoteIP = lifxUdp.remoteIP();
  
  if (packetSize >= sizeof(LifxPacket)) {
    LifxPacket* packet = (LifxPacket*)buffer;
    uint8_t* payload = buffer + sizeof(LifxPacket);
    size_t payloadSize = packetSize - sizeof(LifxPacket);
    
    Serial.print("Received LIFX packet type ");
    Serial.print(packet->type);
    Serial.print(" from ");
    Serial.print(remoteIP);
    Serial.print(" (");
    Serial.print(packetSize);
    Serial.println(" bytes)");
    
    switch (packet->type) {
      case LIFX_STATE_SERVICE:
        handleStateService(payload, payloadSize, remoteIP);
        break;
      case LIFX_STATE_LABEL:
        handleStateLabel(payload, payloadSize, remoteIP);
        break;
      case LIFX_STATE_POWER:
        handleStatePower(payload, payloadSize, remoteIP);
        break;
      case LIFX_STATE_LIGHT:
        handleStateLight(payload, payloadSize, remoteIP);
        break;
      case LIFX_ECHO_RESPONSE:
        handleEchoResponse(payload, payloadSize, remoteIP);
        break;
      case LIFX_ACKNOWLEDGEMENT:
        Serial.println("Received acknowledgment");
        break;
      default:
        Serial.print("Unknown packet type: ");
        Serial.println(packet->type);
        break;
    }
  }
}

void handleStateService(uint8_t* payload, size_t payloadSize, IPAddress remoteIP) {
  if (payloadSize >= 5) {
    uint8_t service = payload[0];
    uint32_t port = *(uint32_t*)(payload + 1);
    
    Serial.print("Device service: ");
    Serial.print(service);
    Serial.print(", port: ");
    Serial.println(port);
    
    // Add device to our list
    if (deviceCount < MAX_DEVICES) {
      devices[deviceCount].ip = remoteIP;
      devices[deviceCount].connected = true;
      devices[deviceCount].lastSeen = millis();
      devices[deviceCount].label = "Unknown";
      devices[deviceCount].power = false;
      devices[deviceCount].hue = 0;
      devices[deviceCount].saturation = 0;
      devices[deviceCount].brightness = 0;
      devices[deviceCount].kelvin = 3500;
      
      // Extract MAC from packet target field
      // Note: This is simplified - in practice you'd need to match by IP
      memset(devices[deviceCount].mac, 0, 6);
      
      deviceCount++;
      Serial.print("Added device #");
      Serial.println(deviceCount - 1);
    }
  }
}

void handleStateLabel(uint8_t* payload, size_t payloadSize, IPAddress remoteIP) {
  if (payloadSize >= 32) {
    char label[33];
    memcpy(label, payload, 32);
    label[32] = '\0';
    
    // Find device by IP and update label
    for (int i = 0; i < deviceCount; i++) {
      if (devices[i].ip == remoteIP) {
        devices[i].label = String(label);
        Serial.print("Device ");
        Serial.print(i);
        Serial.print(" label: ");
        Serial.println(devices[i].label);
        break;
      }
    }
  }
}

void handleStatePower(uint8_t* payload, size_t payloadSize, IPAddress remoteIP) {
  if (payloadSize >= 2) {
    uint16_t level = *(uint16_t*)payload;
    bool power = (level > 0);
    
    // Find device by IP and update power state
    for (int i = 0; i < deviceCount; i++) {
      if (devices[i].ip == remoteIP) {
        devices[i].power = power;
        Serial.print("Device ");
        Serial.print(i);
        Serial.print(" power: ");
        Serial.println(power ? "ON" : "OFF");
        break;
      }
    }
  }
}

void handleStateLight(uint8_t* payload, size_t payloadSize, IPAddress remoteIP) {
  if (payloadSize >= 13) {
    uint16_t hue = *(uint16_t*)(payload + 0);
    uint16_t saturation = *(uint16_t*)(payload + 2);
    uint16_t brightness = *(uint16_t*)(payload + 4);
    uint16_t kelvin = *(uint16_t*)(payload + 6);
    uint16_t power = *(uint16_t*)(payload + 8);
    uint32_t duration = *(uint32_t*)(payload + 10);
    
    // Find device by IP and update state
    for (int i = 0; i < deviceCount; i++) {
      if (devices[i].ip == remoteIP) {
        devices[i].hue = hue;
        devices[i].saturation = saturation;
        devices[i].brightness = brightness;
        devices[i].kelvin = kelvin;
        devices[i].power = (power > 0);
        devices[i].lastSeen = millis();
        
        Serial.print("Device ");
        Serial.print(i);
        Serial.print(" state: H:");
        Serial.print(hue);
        Serial.print(" S:");
        Serial.print(saturation);
        Serial.print(" V:");
        Serial.print(brightness);
        Serial.print(" K:");
        Serial.print(kelvin);
        Serial.print(" Power:");
        Serial.println(devices[i].power ? "ON" : "OFF");
        break;
      }
    }
  }
}

void handleEchoResponse(uint8_t* payload, size_t payloadSize, IPAddress remoteIP) {
  Serial.print("Echo response received (");
  Serial.print(payloadSize);
  Serial.println(" bytes)");
  
  // Find device by IP and mark as responsive
  for (int i = 0; i < deviceCount; i++) {
    if (devices[i].ip == remoteIP) {
      devices[i].connected = true;
      devices[i].lastSeen = millis();
      Serial.print("Device ");
      Serial.print(i);
      Serial.println(" is responsive");
      break;
    }
  }
}

void setDevicePower(LifxDevice* device, bool power) {
  struct {
    uint16_t level;
  } payload;
  
  payload.level = power ? 65535 : 0;
  
  sendLifxPacketToDevice(LIFX_SET_POWER, (uint8_t*)&payload, sizeof(payload), device);
}

void setDeviceColor(LifxDevice* device, uint16_t hue, uint16_t saturation, uint16_t brightness, uint16_t kelvin) {
  struct {
    uint8_t reserved;
    uint16_t hue;
    uint16_t saturation;
    uint16_t brightness;
    uint16_t kelvin;
    uint32_t duration;
  } payload;
  
  payload.reserved = 0;
  payload.hue = hue;
  payload.saturation = saturation;
  payload.brightness = brightness;
  payload.kelvin = kelvin;
  payload.duration = 0; // Instant change
  
  sendLifxPacketToDevice(LIFX_SET_COLOR, (uint8_t*)&payload, sizeof(payload), device);
}

void sendEchoRequest(LifxDevice* device) {
  struct {
    uint8_t payload[64];
  } echoPayload;
  
  // Fill with test data
  for (int i = 0; i < 64; i++) {
    echoPayload.payload[i] = i;
  }
  
  sendLifxPacketToDevice(LIFX_ECHO_REQUEST, (uint8_t*)&echoPayload, sizeof(echoPayload), device);
}

void printDeviceInfo(LifxDevice* device) {
  Serial.print(device->label);
  Serial.print(" (");
  Serial.print(device->ip);
  Serial.print(") - ");
  Serial.print(device->power ? "ON" : "OFF");
  Serial.print(" H:");
  Serial.print(device->hue);
  Serial.print(" S:");
  Serial.print(device->saturation);
  Serial.print(" V:");
  Serial.print(device->brightness);
  Serial.print(" K:");
  Serial.println(device->kelvin);
}

void handleSerialCommand(String command) {
  command.toLowerCase();
  
  if (command == "discover") {
    Serial.println("Rediscovering LIFX devices...");
    deviceCount = 0; // Reset device list
    discoverLifxDevices();
  }
  else if (command == "list") {
    Serial.println("\n=== Discovered Devices ===");
    for (int i = 0; i < deviceCount; i++) {
      Serial.print(i);
      Serial.print(": ");
      printDeviceInfo(&devices[i]);
    }
  }
  else if (command.startsWith("echo ")) {
    int deviceIndex = command.substring(5).toInt();
    if (deviceIndex >= 0 && deviceIndex < deviceCount) {
      Serial.print("Sending echo request to device ");
      Serial.println(deviceIndex);
      sendEchoRequest(&devices[deviceIndex]);
    } else {
      Serial.println("Invalid device index");
    }
  }
  else if (command.startsWith("power ")) {
    // Format: power <device_index> <on/off>
    int firstSpace = command.indexOf(' ', 6);
    if (firstSpace > 0) {
      int deviceIndex = command.substring(6, firstSpace).toInt();
      String powerState = command.substring(firstSpace + 1);
      
      if (deviceIndex >= 0 && deviceIndex < deviceCount) {
        bool power = (powerState == "on");
        Serial.print("Setting device ");
        Serial.print(deviceIndex);
        Serial.print(" power to ");
        Serial.println(power ? "ON" : "OFF");
        setDevicePower(&devices[deviceIndex], power);
      } else {
        Serial.println("Invalid device index");
      }
    } else {
      Serial.println("Usage: power <device_index> <on/off>");
    }
  }
  else if (command.startsWith("color ")) {
    // Format: color <device_index> <hue> <sat> <bright>
    int firstSpace = command.indexOf(' ', 6);
    if (firstSpace > 0) {
      int deviceIndex = command.substring(6, firstSpace).toInt();
      String params = command.substring(firstSpace + 1);
      
      int space1 = params.indexOf(' ');
      int space2 = params.indexOf(' ', space1 + 1);
      int space3 = params.indexOf(' ', space2 + 1);
      
      if (space1 > 0 && space2 > 0 && space3 > 0) {
        uint16_t hue = params.substring(0, space1).toInt();
        uint16_t sat = params.substring(space1 + 1, space2).toInt();
        uint16_t bright = params.substring(space2 + 1, space3).toInt();
        
        if (deviceIndex >= 0 && deviceIndex < deviceCount) {
          Serial.print("Setting device ");
          Serial.print(deviceIndex);
          Serial.print(" color to H:");
          Serial.print(hue);
          Serial.print(" S:");
          Serial.print(sat);
          Serial.print(" V:");
          Serial.println(bright);
          setDeviceColor(&devices[deviceIndex], hue, sat, bright);
        } else {
          Serial.println("Invalid device index");
        }
      } else {
        Serial.println("Usage: color <device_index> <hue> <sat> <bright>");
      }
    } else {
      Serial.println("Usage: color <device_index> <hue> <sat> <bright>");
    }
  }
  else if (command.startsWith("white ")) {
    // Format: white <device_index> <bright>
    int firstSpace = command.indexOf(' ', 6);
    if (firstSpace > 0) {
      int deviceIndex = command.substring(6, firstSpace).toInt();
      uint16_t bright = command.substring(firstSpace + 1).toInt();
      
      if (deviceIndex >= 0 && deviceIndex < deviceCount) {
        Serial.print("Setting device ");
        Serial.print(deviceIndex);
        Serial.print(" to white light, brightness: ");
        Serial.println(bright);
        setDeviceColor(&devices[deviceIndex], 0, 0, bright, 3500);
      } else {
        Serial.println("Invalid device index");
      }
    } else {
      Serial.println("Usage: white <device_index> <bright>");
    }
  }
  else {
    Serial.println("Unknown command. Available commands:");
    Serial.println("  discover - Rediscover LIFX devices");
    Serial.println("  list - List discovered devices");
    Serial.println("  echo <device_index> - Test device connection");
    Serial.println("  power <device_index> <on/off> - Control device power");
    Serial.println("  color <device_index> <hue> <sat> <bright> - Set device color");
    Serial.println("  white <device_index> <bright> - Set device to white light");
  }
}

void checkDeviceStatus() {
  Serial.println("Checking device status...");
  
  for (int i = 0; i < deviceCount; i++) {
    if (millis() - devices[i].lastSeen > 60000) { // 1 minute timeout
      devices[i].connected = false;
      Serial.print("Device ");
      Serial.print(i);
      Serial.println(" appears to be offline");
    }
  }
} 