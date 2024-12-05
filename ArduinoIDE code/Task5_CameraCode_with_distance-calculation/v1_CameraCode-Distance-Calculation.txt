#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <NewPing.h>

// Pin definitions
#define FRONT_TRIGGER_PIN 5  // GPIO5 (D1) for the front sensor trigger
#define FRONT_ECHO_PIN 4     // GPIO4 (D2) for the front sensor echo
#define BACK_TRIGGER_PIN 14  // GPIO14 (D5) for the back sensor trigger
#define BACK_ECHO_PIN 12     // GPIO12 (D6) for the back sensor echo
#define BUZZER_PIN 13        // GPIO13 (D7) for the buzzer
#define MAX_DISTANCE 200     // Maximum measurable distance in cm

NewPing frontSonar(FRONT_TRIGGER_PIN, FRONT_ECHO_PIN, MAX_DISTANCE);
NewPing backSonar(BACK_TRIGGER_PIN, BACK_ECHO_PIN, MAX_DISTANCE);

// Wi-Fi credentials
const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

// ESP8266 Web Server
ESP8266WebServer server(80);

// Overtaking threshold in cm
const int safeDistance = 50;         // Safe distance to avoid warnings
const int overtakingDistanceDiff = 30; // Distance change to detect overtaking
int prevFrontDistance = MAX_DISTANCE; // Store the last distance for comparison

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

  // Buzzer setup
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // Define server route for distance and overtaking data
  server.on("/", []() {
    int frontDistance = frontSonar.ping_cm();
    int backDistance = backSonar.ping_cm();
    bool overtaking = detectOvertaking(frontDistance, backDistance);

    String response = "Front Distance: " + String(frontDistance) + " cm\n";
    response += "Back Distance: " + String(backDistance) + " cm\n";
    response += overtaking ? "Overtaking Detected!\n" : "No Overtaking Detected\n";

    if (frontDistance > 0 && frontDistance < safeDistance) {
      warnProximity(); // Activate buzzer for proximity warning
    } else {
      digitalWrite(BUZZER_PIN, LOW); // Turn off buzzer
    }

    server.send(200, "text/plain", response);
    Serial.println(response);
  });

  server.begin();
  Serial.println("Server started");
}

void loop() {
  server.handleClient();
}

// Function to detect overtaking
bool detectOvertaking(int frontDistance, int backDistance) {
  // Overtaking detected if:
  // - Front distance is reducing significantly
  // - Back distance is increasing
  if (frontDistance > 0 && backDistance > 0 &&
      (prevFrontDistance - frontDistance) > overtakingDistanceDiff &&
      (backDistance - prevFrontDistance) > overtakingDistanceDiff) {
    Serial.println("Overtaking Detected!");
    return true;
  }
  prevFrontDistance = frontDistance; // Update the previous front distance
  return false;
}

// Function to warn proximity with a buzzer
void warnProximity() {
  for (int i = 0; i < 5; i++) { // Create the siren effect
    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
    delay(200);
  }
}
