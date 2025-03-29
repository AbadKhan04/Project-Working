#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

const char* ssid = "ABAD-BB2";       // Replace with your WiFi SSID
const char* password = "Abad723-Linux"; // Replace with your WiFi Password

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("\nConnected to WiFi!");

  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());  // Print assigned IP

  Serial.print("ESP32 MAC Address: ");
  Serial.println(WiFi.macAddress());  // Print MAC Address
}

void loop() {
}
