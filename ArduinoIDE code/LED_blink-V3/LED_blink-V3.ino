#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <NewPing.h>

// Pin definitions
#define FRONT_TRIGGER_PIN 5   // GPIO5 (D1)
#define FRONT_ECHO_PIN 4      // GPIO4 (D2)
#define BACK_TRIGGER_PIN 14   // GPIO14 (D5)
#define BACK_ECHO_PIN 12      // GPIO12 (D6)
#define BUZZER_PIN 13         // GPIO13 (D7)
#define GREEN_LED 15          // GPIO15 (D8)
#define RED_LED 16            // Define only if GPIO16 used externally
#define DISTANCE_SELECT_PIN A0

#define MAX_DISTANCE 200

NewPing frontSonar(FRONT_TRIGGER_PIN, FRONT_ECHO_PIN, MAX_DISTANCE);
NewPing backSonar(BACK_TRIGGER_PIN, BACK_ECHO_PIN, MAX_DISTANCE);

const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

ESP8266WebServer server(80);

int warningDistance = 150;       // Default warning distance
const int safeDistance = 50;     // Critical warning if below

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

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH); // Off (if onboard LED is active low)

  server.on("/", []() {
    int frontDistance = frontSonar.ping_cm();
    int backDistance = backSonar.ping_cm();

    updateWarningDistance();

    Serial.print("Front: "); Serial.print(frontDistance);
    Serial.print(" | Back: "); Serial.println(backDistance);

    if ((frontDistance > 0 && frontDistance < safeDistance) ||
        (backDistance > 0 && backDistance < safeDistance)) {
      int dangerDistance = min(frontDistance, backDistance);
      warnProximity(dangerDistance);
    } else {
      digitalWrite(RED_LED, LOW);
      digitalWrite(GREEN_LED, HIGH);
      digitalWrite(BUZZER_PIN, LOW);
    }

    String jsonResponse = "{";
    jsonResponse += "\"front\":" + String(frontDistance) + ",";
    jsonResponse += "\"back\":" + String(backDistance);
    jsonResponse += "}";

    server.send(200, "application/json", jsonResponse);
    Serial.println(jsonResponse);
  });

  server.begin();
  Serial.println("Server started");
}

void loop() {
  server.handleClient();
}

// Beep and blink red LED if too close
void warnProximity(int distance) {
  Serial.print("Proximity Warning! Distance: ");
  Serial.println(distance);

  int beepDelay = (distance <= 100) ? 100 : 300;

  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
    delay(beepDelay);
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(RED_LED, LOW);
    delay(beepDelay);
  }
}

// Adjust warning distance using analog input
void updateWarningDistance() {
  int sensorValue = analogRead(DISTANCE_SELECT_PIN);
  if (sensorValue < 341) {
    warningDistance = 100;
  } else if (sensorValue < 682) {
    warningDistance = 150;
  } else {
    warningDistance = 200;
  }
  Serial.print("Warning Distance Set To: ");
  Serial.println(warningDistance);
}
