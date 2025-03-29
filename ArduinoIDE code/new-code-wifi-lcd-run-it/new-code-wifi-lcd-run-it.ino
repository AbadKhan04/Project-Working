#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include "esp_camera.h"
#include "tjpgd.h"

#define TFT_CS     15
#define TFT_RST    2
#define TFT_DC     4

TFT_eSPI tft = TFT_eSPI();

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
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.println("Camera Init Failed");
    }
}

// JPEG Read Function (for jd_prepare)
size_t jpgRead(JDEC* jd, uint8_t* buff, size_t nbyte) {
    camera_fb_t* fb = (camera_fb_t*)jd->device;
    if (!fb) return 0;

    if (buff) {
        memcpy(buff, fb->buf, nbyte);
    }
    return nbyte;
}

// JPEG Render Function (for jd_decomp)
int jpgToBuffer(JDEC* jd, void* bitmap, JRECT* rect) {
    uint16_t* buf = (uint16_t*)bitmap;
    for (int y = rect->top; y <= rect->bottom; y++) {
        for (int x = rect->left; x <= rect->right; x++) {
            tft.drawPixel(x, y, *buf++);
        }
    }
    return 1;
}

void displayImage() {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("Camera capture failed");
        return;
    }

    // Ensure the captured format is JPEG
    if (fb->format != PIXFORMAT_JPEG) {
        Serial.println("Invalid format");
        esp_camera_fb_return(fb);
        return;
    }

    JDEC jd;
    JRESULT res;
    uint8_t work[3100];

    res = jd_prepare(&jd, jpgRead, work, sizeof(work), fb);
    if (res == JDR_OK) {
        jd_decomp(&jd, jpgToBuffer, 0);
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
