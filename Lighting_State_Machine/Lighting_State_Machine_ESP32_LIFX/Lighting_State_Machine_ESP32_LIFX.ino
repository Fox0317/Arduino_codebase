#include "FastLED.h"
#include <WiFi.h>
#include <ArduinoWebsockets.h>

// LED Configuration - Three sections of 1000 LEDs each
#define NUM_LEDS 1000  // Each section has 1000 LEDs
#define LED_PIN1 10    // First section (LEDs 1-1000)
#define LED_PIN2 18    // Second section (LEDs 1001-2000)
#define LED_PIN3 19    // Third section (LEDs 2001-3000)
CRGB leds[NUM_LEDS];

// LED Strip Control Switch Configuration
#define STRIP1_SWITCH_PIN 5  // GPIO 5 for first strip switch
#define STRIP2_SWITCH_PIN 6  // GPIO 6 for second strip switch
#define STRIP3_SWITCH_PIN 7  // GPIO 7 for third strip switch

// LED strip control variables
bool strip1Active = true;
bool strip2Active = true;
bool strip3Active = true;

// KY-040 Encoder Configuration
#define ENCODER_CLK D2
#define ENCODER_DT D3
#define ENCODER_SW D4

// Encoder variables
volatile int encoderValue = 0;
volatile int lastEncoderValue = 0;
volatile bool encoderButtonPressed = false;
volatile unsigned long lastButtonPress = 0;
volatile bool buttonState = false;
volatile bool buttonHeld = false; // Track if button is being held
volatile int encoderStepCounter = 0; // Counter for detent handling

// State machine variables
enum LightingMode {
  MODE_WHITE = 0,
  MODE_RED,
  MODE_YELLOW,
  MODE_GREEN,
  MODE_CYAN,
  MODE_BLUE,
  MODE_MAGENTA,
  MODE_SOLID_COLOR,
  MODE_RAINBOW,
  MODE_FIRE,
  MODE_AURORA,
  MODE_RAINBOW_CHASE,
  MODE_COMET,
  MODE_TWINKLE,
  MODE_WAVE,
  MODE_CHASE,
  MODE_BREATHING,
  NUM_MODES
};

int currentMode = MODE_WHITE;
int brightness = 255;
unsigned long lastModeChange = 0;

// Animation variables
unsigned long lastUpdate = 0;
int animationStep = 0;
int hue = 0;
int fireHeat[NUM_LEDS];
int twinkleState[NUM_LEDS];

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Network communication
bool wifiConnected = false;


void setup() {
  Serial.begin(115200);
  Serial.println("Lighting State Machine ESP32 Starting...");
  
  // Initialize WiFi
  setupWiFi();
  
  // Initialize LED strips for three sections
  FastLED.addLeds<WS2812, LED_PIN1, RGB>(leds, NUM_LEDS).setCorrection( TypicalLEDStrip );
  FastLED.addLeds<WS2812, LED_PIN2, RGB>(leds, NUM_LEDS).setCorrection( TypicalLEDStrip );
  FastLED.addLeds<WS2812, LED_PIN3, RGB>(leds, NUM_LEDS).setCorrection( TypicalLEDStrip );
  FastLED.setBrightness(brightness);
  
  // Check initial switch states
  checkLEDStripSwitches();
  
  // Initialize encoder pins
  pinMode(ENCODER_CLK, INPUT_PULLUP);
  pinMode(ENCODER_DT, INPUT_PULLUP);
  pinMode(ENCODER_SW, INPUT_PULLUP);
  
  // Initialize LED strip control switch pins
  pinMode(STRIP1_SWITCH_PIN, INPUT_PULLUP);
  pinMode(STRIP2_SWITCH_PIN, INPUT_PULLUP);
  pinMode(STRIP3_SWITCH_PIN, INPUT_PULLUP);
  
  // Attach interrupts for encoder
  attachInterrupt(digitalPinToInterrupt(ENCODER_CLK), encoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_SW), buttonISR, FALLING);
  
  // Initialize animation arrays
  for (int i = 0; i < NUM_LEDS; i++) {
    fireHeat[i] = 0;
    twinkleState[i] = random(256);
  }
  
  
  Serial.println("Lighting State Machine ESP32 Started");
}

