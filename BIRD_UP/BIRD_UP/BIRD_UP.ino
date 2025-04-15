#include <Adafruit_NeoPixel.h>

#define LED_PIN 4
uint16_t current1 = 0;
uint16_t current2 = 32768;
uint16_t random1 = 32768;
uint16_t random2 = 0;
int result = 0;
int dir1 = 1;
int dir2 = -1;
bool switch1 = false;
// How many NeoPixels are attached to the Arduino?
#define LED_COUNT 6

// Declare our NeoPixel strip object:
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
void setup() {
  strip.begin();
  pinMode(0, INPUT);
  strip.show(); // Initialize all pixels to 'off'
  strip.setBrightness(255);
}

void loop() {

strip.setPixelColor(0, strip.Color(255, 255, 255));
strip.setPixelColor(1, strip.Color(255, 255, 255));
strip.setPixelColor(2, strip.Color(255, 255, 255));
strip.setPixelColor(3, strip.Color(255, 255, 255));
strip.setPixelColor(4, strip.Color(255, 255, 255));
strip.setPixelColor(5, strip.Color(255, 255, 255));
strip.show();


  // put your main code here, to run repeatedly:
  if(digitalRead(0)==HIGH)
  {
    switch1=true;
  }
  
while(switch1==true)
  {
    if (current1!=random1)
  {
    current1=current1+dir1;
  }
  
  else
  {
    random1 = random(65536);
    result = random(1);
    if (result == 0)
    {
      dir1 = 1;
    }
    else
    {
      dir1 = -1;
    }
  }
  
  if (current2!=random2)
  {
    current2=current2+dir2;
  }
  else
  {
    random2 = random(65536);
    result = random(1);
    if (result == 0)
    {
      dir2 = 1;
    }
    else
    {
      dir2 = -1;
    }
  }
  
  uint32_t rgbcolor1 = strip.ColorHSV(current1);
  uint32_t rgbcolor2 = strip.ColorHSV(current2);
  
  strip.setPixelColor(0, rgbcolor1);
  strip.setPixelColor(1, rgbcolor2);
  strip.setPixelColor(2, rgbcolor1);
  strip.setPixelColor(3, rgbcolor1);
  strip.setPixelColor(4, rgbcolor2);
  strip.setPixelColor(5, rgbcolor1);
  strip.show();
  if(digitalRead(0)==LOW)
    {
      switch1=false;
    }
  }
}
