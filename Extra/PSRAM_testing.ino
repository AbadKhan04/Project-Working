void setup() {
  Serial.begin(115200);
  if (psramFound()) {
    Serial.println("PSRAM is enabled");
  } else {
    Serial.println("PSRAM is not available");
  }
}

void loop() {
}