void loop() {
  handleEncoderInput();
  updateLightingMode();
  
  // Check LED strip switches
  static unsigned long lastSwitchCheck = 0;
  if (millis() - lastSwitchCheck > 50) { // Check switches every 50ms
    checkLEDStripSwitches();
    lastSwitchCheck = millis();
  }
  
  
  FastLED.show();
}

// Encoder interrupt service routine
void encoderISR() {
  static unsigned long lastInterruptTime = 0;
  unsigned long interruptTime = millis();
  
  if (interruptTime - lastInterruptTime > 5) { // Debounce
    int clkState = digitalRead(ENCODER_CLK);
    int dtState = digitalRead(ENCODER_DT);
    
    if (clkState != dtState) {
      encoderStepCounter++;
    } else {
      encoderStepCounter--;
    }
    
    // Check if button is held for brightness adjustment
    bool buttonCurrentlyHeld = !digitalRead(ENCODER_SW); // Button is active low
    
    if (buttonCurrentlyHeld) {
      // Button is held - adjust brightness
      if (encoderStepCounter >= 1) {
        brightness = constrain(brightness + 12, 0, 255);
        FastLED.setBrightness(brightness);
        encoderStepCounter = 0;
        
        Serial.print("Brightness increased to: ");
        Serial.println(brightness);
      } else if (encoderStepCounter <= -1) {
        brightness = constrain(brightness - 12, 0, 255);
        FastLED.setBrightness(brightness);
        encoderStepCounter = 0;
        
        Serial.print("Brightness decreased to: ");
        Serial.println(brightness);
      }
    } else {
      // Button not held - change mode
      if (encoderStepCounter >= 2) {
        encoderValue++;
        if (encoderValue >= NUM_MODES) encoderValue = 0;
        encoderStepCounter = 0;
        
        currentMode = encoderValue;
        lastModeChange = millis();
        
        Serial.print("Mode changed to: ");
        Serial.println(currentMode);
      } else if (encoderStepCounter <= -2) {
        encoderValue--;
        if (encoderValue < 0) encoderValue = NUM_MODES - 1;
        encoderStepCounter = 0;
        
        currentMode = encoderValue;
        lastModeChange = millis();
        
        Serial.print("Mode changed to: ");
        Serial.println(currentMode);
      }
    }
  }
  lastInterruptTime = interruptTime;
}

// Button interrupt service routine
void buttonISR() {
  static unsigned long lastButtonInterruptTime = 0;
  unsigned long interruptTime = millis();
  
  if (interruptTime - lastButtonInterruptTime > 200) { // Debounce
    encoderButtonPressed = true;
    Serial.println("Button pressed");
  }
  lastButtonInterruptTime = interruptTime;
}

void handleEncoderInput() {
  if (encoderButtonPressed) {
    encoderButtonPressed = false;
    // Button functionality handled in ISR
  }
}

void updateLightingMode() {
  switch (currentMode) {
    case MODE_WHITE:
      modeWhite();
      break;
    case MODE_RED:
      modeRed();
      break;
    case MODE_YELLOW:
      modeYellow();
      break;
    case MODE_GREEN:
      modeGreen();
      break;
    case MODE_CYAN:
      modeCyan();
      break;
    case MODE_BLUE:
      modeBlue();
      break;
    case MODE_MAGENTA:
      modeMagenta();
      break;
    case MODE_SOLID_COLOR:
      modeSolidColor();
      break;
    case MODE_RAINBOW:
      modeRainbow();
      break;
    case MODE_FIRE:
      modeFire();
      break;
    case MODE_AURORA:
      modeAurora();
      break;
    case MODE_RAINBOW_CHASE:
      modeRainbowChase();
      break;
    case MODE_COMET:
      modeComet();
      break;
    case MODE_TWINKLE:
      modeTwinkle();
      break;
    case MODE_WAVE:
      modeWave();
      break;
    case MODE_CHASE:
      modeChase();
      break;
    case MODE_BREATHING:
      modeBreathing();
      break;
  }
}

// Lighting Mode Functions

void modeWhite() {
  fill_solid(leds, NUM_LEDS, CRGB::White);
}

void modeSolidColor() {
  fill_solid(leds, NUM_LEDS, CHSV(hue, 255, 255));
  EVERY_N_MILLISECONDS(100) {
    hue++;
  }
}

void modeRed() {
  fill_solid(leds, NUM_LEDS, CRGB::Red);
}

