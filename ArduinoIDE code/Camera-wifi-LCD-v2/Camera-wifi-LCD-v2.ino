#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include <TFT_eSPI.h>  // Include TFT library
#include <SPI.h>

// WiFi credentials
const char* ssid = "ABAD-BB2";
const char* password = "Abad723-Linux";

// TFT Display Object
TFT_eSPI tft = TFT_eSPI();

// Video Stream Handler
esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t *_jpg_buf = NULL;
  char part_buf[64];

  // Set the response type as multipart
  httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      tft.println("Camera capture failed");
      httpd_resp_send_500(req);
      return ESP_FAIL;
    }

    delay(100);  // Prevent memory overflow

    if (fb->format != PIXFORMAT_JPEG) {
      bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
      if (!jpeg_converted) {
        Serial.println("JPEG compression failed");
        esp_camera_fb_return(fb);
        return ESP_FAIL;
      }
    } else {
      _jpg_buf_len = fb->len;
      _jpg_buf = fb->buf;
    }

    // Send the frame header
    size_t hlen = snprintf(part_buf, 64, "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", _jpg_buf_len);
    res = httpd_resp_send_chunk(req, part_buf, hlen);
    if (res == ESP_OK) {
      // Send the actual JPEG image
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    }
    if (res == ESP_OK) {
      // Send the frame boundary
      res = httpd_resp_send_chunk(req, "\r\n", 2);
    }

    if (fb->format != PIXFORMAT_JPEG) {
      free(_jpg_buf);
    }
    esp_camera_fb_return(fb);

    if (res != ESP_OK) {
      break;
    }
  }
  return res;
}

// Start Web Server
void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  // config.stack_size = 8192;  // Increase stack size to prevent crashes
  httpd_handle_t server = NULL;

  if (httpd_start(&server, &config) == ESP_OK) {
    // Register URI handler for the video stream
    httpd_uri_t uri_stream = {
      .uri       = "/stream",
      .method    = HTTP_GET,
      .handler   = stream_handler,
      .user_ctx  = NULL
    };
    httpd_register_uri_handler(server, &uri_stream);
  }
}

void setup() {
  Serial.begin(115200);
  
  // Initialize TFT Display
  tft.init();
  tft.setRotation(3);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);

  tft.setCursor(10, 10);
  tft.println("Connecting WiFi...");
  
  WiFi.setSleep(false);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
    tft.setCursor(10, 40);
    tft.println(".");
  }
  String ipAddress = WiFi.localIP().toString();
  Serial.println("WiFi connected");
  Serial.print("Camera Stream Ready! Go to: http://");
  Serial.println(WiFi.localIP());

  tft.fillScreen(TFT_BLACK);
  tft.setCursor(10, 30);
  tft.println("WiFi Connected!");
  tft.setCursor(10, 60);
  tft.print("IP: ");
  tft.println(ipAddress);
  tft.setCursor(10, 100);
  tft.println("Access stream at:");
  tft.setCursor(10, 130);
  tft.print("http://");
  tft.println(ipAddress);

  // Camera Configuration
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
  config.frame_size = FRAMESIZE_QVGA;  // Lower resolution
  config.jpeg_quality = 20;             // Reduce quality
  config.fb_count = 2;                  // Single buffer

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed! Error: 0x%x", err);
    return;
  }

  startCameraServer();
}

void loop() {
  delay(10);
}
