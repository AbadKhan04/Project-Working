#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include "esp_camera.h"
#include "tjpgd.h"

#define TFT_CS  12
#define TFT_RST 2
#define TFT_DC  13

TFT_eSPI tft = TFT_eSPI();

// ✅ Global buffer for JPEG decompression
uint8_t work[20000];

size_t jpg_offset = 0;

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

    config.frame_size = FRAMESIZE_QVGA;  // ✅ 320x240 for better compatibility
    config.jpeg_quality = 10;            // ✅ Higher compression for stability
    config.fb_count = 2;

    // ❌ Disable PSRAM
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.println("Camera Init Failed");
    }
}

// ✅ JPEG Read Function with Proper Offset Handling
size_t jpgRead(JDEC* jd, uint8_t* buff, size_t nbyte) {
    camera_fb_t* fb = (camera_fb_t*)jd->device;

    if (!fb) return 0;

    if (jpg_offset + nbyte > fb->len) nbyte = fb->len - jpg_offset;

    if (buff) {
        memcpy(buff, fb->buf + jpg_offset, nbyte);
    }

    jpg_offset += nbyte;
    return nbyte;
}

// ✅ Improved JPEG Rendering Function
// int jpgToBuffer(JDEC* jd, void* bitmap, JRECT* rect) {
//     uint16_t* buf = (uint16_t*)bitmap;
//     int w = rect->right - rect->left + 1;
//     int h = rect->bottom - rect->top + 1;

//     tft.startWrite();
//     tft.setAddrWindow(rect->left, rect->top, w, h);
//     tft.pushColors(buf, w * h, true);

//     tft.endWrite();
//     return 1;
// }

// Updated JPEG Rendering Function with RGB888 to RGB565 conversion
int jpgToBuffer(JDEC* jd, void* bitmap, JRECT* rect) {
    uint8_t* src = (uint8_t*)bitmap;
    uint16_t lineBuf[320];  // max width of the screen

    int w = rect->right - rect->left + 1;
    int h = rect->bottom - rect->top + 1;

    tft.startWrite();
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            int idx = (y * w + x) * 3;
            uint8_t r = src[idx];
            uint8_t g = src[idx + 1];
            uint8_t b = src[idx + 2];
            // Convert RGB888 to RGB565
            lineBuf[x] = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
        }
        tft.setAddrWindow(rect->left, rect->top + y, w, 1);
        tft.pushColors(lineBuf, w, true);
    }
    tft.endWrite();
    return 1;
}



void displayImage() {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("Camera capture failed");
        return;
    }

    // Serial.println("Image Captured.");
    Serial.println("📸 Image Captured!");

    // * Print first few bytes to check if valid JPEG
    Serial.print("JPEG Data (first 10 bytes): ");
    for (int i = 0; i < 10; i++) {
        Serial.printf("%02X ", fb->buf[i]);
    }
    Serial.println();

    // Ensure the captured format is JPEG
    if (fb->format != PIXFORMAT_JPEG) {
        Serial.println("Invalid format");
        esp_camera_fb_return(fb);
        return;
    }

    jpg_offset = 0; // * ✅ Reset offset before decompression

    JDEC jd;
    JRESULT res;

    res = jd_prepare(&jd, jpgRead, work, sizeof(work), fb);
    if (res == JDR_OK) {
      Serial.println("✅ JPEG Decompression Started...");
      jd_decomp(&jd, jpgToBuffer, 0);
    } else {
        Serial.printf("❌ JPEG Decompression Failed! Error: %d\n", res);
    }

    esp_camera_fb_return(fb);
}

void setup() {
    Serial.begin(115200);
    tft.begin();
    tft.setRotation(3);
    tft.fillScreen(TFT_BLACK);
    setupCamera();
}

void loop() {
    displayImage();
    delay(500);
}