void modeYellow() {
  fill_solid(leds, NUM_LEDS, CRGB::Yellow);
}

void modeGreen() {
  fill_solid(leds, NUM_LEDS, CRGB::Green);
}

void modeCyan() {
  fill_solid(leds, NUM_LEDS, CRGB::Cyan);
}

void modeBlue() {
  fill_solid(leds, NUM_LEDS, CRGB::Blue);
}

void modeMagenta() {
  fill_solid(leds, NUM_LEDS, CRGB::Magenta);
}

void modeFire() {
  // Cool down every cell a little
  for (int i = 0; i < NUM_LEDS; i++) {
    fireHeat[i] = qsub8(fireHeat[i], random8(2));
  }
  
  // Create a temporary array to store new heat values
  static uint8_t newHeat[NUM_LEDS];
  
  // Heat diffuses in both directions for horizontal strip
  for (int i = 0; i < NUM_LEDS; i++) {
    uint8_t leftHeat = (i > 0) ? fireHeat[i - 1] : 0;
    uint8_t rightHeat = (i < NUM_LEDS - 1) ? fireHeat[i + 1] : 0;
    uint8_t currentHeat = fireHeat[i];
    
    // Average heat from current position and adjacent positions
    newHeat[i] = (leftHeat + currentHeat + rightHeat) / 3;
    
    // Add some randomness for natural fire movement
    if (random8() < 50) {
      newHeat[i] = qadd8(newHeat[i], random8(10));
    }
  }
  
  // Copy new heat values back to main array
  for (int i = 0; i < NUM_LEDS; i++) {
    fireHeat[i] = newHeat[i];
  }
  
  // Randomly ignite new sparks across the strip
  if (random8() < 120) {
    int sparkPos = random8(NUM_LEDS);
    fireHeat[sparkPos] = qadd8(fireHeat[sparkPos], random8(160, 255));
  }
  
  // Add some additional sparks for more dynamic fire
  if (random8() < 60) {
    int sparkPos = random8(NUM_LEDS);
    fireHeat[sparkPos] = qadd8(fireHeat[sparkPos], random8(100, 200));
  }
  
  // Map from heat cells to LED colors
  for (int j = 0; j < NUM_LEDS; j++) {
    CRGB color = HeatColor(fireHeat[j]);
    leds[j] = color;
  }
}

