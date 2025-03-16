#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <NewPing.h>

// Pin definitions
#define FRONT_TRIGGER_PIN 5  // GPIO5 (D1) for the front sensor trigger
#define FRONT_ECHO_PIN 4     // GPIO4 (D2) for the front sensor echo
#define BACK_TRIGGER_PIN 14  // GPIO14 (D5) for the back sensor trigger
#define BACK_ECHO_PIN 12     // GPIO12 (D6) for the back sensor echo
#define BUZZER_PIN 13        // GPIO13 (D7) for the buzzer
#define GREEN_LED 15         // GPIO15 (D8) Green LED (Safe to overtake)
#define RED_LED 2            // GPIO2 (D4) Red LED (Unsafe to overtake)
#define DISTANCE_SELECT_PIN A0 // Analog input for setting alert distance
#define MAX_DISTANCE 200     // Maximum measurable distance in cm

NewPing frontSonar(FRONT_TRIGGER_PIN, FRONT_ECHO_PIN, MAX_DISTANCE);
NewPing backSonar(BACK_TRIGGER_PIN, BACK_ECHO_PIN, MAX_DISTANCE);

// Wi-Fi credentials
const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

// ESP8266 Web Server
ESP8266WebServer server(80);

// Default warning distance (modifiable via a potentiometer or button input)
int warningDistance = 150; // Default 15m (1500cm)
const int safeDistance = 50; // Safe distance threshold
const int overtakingDistanceDiff = 30;
int prevFrontDistance = MAX_DISTANCE;

void setup() {
  Serial.begin(115200);

  // Start WiFi connection
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // LED and buzzer setup
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);

  // Define server route for distance and overtaking data
  server.on("/", []() {
    int frontDistance = frontSonar.ping_cm();
    int backDistance = backSonar.ping_cm();
    bool overtaking = detectOvertaking(frontDistance, backDistance);

    // Update warning distance dynamically
    updateWarningDistance();

    // Handle LED indicators
    if ((frontDistance > 0 && frontDistance < safeDistance) || (backDistance > 0 && backDistance < safeDistance)) {
      warnProximity(frontDistance);
      digitalWrite(RED_LED, HIGH);
      digitalWrite(GREEN_LED, LOW);
    } else {
      digitalWrite(RED_LED, LOW);
      digitalWrite(GREEN_LED, HIGH);
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

// Function to detect overtaking
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

// Function to warn proximity with a buzzer and LED blink effect
void warnProximity(int distance) {
  if (distance > 0 && distance <= warningDistance) {
    int beepDelay = (distance <= 100) ? 100 : 300; // Faster beep if closer than 10m
    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZER_PIN, HIGH);
      digitalWrite(RED_LED, LOW);
      delay(beepDelay);
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(RED_LED, HIGH);
      delay(beepDelay);
    }
  }
}

// Function to update warning distance based on user input
void updateWarningDistance() {
  int sensorValue = analogRead(DISTANCE_SELECT_PIN);
  if (sensorValue < 341) {
    warningDistance = 100; // 10m
  } else if (sensorValue < 682) {
    warningDistance = 150; // 15m
  } else {
    warningDistance = 200; // 20m
  }
  Serial.print("Warning Distance Set To: ");
  Serial.println(warningDistance);
}
