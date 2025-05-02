#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <TFT_eSPI.h>  // For LCD (SPI)

const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

WebServer server(80);
TFT_eSPI tft = TFT_eSPI();  // Setup LCD (adjust pins in User_Setup.h)

void startCameraServer();

// Camera configuration (adjust pins according to your ESP32-CAM module)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
  Serial.begin(115200);

  // Init LCD
  tft.init();
  tft.setRotation(1); // adjust if needed
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("Initializing...", 50, 120, 2);

  // Init WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println(WiFi.localIP());
  
  // Init Camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  config.frame_size = FRAMESIZE_QVGA; // 320x240
  config.jpeg_quality = 10; // better quality
  config.fb_count = 2;
  
  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    while (true);
  }
  
  // Start Server
  startCameraServer();
  
  Serial.println("Camera ready! Use your browser to connect.");
}

void loop() {
  server.handleClient();
}

// Webserver function
void startCameraServer() {
  server.on("/", HTTP_GET, []() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/html", "<html><body><img src='/stream' /></body></html>");
  });

  server.on("/stream", HTTP_GET, []() {
    WiFiClient client = server.client();
    String response = "HTTP/1.1 200 OK\r\n";
    response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
    server.sendContent(response);

    while (client.connected()) {
      camera_fb_t *fb = esp_camera_fb_get();
      if (!fb) {
        Serial.println("Camera capture failed");
        continue;
      }
      
      // Send frame to browser
      String head = "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + String(fb->len) + "\r\n\r\n";
      server.sendContent(head);
      server.sendContent((const char*)fb->buf, fb->len);
      server.sendContent("\r\n");

      // ALSO, draw frame on LCD (frame by frame)
      draw_jpeg_frame_on_lcd(fb->buf, fb->len);

      esp_camera_fb_return(fb);
      delay(50); // 20 fps approx, adjust if needed
    }
  });

  server.begin();
}

// Simple LCD JPEG frame draw function
void draw_jpeg_frame_on_lcd(const uint8_t *buf, size_t len) {
  // Decode JPEG into a bitmap buffer
  // (simplified here, you need JPEG decoding lib if you want real decode)
  // We'll just write raw data simulation

  // Instead, for simplicity here:
  tft.fillScreen(TFT_BLACK);
  tft.drawString("Frame OK", 90, 120, 2);
}
