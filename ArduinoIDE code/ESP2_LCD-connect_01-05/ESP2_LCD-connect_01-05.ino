#include <WiFi.h>
#include <TFT_eSPI.h>
#include <JPEGDecoder.h>
#include <HTTPClient.h>

TFT_eSPI tft = TFT_eSPI();

const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";
const char* cam_url = "http://192.168.1.60/capture";  // ESP32-CAM IP

void setup() {
  Serial.begin(115200);
  tft.begin();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.drawString("Connecting...", 10, 10);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  tft.fillScreen(TFT_BLACK);
  tft.drawString("WiFi Connected!", 10, 10);
  delay(1000);
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(cam_url);
    int httpCode = http.GET();

    if (httpCode == 200) {
      int len = http.getSize();
      WiFiClient* stream = http.getStreamPtr();

      // Allocate buffer
      uint8_t* jpegBuf = (uint8_t*)malloc(len);
      if (!jpegBuf) {
        Serial.println("Memory alloc failed");
        http.end();
        return;
      }

      int index = 0;
      while (http.connected() && index < len) {
        if (stream->available()) {
          jpegBuf[index++] = stream->read();
        }
      }

      Serial.printf("Image downloaded: %d bytes\n", index);

      if (JpegDec.decodeArray(jpegBuf, index)) {
        renderJPEG();
      } else {
        Serial.println("JPEG decode failed.");
      }

      free(jpegBuf);
    } else {
      Serial.print("HTTP error: ");
      Serial.println(httpCode);
    }

    http.end();
  } else {
    Serial.println("WiFi disconnected");
  }

  delay(2000);  // Adjust refresh rate
}

void renderJPEG() {
  uint16_t* pImg;
  int16_t mcu_w = JpegDec.MCUWidth;
  int16_t mcu_h = JpegDec.MCUHeight;
  int32_t max_x = JpegDec.width;
  int32_t max_y = JpegDec.height;

  while (JpegDec.read()) {
    pImg = JpegDec.pImage;
    int16_t x = JpegDec.MCUx * mcu_w;
    int16_t y = JpegDec.MCUy * mcu_h;

    if ((x + mcu_w) <= tft.width() && (y + mcu_h) <= tft.height()) {
      tft.pushImage(x, y, mcu_w, mcu_h, pImg);
    }
  }
}
