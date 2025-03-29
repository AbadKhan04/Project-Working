#include <WiFi.h>
#include <ETH.h>
#include <SPI.h>
#include <Ethernet.h>
#include "esp_camera.h"
#include <WebServer.h>

// 📌 Define W5500 SPI Pins
#define W5500_CS 2
#define W5500_RST 15

// 📌 MAC & Static IP Configuration
byte mac[] = { 0xA0, 0xB7, 0x65, 0x25, 0xBE, 0x08 }; // Your ESP32 MAC Address
IPAddress ip(192, 168, 100, 29);  // Set static IP
EthernetServer server(80);

// 📌 Define Camera Pins (ESP32-CAM OV2640)
#define PWDN_GPIO_NUM    -1
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27
#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22

WebServer webServer(80);

// 📌 Function to Initialize Camera
void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000; // Reduce XCLK to 10MHz
  config.pixel_format = PIXFORMAT_JPEG;  // Use JPEG format
  config.frame_size = FRAMESIZE_QVGA;    // Lower resolution for stability
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("❌ Camera init failed!");
    return;
  }
  Serial.println("✅ Camera Ready!");
}

// 📌 Capture Image & Send to Client
void handleStream() {
  EthernetClient client = server.available(); // ✅ Use EthernetClient
  if (client) {
    Serial.println("📷 Client Connected! Sending Stream...");
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: multipart/x-mixed-replace; boundary=frame");
    client.println();

    while (client.connected()) {
      camera_fb_t *fb = esp_camera_fb_get();
      if (!fb) {
        Serial.println("❌ Camera capture failed!");
        continue;
      }

      client.println("--frame");
      client.println("Content-Type: image/jpeg");
      client.println("Content-Length: " + String(fb->len));
      client.println();
      client.write(fb->buf, fb->len);
      client.println();
      esp_camera_fb_return(fb);

      delay(100);
    }
    client.stop();
    Serial.println("❌ Client Disconnected!");
  }
}

// 📌 Setup Function
void setup() {
  Serial.begin(115200);
  delay(3000);
  
  // 🔹 Initialize W5500 Ethernet
  Serial.println("⏳ Initializing Ethernet...");
  Ethernet.init(W5500_CS);
  Ethernet.begin(mac, ip);

  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    Serial.println("❌ W5500 not found!");
    while (1);
  }
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("❌ Ethernet cable is not connected!");
  } else {
    Serial.println("✅ Ethernet Connected!");
  }

  Serial.print("📡 IP Address: ");
  Serial.println(Ethernet.localIP());

  // 🔹 Initialize Camera
  initCamera();

  // 🔹 Start Server
  server.begin();
  Serial.println("🚀 Stream Ready! Open: http://" + Ethernet.localIP().toString());
}

// 📌 Loop Function
void loop() {
  handleStream();
}