void modeAurora() {
  // Aurora borealis animation with green, purple, and pink hues only
  static uint16_t auroraHue = 96; // Start with green (16-bit for smoother transitions)
  static uint16_t auroraPhase = 0; // 16-bit for smoother wave movement
  static uint8_t auroraIntensity[NUM_LEDS];
  static uint8_t sparkleTimer = 0;
  
  // Define our aurora color palette (green, purple, pink)
  uint8_t auroraColors[] = {96, 192, 224}; // Green, Purple, Pink
  uint8_t numColors = 3;
  
  // Create flowing aurora effect with color feathering
  for (int i = 0; i < NUM_LEDS; i++) {
    // Create multiple wave patterns for aurora movement with smoother transitions
    uint8_t wave1 = sin8((auroraPhase + i * 2) % 256);           // Slower primary wave
    uint8_t wave2 = sin8((auroraPhase * 0.6 + i * 3) % 256);    // Medium secondary wave
    uint8_t wave3 = sin8((auroraPhase * 0.3 + i * 1) % 256);    // Slow tertiary wave
    
    // Combine waves with weighted averaging for more natural movement
    uint16_t combinedWave = (wave1 * 2 + wave2 + wave3) / 4;
    
    // Create aurora intensity based on wave patterns
    auroraIntensity[i] = combinedWave;
    
    // Calculate color blending with feathering
    float colorPosition = (float)combinedWave / 256.0;  // Normalize to 0.0-1.0
    float colorIndexFloat = colorPosition * (numColors - 1);  // Get floating point color index
    
    // Get the two colors to blend between
    int colorIndex1 = (int)colorIndexFloat;
    int colorIndex2 = min(colorIndex1 + 1, numColors - 1);
    float blendFactor = colorIndexFloat - colorIndex1;  // 0.0 to 1.0 blend factor
    
    // Get the two base colors
    uint8_t hue1 = auroraColors[colorIndex1];
    uint8_t hue2 = auroraColors[colorIndex2];
    
    // Blend between the two colors using HSV interpolation
    uint8_t currentHue;
    if (blendFactor < 0.1) {
      // Use first color when very close
      currentHue = hue1;
    } else if (blendFactor > 0.9) {
      // Use second color when very close
      currentHue = hue2;
    } else {
      // Smooth blend between colors
      currentHue = hue1 + (uint8_t)((hue2 - hue1) * blendFactor);
    }
    
    // Add subtle variation to the hue for more natural look (limited range)
    currentHue += random8(-12, 12);
    
    // Create the aurora color with varying saturation and brightness
    uint8_t saturation = 200 + random8(40);  // Reduced random range
    uint8_t brightness = 120 + combinedWave / 3;  // Adjusted brightness calculation
    
    leds[i] = CHSV(currentHue, saturation, brightness);
  }
  
  // Apply subtle blur/feathering between adjacent LEDs for smoother transitions
  static uint8_t blurPasses = 0;
  EVERY_N_MILLISECONDS(100) {
    blurPasses++;
    if (blurPasses >= 3) {  // Apply blur every 3rd pass for subtle effect
      blurPasses = 0;
      
      // Create temporary array for blurring
      CRGB tempLeds[NUM_LEDS];
      memcpy(tempLeds, leds, sizeof(leds));
      
      // Apply subtle blur to smooth out color transitions
      for (int i = 1; i < NUM_LEDS - 1; i++) {
        // Blend with adjacent LEDs (subtle effect)
        leds[i] = blend(tempLeds[i-1], tempLeds[i], 240);  // 240 = 94% current, 6% previous
        leds[i] = blend(leds[i], tempLeds[i+1], 240);     // 240 = 94% current, 6% next
      }
      
      // Handle edge cases
      leds[0] = blend(tempLeds[0], tempLeds[1], 240);
      leds[NUM_LEDS-1] = blend(tempLeds[NUM_LEDS-1], tempLeds[NUM_LEDS-2], 240);
    }
  }
  
  // Slowly shift the aurora colors (smoother transition)
  EVERY_N_MILLISECONDS(150) {  // Slower color shift
    auroraHue += 1;
    if (auroraHue >= 256) auroraHue = 0;  // Prevent overflow
  }
  
  // Update the wave phase for flowing movement (smoother)
  EVERY_N_MILLISECONDS(40) {  // Slightly faster for smoother movement
    auroraPhase += 1;  // Smaller increment for smoother waves
    if (auroraPhase >= 1000) auroraPhase = 0;  // Reset at higher value to avoid jarring transitions
  }
  
  // Add sparkles with better timing and positioning
  EVERY_N_MILLISECONDS(300) {  // Slower sparkle rate
    sparkleTimer++;
    
    // Add 2-4 sparkles per cycle for more natural effect
    uint8_t numSparkles = 2 + (sparkleTimer % 3);
    
    for (int s = 0; s < numSparkles; s++) {
      if (random8() < 40) {  // Reduced probability
        int sparklePos = random8(NUM_LEDS);
        uint8_t sparkleColor = auroraColors[random8(numColors)];
        
        // Create softer sparkles that blend better
        uint8_t sparkleBrightness = 180 + random8(75);
        leds[sparklePos] = CHSV(sparkleColor, 255, sparkleBrightness);
      }
    }
  }
}

void modeRainbow() {
  fill_rainbow(leds, NUM_LEDS, hue, 255 / NUM_LEDS);
  EVERY_N_MILLISECONDS(50) {
    hue++;
  }
}


void modeTwinkle() {
  fadeToBlackBy(leds, NUM_LEDS, 20);
  
  for (int i = 0; i < NUM_LEDS; i++) {
    if (random8() < 20) {
      leds[i] += CHSV(random8(), 255, 255);
    }
  }
}

void modeWave() {
  for (int i = 0; i < NUM_LEDS; i++) {
    int wave = sin8(animationStep + i * 8);
    leds[i] = CHSV(hue + i * 2, 255, wave);
  }
  EVERY_N_MILLISECONDS(50) {
    animationStep++;
  }
  EVERY_N_MILLISECONDS(100) {
    hue++;
  }
}

