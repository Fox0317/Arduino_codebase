#include "FastLED.h"

// LED Configuration
#define NUM_LEDS 1000
#define LED_PIN 10
CRGB leds[NUM_LEDS];

void setup() {
  Serial.begin(115200);
  Serial.println("LED Test Starting...");
  
  // Initialize LED strip
  FastLED.addLeds<WS2812, LED_PIN, RGB>(leds, NUM_LEDS);
  FastLED.setBrightness(255);
  
  Serial.print("Testing LED strip on pin ");
  Serial.println(LED_PIN);
  Serial.print("Number of LEDs: ");
  Serial.println(NUM_LEDS);
  
  // Test pattern
  Serial.println("Testing Red...");
  fill_solid(leds, NUM_LEDS, CRGB::Red);
  FastLED.show();
  delay(2000);
  
  Serial.println("Testing Green...");
  fill_solid(leds, NUM_LEDS, CRGB::Green);
  FastLED.show();
  delay(2000);
  
  Serial.println("Testing Blue...");
  fill_solid(leds, NUM_LEDS, CRGB::Blue);
  FastLED.show();
  delay(2000);
  
  Serial.println("Testing White...");
  fill_solid(leds, NUM_LEDS, CRGB::White);
  FastLED.show();
  delay(2000);
  
  Serial.println("Clearing LEDs...");
  FastLED.clear();
  FastLED.show();
  
  Serial.println("LED Test Complete!");
}

void loop() {
  // Simple rainbow pattern
  static uint8_t hue = 0;
  
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV(hue + i * 2, 255, 255);
  }
  
  FastLED.show();
  delay(50);
  hue++;
}
