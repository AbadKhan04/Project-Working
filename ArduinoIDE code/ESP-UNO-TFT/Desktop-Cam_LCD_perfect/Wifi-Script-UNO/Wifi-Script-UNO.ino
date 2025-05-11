#include <MCUFRIEND_kbv.h>
MCUFRIEND_kbv tft;

#define BLACK   0x0000
#define BLUE    0x001F
#define RED     0xF800
#define GREEN   0x07E0
#define CYAN    0x07FF
#define MAGENTA 0xF81F
#define YELLOW  0xFFE0
#define WHITE   0xFFFF


void setup() {
  Serial.begin(115200);
  uint16_t ID = tft.readID();
  tft.begin(ID);
  tft.setRotation(1);
  tft.fillScreen(BLACK);
}

void loop() {
  if (Serial.available() >= 6) {
    // Wait for header: 0xFF 0xD8 + width + height
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
