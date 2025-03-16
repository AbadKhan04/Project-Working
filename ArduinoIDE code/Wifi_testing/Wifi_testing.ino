#include <WiFi.h>

// Replace with your WiFi credentials
const char* ssid = "ABAD-BB2";
const char* password = "Abad723-Linux";

void setup() {
  pinMode(4, OUTPUT);
    Serial.begin(115200);
    Serial.println("\nConnecting to WiFi...");

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\nWiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
}

void loop() {
    // Nothing needed here for just WiFi connection
    digitalWrite(4, HIGH);
    delay(500);
    digitalWrite(4, LOW);
    delay(500);
}
