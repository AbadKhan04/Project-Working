#define TRIG_PIN D2 // Trigger pin connected to D2
#define ECHO_PIN D1 // Echo pin connected to D1

void setup() {
  Serial.begin(115200); // Initialize serial communication
  pinMode(TRIG_PIN, OUTPUT); // Set trigger pin as OUTPUT
  pinMode(ECHO_PIN, INPUT); // Set echo pin as INPUT
}

void loop() {
  long duration, distance;

  // Clear the trigger pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  
  // Set the trigger pin HIGH for 10 microseconds
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read the echo pin and calculate the duration
  duration = pulseIn(ECHO_PIN, HIGH);
  
  // Calculate distance in centimeters (speed of sound = 34300 cm/s)
  distance = duration * 0.034 / 2;

  // Print the distance to the Serial Monitor
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  delay(1000); // Wait for a second before the next measurement
}
