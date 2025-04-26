#include <Arduino.h>
#include <WiFi.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "tjpgd.h"

// 📶 WiFi Credentials
const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

// TFT Pins and Init
#define TFT_CS  12
#define TFT_RST 2
#define TFT_DC  13
TFT_eSPI tft = TFT_eSPI();

// JPEG buffer
uint8_t work[20000];
size_t jpg_offset = 0;

// ✅ Setup Camera
void setupCamera() {
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
    config.xclk_freq_hz = 10000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.println("❌ Camera Init Failed");
    }
}

// 📦 JPEG Reader
size_t jpgRead(JDEC* jd, uint8_t* buff, size_t nbyte) {
    camera_fb_t* fb = (camera_fb_t*)jd->device;
    if (!fb) return 0;
    if (jpg_offset + nbyte > fb->len) nbyte = fb->len - jpg_offset;
    if (buff) memcpy(buff, fb->buf + jpg_offset, nbyte);
    jpg_offset += nbyte;
    return nbyte;
}

// 🖼️ JPEG to TFT Renderer
int jpgToBuffer(JDEC* jd, void* bitmap, JRECT* rect) {
    uint16_t* buf = (uint16_t*)bitmap;
    int w = rect->right - rect->left + 1;
    int h = rect->bottom - rect->top + 1;
    tft.startWrite();
    tft.setAddrWindow(rect->left, rect->top, w, h);
    tft.pushColors(buf, w * h, true);
    tft.endWrite();
    return 1;
}

// 🖥️ Show Camera Frame on TFT
void displayImage(camera_fb_t* fb) {
    if (!fb) return;

    if (fb->format != PIXFORMAT_JPEG) {
        Serial.println("Invalid Format");
        return;
    }

    jpg_offset = 0;

    JDEC jd;
    JRESULT res = jd_prepare(&jd, jpgRead, work, sizeof(work), fb);
    if (res == JDR_OK) {
        jd_decomp(&jd, jpgToBuffer, 0);
    } else {
        Serial.printf("❌ JPEG Decompression Error: %d\n", res);
    }
}

// 🌐 Stream Handler (Web)
esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len = 0;
    uint8_t *_jpg_buf = NULL;
    char part_buf[64];

    httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");

    while (true) {
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed");
            httpd_resp_send_500(req);
            return ESP_FAIL;
        }

        // 🖼️ Show on TFT
        displayImage(fb);

        if (fb->format != PIXFORMAT_JPEG) {
            bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
            if (!jpeg_converted) {
                Serial.println("JPEG compression failed");
                esp_camera_fb_return(fb);
                return ESP_FAIL;
            }
        } else {
            _jpg_buf = fb->buf;
            _jpg_buf_len = fb->len;
        }

        size_t hlen = snprintf(part_buf, 64,
            "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", _jpg_buf_len);
        res = httpd_resp_send_chunk(req, part_buf, hlen);
        if (res == ESP_OK)
            res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
        if (res == ESP_OK)
            res = httpd_resp_send_chunk(req, "\r\n", 2);

        if (fb->format != PIXFORMAT_JPEG) free(_jpg_buf);
        esp_camera_fb_return(fb);

        if (res != ESP_OK) break;
    }
    return res;
}

// 🚀 Start Camera Web Server
void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    httpd_handle_t server = NULL;

    if (httpd_start(&server, &config) == ESP_OK) {
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

    // 📶 WiFi Connect
    WiFi.setSleep(false);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("✅ WiFi connected");
    Serial.print("🌐 Stream at: http://");
    Serial.println(WiFi.localIP());

    // 🔧 Init Display
    tft.begin();
    tft.setRotation(3);
    tft.fillScreen(TFT_BLACK);

    // 📸 Init Camera
    setupCamera();

    // 🌐 Init Server
    startCameraServer();
}

void loop() {
    delay(1);  // Everything is inside stream handler
}