void modeChase() {
  FastLED.clear();
  int pos = (animationStep / 2) % NUM_LEDS;
  leds[pos] = CHSV(hue, 255, 255);
  leds[(pos + 1) % NUM_LEDS] = CHSV(hue, 255, 128);
  leds[(pos + 2) % NUM_LEDS] = CHSV(hue, 255, 64);
  
  EVERY_N_MILLISECONDS(100) {
    animationStep++;
  }
  EVERY_N_MILLISECONDS(2000) {
    hue += 64;
  }
}

void modeBreathing() {
  int breath = sin8(animationStep);
  fill_solid(leds, NUM_LEDS, CHSV(hue, 255, breath));
  
  EVERY_N_MILLISECONDS(50) {
    animationStep++;
  }
  EVERY_N_MILLISECONDS(5000) {
    hue += 64;
  }
}

void modeRainbowChase() {
  FastLED.clear();
  for (int i = 0; i < 3; i++) {
    int pos = (animationStep + i * NUM_LEDS / 3) % NUM_LEDS;
    leds[pos] = CHSV(hue + i * 85, 255, 255);
  }
  
  EVERY_N_MILLISECONDS(100) {
    animationStep++;
  }
  EVERY_N_MILLISECONDS(100) {
    hue++;
  }
}

void modeComet() {
  fadeToBlackBy(leds, NUM_LEDS, 20);
  
  int pos = animationStep % NUM_LEDS;
  leds[pos] = CHSV(hue, 255, 255);
  leds[(pos + 1) % NUM_LEDS] = CHSV(hue, 255, 128);
  leds[(pos + 2) % NUM_LEDS] = CHSV(hue, 255, 64);
  
  EVERY_N_MILLISECONDS(100) {
    animationStep++;
  }
  EVERY_N_MILLISECONDS(2000) {
    hue += 64;
  }
}

// WiFi and Network Communication Functions

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


void checkLEDStripSwitches() {
  // Read switch states (active low due to INPUT_PULLUP)
  bool switch1Low = !digitalRead(STRIP1_SWITCH_PIN);
  bool switch2Low = !digitalRead(STRIP2_SWITCH_PIN);
  bool switch3Low = !digitalRead(STRIP3_SWITCH_PIN);
  
  // Update strip active states based on switch positions
  // Check for individual strip activation
  if (switch1Low && !switch2Low && !switch3Low) {
    // Only first strip active
    if (strip1Active != true || strip2Active != false || strip3Active != false) {
      strip1Active = true;
      strip2Active = false;
      strip3Active = false;
      reconfigureLEDStrips();
      Serial.println("Switch: First strip only active");
    }
  } else if (!switch1Low && switch2Low && !switch3Low) {
    // Only second strip active
    if (strip1Active != false || strip2Active != true || strip3Active != false) {
      strip1Active = false;
      strip2Active = true;
      strip3Active = false;
      reconfigureLEDStrips();
      Serial.println("Switch: Second strip only active");
    }
  } else if (!switch1Low && !switch2Low && switch3Low) {
    // Only third strip active
    if (strip1Active != false || strip2Active != false || strip3Active != true) {
      strip1Active = false;
      strip2Active = false;
      strip3Active = true;
      reconfigureLEDStrips();
      Serial.println("Switch: Third strip only active");
    }
  } else if (!switch1Low && !switch2Low && !switch3Low) {
    // All strips active (default behavior)
    if (strip1Active != true || strip2Active != true || strip3Active != true) {
      strip1Active = true;
      strip2Active = true;
      strip3Active = true;
      reconfigureLEDStrips();
      Serial.println("Switch: All strips active");
    }
  } else {
    // Multiple switches low or invalid state - default to all strips active
    if (strip1Active != true || strip2Active != true || strip3Active != true) {
      strip1Active = true;
      strip2Active = true;
      strip3Active = true;
      reconfigureLEDStrips();
      Serial.println("Switch: Invalid state, defaulting to all strips");
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
  if (strip3Active) {
    FastLED.addLeds<WS2812, LED_PIN3, RGB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  }
  
  // Set brightness
  FastLED.setBrightness(brightness);
  
  Serial.print("Reconfigured LED strips - Strip1: ");
  Serial.print(strip1Active ? "ON" : "OFF");
  Serial.print(", Strip2: ");
  Serial.print(strip2Active ? "ON" : "OFF");
  Serial.print(", Strip3: ");
  Serial.println(strip3Active ? "ON" : "OFF");
}


