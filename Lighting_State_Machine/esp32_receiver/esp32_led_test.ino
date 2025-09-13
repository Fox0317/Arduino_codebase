/*
 * ESP32 LED Strip Test
 * Tests LED strip connections without WiFi
 * Cycles through different test patterns
 */

#include <FastLED.h>

// LED Configuration
#define LED_PIN 18
#define NUM_LEDS 5  // Adjust based on your strip length
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

// LED array
CRGB leds[NUM_LEDS];

// Test pattern variables
int currentTest = 0;
unsigned long lastUpdate = 0;
unsigned long updateInterval = 2000; // 1 second between test changes
int hue = 0;

// Test patterns
enum TestPattern {
  TEST_RED,
  TEST_GREEN,
  TEST_BLUE,
  TEST_WHITE,
  TEST_RAINBOW,
  TEST_CHASE,
  TEST_TWINKLE,
  TEST_FIRE,
  TEST_BREATHING,
  TEST_OFF
};

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 LED Strip Test Starting...");
  
  // Initialize FastLED
  FastLED.addLeds<WS2812, LED_PIN, RGB>(leds, NUM_LEDS).setCorrection( TypicalLEDStrip );
  FastLED.setBrightness(50); // Start with low brightness
  FastLED.clear();
  FastLED.show();
  
  Serial.println("FastLED initialized");
  Serial.print("Testing ");
  Serial.print(NUM_LEDS);
  Serial.println(" LEDs");
  Serial.println("Test patterns will cycle every second");
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastUpdate >= updateInterval) {
    lastUpdate = currentTime;
    runTest(currentTest);
    currentTest = (currentTest + 1) % 10; // Cycle through all tests
    hue += 10; // Increment hue for rainbow effects
  }
  
  // Update patterns that need continuous animation
  if (currentTest == TEST_RAINBOW) {
    updateRainbow();
  } else if (currentTest == TEST_CHASE) {
    updateChase();
  } else if (currentTest == TEST_TWINKLE) {
    updateTwinkle();
  } else if (currentTest == TEST_FIRE) {
    updateFire();
  } else if (currentTest == TEST_BREATHING) {
    updateBreathing();
  }
  
  FastLED.show();
  delay(50); // Small delay for smooth animation
}

void runTest(int test) {
  Serial.print("Running test ");
  Serial.print(test);
  Serial.print(": ");
  
  switch (test) {
    case TEST_RED:
      Serial.println("Solid Red");
      fill_solid(leds, NUM_LEDS, CRGB::Red);
      break;
      
    case TEST_GREEN:
      Serial.println("Solid Green");
      fill_solid(leds, NUM_LEDS, CRGB::Green);
      break;
      
    case TEST_BLUE:
      Serial.println("Solid Blue");
      fill_solid(leds, NUM_LEDS, CRGB::Blue);
      break;
      
    case TEST_WHITE:
      Serial.println("Solid White");
      fill_solid(leds, NUM_LEDS, CRGB::White);
      break;
      
    case TEST_RAINBOW:
      Serial.println("Rainbow");
      // Rainbow will be updated in updateRainbow()
      break;
      
    case TEST_CHASE:
      Serial.println("Chase Pattern");
      // Chase will be updated in updateChase()
      break;
      
    case TEST_TWINKLE:
      Serial.println("Twinkle");
      FastLED.clear();
      // Twinkle will be updated in updateTwinkle()
      break;
      
    case TEST_FIRE:
      Serial.println("Fire Effect");
      FastLED.clear();
      // Fire will be updated in updateFire()
      break;
      
    case TEST_BREATHING:
      Serial.println("Breathing");
      // Breathing will be updated in updateBreathing()
      break;
      
    case TEST_OFF:
      Serial.println("All Off");
      FastLED.clear();
      break;
  }
}

void updateRainbow() {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV((i * 256 / NUM_LEDS + hue) % 256, 255, 255);
  }
}

void updateChase() {
  static int pos = 0;
  FastLED.clear();
  
  // Create a moving dot
  for (int i = 0; i < 10; i++) {
    int ledIndex = (pos + i) % NUM_LEDS;
    int brightness = 255 - (i * 25);
    leds[ledIndex] = CHSV(hue, 255, brightness);
  }
  
  pos = (pos + 1) % NUM_LEDS;
}

void updateTwinkle() {
  // Randomly twinkle LEDs
  for (int i = 0; i < NUM_LEDS; i++) {
    if (random(100) < 2) { // 2% chance each LED will twinkle
      leds[i] = CRGB(random(256), random(256), random(256));
    } else {
      leds[i].fadeToBlackBy(10); // Fade out
    }
  }
}

void updateFire() {
  // Simple fire effect
  for (int i = 0; i < NUM_LEDS; i++) {
    if (i < NUM_LEDS / 4) {
      // Bottom quarter - hot (white/yellow)
      leds[i] = CRGB(255, random(100, 255), 0);
    } else if (i < NUM_LEDS / 2) {
      // Second quarter - medium (orange/red)
      leds[i] = CRGB(random(150, 255), random(50, 150), 0);
    } else {
      // Top half - cool (red/dark)
      leds[i] = CRGB(random(50, 150), 0, 0);
    }
    
    // Add some randomness
    if (random(100) < 20) {
      leds[i] = CRGB(0, 0, 0);
    }
  }
}

void updateBreathing() {
  static float brightness = 0;
  static float direction = 1;
  
  brightness += direction * 0.02;
  if (brightness >= 1.0) {
    brightness = 1.0;
    direction = -1;
  } else if (brightness <= 0.1) {
    brightness = 0.1;
    direction = 1;
  }
  
  uint8_t brightnessValue = brightness * 255;
  fill_solid(leds, NUM_LEDS, CHSV(hue, 255, brightnessValue));
}

// Print test information
void printTestInfo() {
  Serial.println("\n=== ESP32 LED Strip Test ===");
  Serial.print("LED Pin: ");
  Serial.println(LED_PIN);
  Serial.print("Number of LEDs: ");
  Serial.println(NUM_LEDS);
  Serial.print("LED Type: ");
  Serial.println(LED_TYPE);
  Serial.print("Color Order: ");
  Serial.println(COLOR_ORDER);
  Serial.println("Test patterns cycle every second");
  Serial.println("=============================\n");
}
