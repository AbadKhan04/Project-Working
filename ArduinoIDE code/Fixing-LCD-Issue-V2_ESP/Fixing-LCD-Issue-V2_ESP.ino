#include <TJpg_Decoder.h>
#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();  // Uses setup from User_Setup.h

// Corrected callback signature for TJpg_Decoder
bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t *bitmap) {
  tft.pushImage(x, y, w, h, bitmap);
  return true;
}

void setup() {
  Serial.begin(115200);

  tft.begin();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);

  TJpgDec.setSwapBytes(true);
  TJpgDec.setCallback(tft_output);
}

void loop() {
  if (Serial.available() >= 6) {
    if (Serial.read() == 0xFF && Serial.read() == 0xD8) {
      uint16_t width = (Serial.read() << 8) | Serial.read();
      uint16_t height = (Serial.read() << 8) | Serial.read();

      if (width > 320 || height > 240) return;

      for (uint16_t y = 0; y < height; y++) {
        for (uint16_t x = 0; x < width; x++) {
          while (Serial.available() < 2);
          uint8_t hi = Serial.read();
          uint8_t lo = Serial.read();
          uint16_t color = (hi << 8) | lo;
          tft.drawPixel(x, y, color);
        }
      }
    }
  }
}
