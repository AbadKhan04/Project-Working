#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <NewPing.h>

#define TRIGGER_PIN 5  // GPIO5 (D1) on ESP8266
#define ECHO_PIN 4     // GPIO4 (D2) on ESP8266
#define MAX_DISTANCE 200

NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE);

const char* ssid = "ABAD-BB2";  // Replace with your Wi-Fi credentials
const char* password = "Abad723-Linux";

ESP8266WebServer server(80);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/", []() {
    int distance = sonar.ping_cm();
    server.send(200, "text/plain", String(distance));
  });

  server.begin();
  Serial.println("Server started");
}

void loop() {
  server.handleClient();
}
