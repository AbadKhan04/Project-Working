#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <TFT_eSPI.h>      // TFT_eSPI handles SPI communication for ILI9341
#include <TJpg_Decoder.h>  // JPEG decoder for TFT

// Camera pin mapping (example for AI Thinker ESP32-CAM module)
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

// WiFi credentials
const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

// Globals
WebServer server(80);
TFT_eSPI tft = TFT_eSPI();
camera_fb_t* fb = NULL;
SemaphoreHandle_t frameSemaphore;
bool lcdConnected = true; // Assume LCD is connected, fallback if crash

// Debug print macro
#define DEBUG_PRINT(x) Serial.println(x)

// Camera setup function
void setupCamera() {
  DEBUG_PRINT("[setupCamera] Starting camera config");
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
  config.frame_size   = FRAMESIZE_QVGA; // 320x240
  config.jpeg_quality = 10;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    DEBUG_PRINT("[setupCamera] Camera init failed");
    ESP.restart();
  }
  DEBUG_PRINT("[setupCamera] Camera init success");
}

// Handle browser client requests
void handleJPGStream() {
  WiFiClient client = server.client();
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);

  while (client.connected()) {
    fb = esp_camera_fb_get();
    if (!fb) {
      DEBUG_PRINT("[handleJPGStream] Camera capture failed");
      continue;
    }
    
    server.sendContent("--frame\r\n");
    server.sendContent("Content-Type: image/jpeg\r\n\r\n");
    server.sendContent((const char *)fb->buf, fb->len);
    server.sendContent("\r\n");
    
    esp_camera_fb_return(fb);
    delay(50); // Small delay for stability
  }
}

// Corrected Callback for TJpg_Decoder
bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t *bitmap) {
  if (w && h) tft.pushImage(x, y, w, h, bitmap);
  return true;
}


// LCD display task
void lcdTask(void* parameter) {
  TJpgDec.setSwapBytes(true); // Needed for correct color
  TJpgDec.setJpgScale(1);     // No scaling
  TJpgDec.setCallback(tft_output); // Register the correct callback


  while (true) {
    fb = esp_camera_fb_get();
    if (fb) {
      if (lcdConnected) {
        tft.startWrite();
        TJpgDec.drawJpg(0, 0, fb->buf, fb->len);
        tft.endWrite();
      }
      esp_camera_fb_return(fb);
    } else {
      DEBUG_PRINT("[lcdTask] Frame buffer null");
    }
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }
}

// Setup
void setup() {
  Serial.begin(115200);
  DEBUG_PRINT("=== SETUP START ===");

  frameSemaphore = xSemaphoreCreateMutex();
  
  // Init TFT
  tft.init();
  tft.setRotation(1); // Landscape
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("Connecting Wi-Fi...", 10, 10, 2);

  // Connect Wi-Fi
  WiFi.begin(ssid, password);
  DEBUG_PRINT("[setup] Connecting Wi-Fi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  DEBUG_PRINT("");
  DEBUG_PRINT("[setup] Wi-Fi connected, IP = " + WiFi.localIP().toString());

  // Setup camera
  setupCamera();

  // Setup web server
  server.on("/", HTTP_GET, handleJPGStream);
  server.begin();
  DEBUG_PRINT("[setup] Web server started");

  // Start LCD task
  xTaskCreatePinnedToCore(
    lcdTask,
    "LCD Task",
    10000,
    NULL,
    1,
    NULL,
    1
  );
}

// Loop
void loop() {
  server.handleClient();
}
