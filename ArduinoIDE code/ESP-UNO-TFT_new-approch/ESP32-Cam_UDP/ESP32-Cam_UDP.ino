#include <WiFi.h>
#include "esp_camera.h"
#include <WiFiUdp.h>

// WiFi credentials
const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

// UDP target IP and port (Receiver ESP32-WROOM or Laptop)
const char* udpTargetIP = "192.168.137.164"; 
const uint16_t udpPort = 1069;

WiFiUDP udp;

void startCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;
  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Camera settings
  config.frame_size = FRAMESIZE_QVGA; // 320x240
  config.jpeg_quality = 20;
  config.fb_count = 1;

  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return;
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("Booting...");

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("ESP32-CAM IP: ");
  Serial.println(WiFi.localIP());

  udp.begin(udpPort);

  startCamera();
}

void loop() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  // Split image into 1024 byte chunks
  const size_t packetSize = 1024;
  for (size_t i = 0; i < fb->len; i += packetSize) {
    size_t chunkSize = min((size_t)packetSize, fb->len - i);
    udp.beginPacket(udpTargetIP, udpPort);
    udp.write(fb->buf + i, chunkSize);
    udp.endPacket();
    delay(1); // Small delay for receiver to catch up
  }

  esp_camera_fb_return(fb);
  delay(30); // ~30 FPS
}
