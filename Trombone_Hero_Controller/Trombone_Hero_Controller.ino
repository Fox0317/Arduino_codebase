/* Get tilt angles on X and Y, and rotation angle on Z
 * Angles are given in degrees
 * 
 * License: MIT
 */

#include "Wire.h"
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP085_U.h>
#include <MPU6050_light.h>
#include <BleMouse.h>
BleMouse bleMouse;
MPU6050 mpu(Wire);
Adafruit_BMP085_Unified bmp = Adafruit_BMP085_Unified(10085);
unsigned long timer = 0;
int desired_pixel = 700;
int current_pixel = 700;
int tomove=0;
int sum = 0;
bool mouseclick = false;
void setup() {
  Serial.begin(115200);

  Wire.begin();
  bleMouse.begin();
  
  byte status = mpu.begin();
  Serial.print(F("MPU6050 status: "));
  Serial.println(status);
  while(status!=0){ } // stop everything if could not connect to MPU6050
  
  Serial.println(F("Calculating offsets, do not move MPU6050"));
  delay(1000);
  // mpu.upsideDownMounting = true; // uncomment this line if the MPU6050 is mounted upside-down
  mpu.calcOffsets(); // gyro and accelero
  Serial.println("Done!\n");
  
  if(!bmp.begin())
  {
    /* There was a problem detecting the BMP085 ... check your connections */
    Serial.print("Ooops, no BMP085 detected ... Check your wiring or I2C ADDR!");
    while(1);
  }
}

void loop() {
  sensors_event_t event;
  bmp.getEvent(&event);
 
  /* Display the results (barometric pressure is measure in hPa) */
  mpu.update();
  desired_pixel = (mpu.getAngleX()*12)+540;
  if (desired_pixel < 0)
  {
    desired_pixel = 0;
  }
  if (desired_pixel > 1080)
  {
    desired_pixel = 1080;
  }
  tomove=desired_pixel-current_pixel;

  bleMouse.move(0,tomove);
  current_pixel=desired_pixel;
    
  if (mouseclick == false && event.pressure>1008)
  {
    mouseclick=true;
  }
  else if(mouseclick == true && event.pressure<1004)
  {
    mouseclick=false;
  }
  else
  {
    
  }
  if (event.pressure)
  {
    /* Display atmospheric pressue in hPa */
    Serial.print("Pressure:    ");
    Serial.print(event.pressure);
    Serial.println(" hPa");
  }
  Serial.print("X : ");
  Serial.print(mpu.getAngleX());
  Serial.print("Desired Pixel : ");
  Serial.print(desired_pixel);
  if (mouseclick==true)
  {
    bleMouse.press(MOUSE_LEFT);
  }
  else
  {
    bleMouse.release(MOUSE_LEFT);
  }
  
}
