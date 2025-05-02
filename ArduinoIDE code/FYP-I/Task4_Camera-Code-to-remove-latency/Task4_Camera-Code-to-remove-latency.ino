#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// Replace with your network credentials
const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

// Function to handle video streaming
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
      httpd_resp_send_500(req);
      return ESP_FAIL;
    }

    if (fb->format != PIXFORMAT_JPEG) {
      // Convert to JPEG if necessary
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

// Function to start the web server
void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
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

  // Disable WiFi power saving mode for reduced latency
  WiFi.setSleep(false);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("WiFi connected");
  Serial.print("Camera Stream Ready! Go to: http://");
  Serial.println(WiFi.localIP());

  // Camera configuration
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
  config.frame_size = FRAMESIZE_VGA; // Lower resolution for faster stream
  config.jpeg_quality = 12;          // Reduce image quality to decrease delay
  config.fb_count = 1;               // Use single frame buffer for lower latency

  // Initialize the camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // Start the web server
  startCameraServer();
}

void loop() {
  delay(1);
}
