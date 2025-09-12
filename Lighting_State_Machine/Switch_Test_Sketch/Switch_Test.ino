/*
  LED Strip Switch Test Sketch
  
  This sketch tests the on-off-on switch functionality for controlling
  which LED strips are active on the main controller.
  
  Hardware:
  - ESP32 development board
  - On-Off-On switch connected to GPIO 5 and GPIO 6
  - WS2812B LED strips connected to GPIO 10 and GPIO 18
  
  Switch Positions:
  - Position 1 (Left): Only first strip active
  - Position 2 (Center): Both strips active
  - Position 3 (Right): Only second strip active
*/

#include "FastLED.h"

// LED Configuration
#define NUM_LEDS 1000
#define LED_PIN1 10
#define LED_PIN2 18
CRGB leds[NUM_LEDS];

// LED Strip Control Switch Configuration
#define STRIP1_SWITCH_PIN 5  // GPIO 5 for first strip switch
#define STRIP2_SWITCH_PIN 6  // GPIO 6 for second strip switch

// LED strip control variables
bool strip1Active = true;
bool strip2Active = true;

// Test pattern variables
int testHue = 0;
unsigned long lastUpdate = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("LED Strip Switch Test Starting...");
  
  // Initialize LED strip control switch pins
  pinMode(STRIP1_SWITCH_PIN, INPUT_PULLUP);
  pinMode(STRIP2_SWITCH_PIN, INPUT_PULLUP);
  
  // Initialize LED strips
  FastLED.addLeds<WS2812, LED_PIN1, RGB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.addLeds<WS2812, LED_PIN2, RGB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(128);
  
  // Check initial switch states
  checkLEDStripSwitches();
  
  Serial.println("LED Strip Switch Test Started");
  Serial.println("Move the switch to test different configurations");
}

void loop() {
  // Check LED strip switches
  static unsigned long lastSwitchCheck = 0;
  if (millis() - lastSwitchCheck > 100) { // Check switches every 100ms
    checkLEDStripSwitches();
    lastSwitchCheck = millis();
  }
  
  // Update test pattern
  if (millis() - lastUpdate > 50) {
    updateTestPattern();
    lastUpdate = millis();
  }
  
  FastLED.show();
}

void checkLEDStripSwitches() {
  // Read switch states (active low due to INPUT_PULLUP)
  bool switch1Low = !digitalRead(STRIP1_SWITCH_PIN);
  bool switch2Low = !digitalRead(STRIP2_SWITCH_PIN);
  
  // Update strip active states based on switch positions
  if (switch1Low && !switch2Low) {
    // Only first strip active
    if (strip1Active != true || strip2Active != false) {
      strip1Active = true;
      strip2Active = false;
      reconfigureLEDStrips();
      Serial.println("Switch: First strip only active");
    }
  } else if (!switch1Low && switch2Low) {
    // Only second strip active
    if (strip1Active != false || strip2Active != true) {
      strip1Active = false;
      strip2Active = true;
      reconfigureLEDStrips();
      Serial.println("Switch: Second strip only active");
    }
  } else if (!switch1Low && !switch2Low) {
    // Both strips active (default behavior)
    if (strip1Active != true || strip2Active != true) {
      strip1Active = true;
      strip2Active = true;
      reconfigureLEDStrips();
      Serial.println("Switch: Both strips active");
    }
  } else {
    // Both switches low - this shouldn't happen with on-off-on switch
    // Default to both strips active
    if (strip1Active != true || strip2Active != true) {
      strip1Active = true;
      strip2Active = true;
      reconfigureLEDStrips();
      Serial.println("Switch: Invalid state, defaulting to both strips");
    }
  }
}

void reconfigureLEDStrips() {
  // Clear all LED strips
  FastLED.clear();
  
  // Remove all LED strips
  FastLED.clear();
  
  // Re-add LED strips based on active states
  if (strip1Active) {
    FastLED.addLeds<WS2812, LED_PIN1, RGB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  }
  if (strip2Active) {
    FastLED.addLeds<WS2812, LED_PIN2, RGB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  }
  
  // Set brightness
  FastLED.setBrightness(128);
  
  Serial.print("Reconfigured LED strips - Strip1: ");
  Serial.print(strip1Active ? "ON" : "OFF");
  Serial.print(", Strip2: ");
  Serial.println(strip2Active ? "ON" : "OFF");
}

void updateTestPattern() {
  // Create a moving rainbow pattern
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV(testHue + i * 2, 255, 255);
  }
  
  // Move the pattern
  testHue++;
  
  // Print current configuration every few seconds
  static unsigned long lastStatusPrint = 0;
  if (millis() - lastStatusPrint > 3000) {
    Serial.print("Current configuration - Strip1: ");
    Serial.print(strip1Active ? "ON" : "OFF");
    Serial.print(", Strip2: ");
    Serial.print(strip2Active ? "ON" : "OFF");
    Serial.print(", Switch1: ");
    Serial.print(digitalRead(STRIP1_SWITCH_PIN) ? "HIGH" : "LOW");
    Serial.print(", Switch2: ");
    Serial.println(digitalRead(STRIP2_SWITCH_PIN) ? "HIGH" : "LOW");
    lastStatusPrint = millis();
  }
}

/*
  Expected Serial Output:
  
  LED Strip Switch Test Starting...
  LED Strip Switch Test Started
  Move the switch to test different configurations
  Switch: Both strips active
  Reconfigured LED strips - Strip1: ON, Strip2: ON
  Current configuration - Strip1: ON, Strip2: ON, Switch1: HIGH, Switch2: HIGH
  Switch: First strip only active
  Reconfigured LED strips - Strip1: ON, Strip2: OFF
  Switch: Second strip only active
  Reconfigured LED strips - Strip1: OFF, Strip2: ON
  Switch: Both strips active
  Reconfigured LED strips - Strip1: ON, Strip2: ON
*/
