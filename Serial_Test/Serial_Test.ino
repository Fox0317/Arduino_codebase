void setup() {
  Serial.begin(115200);
  delay(2000); // Wait for serial to initialize
  Serial.println("ESP32-S3 Serial Test - Working!");
  Serial.println("If you see this, serial communication is working!");
}

void loop() {
  Serial.println("Loop running - " + String(millis()) + " ms");
  delay(1000);
}
