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
#define RED_LED 16             // 

#define DISTANCE_SELECT_PIN A0
#define MAX_DISTANCE 200      // in cm

NewPing frontSonar(FRONT_TRIGGER_PIN, FRONT_ECHO_PIN, MAX_DISTANCE);
NewPing backSonar(BACK_TRIGGER_PIN, BACK_ECHO_PIN, MAX_DISTANCE);

const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

ESP8266WebServer server(80);

int warningDistance = 150;       // Default: 15m
const int safeDistance = 50;     // Below this is dangerous
const int overtakingDistanceDiff = 30;
int prevFrontDistance = MAX_DISTANCE;

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
  digitalWrite(RED_LED, HIGH);  // Off if using onboard LED (inverted)

  server.on("/", []() {
    int frontDistance = frontSonar.ping_cm();
    int backDistance = backSonar.ping_cm();
    bool overtaking = detectOvertaking(frontDistance, backDistance);

    updateWarningDistance();

    Serial.print("Front: "); Serial.print(frontDistance);
    Serial.print(" | Back: "); Serial.println(backDistance);

    if (frontDistance > 0 && frontDistance < safeDistance) {
      warnProximity(frontDistance);
    } else if (backDistance > 0 && backDistance < safeDistance) {
      warnProximity(backDistance);
    } else {
      digitalWrite(RED_LED, LOW);      // OFF if using onboard LED
      digitalWrite(GREEN_LED, HIGH);    // ON
      digitalWrite(BUZZER_PIN, LOW);
    }

    String jsonResponse = "{";
    jsonResponse += "\"front\":" + String(frontDistance) + ",";
    jsonResponse += "\"back\":" + String(backDistance) + ",";
    jsonResponse += "\"overtaking\":" + String(overtaking ? "true" : "false");
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

// Overtaking detection logic
bool detectOvertaking(int frontDistance, int backDistance) {
  if (frontDistance > 0 && backDistance > 0 &&
      (prevFrontDistance - frontDistance) > overtakingDistanceDiff &&
      (backDistance - prevFrontDistance) > overtakingDistanceDiff) {
    Serial.println("Overtaking Detected!");
    return true;
  }
  prevFrontDistance = frontDistance;
  return false;
}

// Blink RED LED and beep buzzer based on distance
void warnProximity(int distance) {
  Serial.print("Proximity Warning! Distance: ");
  Serial.println(distance);

  int beepDelay = (distance <= 100) ? 100 : 300;

  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    digitalWrite(RED_LED, HIGH);   // ON (for onboard LED, LOW = ON)
    digitalWrite(GREEN_LED, LOW);
    delay(beepDelay);

    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(RED_LED, LOW);  // OFF
    delay(beepDelay);
  }
}

// Dynamically update warning distance
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
