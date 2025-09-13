#include <Arduino.h>
#line 1 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\esp32_led_test\\esp32_led_test.ino"
#include <FastLED.h>

#define LED_PIN 2
#define NUM_LEDS 5
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

CRGB leds[NUM_LEDS];

#line 10 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\esp32_led_test\\esp32_led_test.ino"
void setup();
#line 19 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\esp32_led_test\\esp32_led_test.ino"
void loop();
#line 10 "C:\\Users\\foxwo\\OneDrive\\Documents\\GitHub\\Arduino_codebase\\esp32_led_test\\esp32_led_test.ino"
void setup() {
  Serial.begin(115200);
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(50);
  FastLED.clear();
  FastLED.show();
  Serial.println("LED Test Starting - 5 LEDs");
}

void loop() {
  // Red
  fill_solid(leds, NUM_LEDS, CRGB::Red);
  FastLED.show();
  Serial.println("Red");
  delay(1000);
  
  // Green
  fill_solid(leds, NUM_LEDS, CRGB::Green);
  FastLED.show();
  Serial.println("Green");
  delay(1000);
  
  // Blue
  fill_solid(leds, NUM_LEDS, CRGB::Blue);
  FastLED.show();
  Serial.println("Blue");
  delay(1000);
  
  // White
  fill_solid(leds, NUM_LEDS, CRGB::White);
  FastLED.show();
  Serial.println("White");
  delay(1000);
  
  // Off
  FastLED.clear();
  FastLED.show();
  Serial.println("Off");
  delay(1000);
}
