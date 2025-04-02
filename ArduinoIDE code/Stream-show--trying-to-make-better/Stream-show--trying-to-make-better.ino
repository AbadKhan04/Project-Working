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
uint8_t work[10000];

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
    config.jpeg_quality = 15;            // ✅ Higher compression for stability
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
    static size_t offset = 0;
    camera_fb_t* fb = (camera_fb_t*)jd->device;

    if (!fb) return 0;
    if (offset == 0) Serial.println("✅ Resetting JPEG Read Offset!"); // Debugging

    if (offset + nbyte > fb->len) nbyte = fb->len - offset;

    if (buff) {
        memcpy(buff, fb->buf + offset, nbyte);
    }
    offset += nbyte;

    return nbyte;
}

// // ✅ Updated JPEG Render Function (for jd_decomp)
// int jpgToBuffer(JDEC* jd, void* bitmap, JRECT* rect) {
//     uint16_t* buf = (uint16_t*)bitmap;
//     for (int y = rect->top; y <= rect->bottom; y++) {
//         for (int x = rect->left; x <= rect->right; x++) {
//             uint16_t color = *buf++;
//             tft.drawPixel(x, y, color);
//         }
//     }
//     return 1;
// }

// ✅ Improved JPEG Rendering Function
int jpgToBuffer(JDEC* jd, void* bitmap, JRECT* rect) {
    uint16_t* buf = (uint16_t*)bitmap;
    int w = rect->right - rect->left + 1;
    int h = rect->bottom - rect->top + 1;

    tft.startWrite();
    tft.setAddrWindow(rect->left, rect->top, w, h);

    // for (int i = 0; i < w * h; i++) {
    //     tft.pushColor(buf[i]);
    // }
    tft.pushColors(buf, w * h, true);

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
    Serial.println("Image Captured!");

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

    // offset = 0; // * ✅ Reset offset before decompression

    JDEC jd;
    JRESULT res;
    // uint16_t image[320 * 240];  // ✅ Buffer for image data (320 * 240)

    res = jd_prepare(&jd, jpgRead, work, sizeof(work), fb);
    if (res == JDR_OK) {
      Serial.println("✅ JPEG Decompression Started...");
      jd_decomp(&jd, jpgToBuffer, 0);
    } else {
        // Serial.println("JPEG Decompression Failed");
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
