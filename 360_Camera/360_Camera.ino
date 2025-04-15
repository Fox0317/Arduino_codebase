#include <AccelStepper.h>

// Define stepper motor connections and motor interface type. Motor interface type must be set to 1 when using a driver:
#define dirPin 5
#define stepPin 6
#define enablePin 13
#define motorInterfaceType 1
bool torun = false;
int counter = 0;
int tomove = 1200;
// Create a new instance of the AccelStepper class:
AccelStepper stepper = AccelStepper(motorInterfaceType, stepPin, dirPin);


void setup()
{
Serial.begin(9600);
pinMode(8, OUTPUT);
pinMode(enablePin, OUTPUT);
pinMode(2, INPUT_PULLUP);
stepper.setMaxSpeed(500);
stepper.setAcceleration(85);
digitalWrite(enablePin, LOW);
}
void loop()
{
  counter = 0;
  while(digitalRead(2)==LOW)
  {
  
    counter++;
    torun=true;
    delay(20);
  }
  if(counter>=180)
  {
    tomove=6350;
  }

  else if(counter>=50)
  {
    tomove=3900;
  }
  else
  {
    tomove=1200;
  }

  if(torun==true)
  {
  delay(5000);
  digitalWrite(8,HIGH);
  delay(200);
  digitalWrite(8,LOW);
  delay(1200);
  // Set the target position:
  digitalWrite(enablePin,HIGH);
  stepper.move(tomove);
  stepper.runToPosition();
  delay(500);
  digitalWrite(enablePin,LOW);
  delay(1500);
  digitalWrite(8,HIGH);
  delay(200);
  digitalWrite(8,LOW);
  torun=false;
  }
  else{}
  torun=false;
}
