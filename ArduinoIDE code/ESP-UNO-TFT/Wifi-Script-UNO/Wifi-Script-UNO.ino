#include <MCUFRIEND_kbv.h>
MCUFRIEND_kbv tft;

void setup() {
  //Serial.begin(115200);
  Serial.begin(921600);
  uint16_t ID = tft.readID();
  tft.begin(ID);
  tft.setRotation(1);
  tft.fillScreen(0x0000); // Black
}

void loop() {
  if (Serial.available() >= 6) {
    if (Serial.read() == 0xFF && Serial.read() == 0xD8) {
      uint16_t width = (Serial.read() << 8) | Serial.read();
      uint16_t height = (Serial.read() << 8) | Serial.read();

      if (width > 480 || height > 320) return;

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
