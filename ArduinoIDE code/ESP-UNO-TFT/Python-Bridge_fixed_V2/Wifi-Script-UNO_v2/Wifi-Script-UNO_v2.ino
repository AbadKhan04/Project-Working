#include <MCUFRIEND_kbv.h>
MCUFRIEND_kbv tft;

#define WIDTH 480
#define HEIGHT 320
uint16_t lineBuffer[WIDTH];

void setup() {
  Serial.begin(2000000);
  uint16_t ID = tft.readID();
  tft.begin(ID);
  tft.setRotation(1);
  tft.fillScreen(0x0000); // Clear screen to black
}

void loop() {
  if (Serial.available() >= 6) {
    if (Serial.read() == 0xFF && Serial.read() == 0xD8) {
      uint16_t w = (Serial.read() << 8) | Serial.read();
      uint16_t h = (Serial.read() << 8) | Serial.read();

      if (w != WIDTH || h != HEIGHT) return; // ensure correct size

      for (uint16_t y = 0; y < HEIGHT; y++) {
        uint16_t i = 0;
        while (i < WIDTH) {
          if (Serial.available() >= 2) {
            uint8_t hi = Serial.read();
            uint8_t lo = Serial.read();
            lineBuffer[i++] = (hi << 8) | lo;
          }
        }
        // Only draw after full line is ready
        tft.setAddrWindow(0, y, WIDTH - 1, y);
        tft.pushColors(lineBuffer, WIDTH, 1);
      }
    }
  }
}
