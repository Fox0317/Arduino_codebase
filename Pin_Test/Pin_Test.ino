// Simple Pin Test - Toggle pin 10 every 5 seconds
#define TEST_PIN 10

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("Pin Test Starting...");
  
  // Set pin 10 as output
  pinMode(TEST_PIN, OUTPUT);
  
  Serial.print("Testing pin ");
  Serial.println(TEST_PIN);
  Serial.println("Pin will toggle HIGH/LOW every 5 seconds");
}

void loop() {
  // Turn pin HIGH
  Serial.println("Pin HIGH");
  digitalWrite(TEST_PIN, HIGH);
  delay(5000);
  
  // Turn pin LOW
  Serial.println("Pin LOW");
  digitalWrite(TEST_PIN, LOW);
  delay(5000);
}
