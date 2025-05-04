#include <LCDWIKI_KBV.h>  // Install from LCDWIKI library
#include <SPI.h>

// Configure according to your shield and wiring
// For Uno with TFT shield plugged directly, control pins are usually:
// RS = A3, WR = A2, CS = A1, RST = A0, RD = A4
LCDWIKI_KBV mylcd(ILI9486, A3, A2, A1, A0, A4);

#define TFT_WIDTH  320
#define TFT_HEIGHT 240

void setup() {
  Serial.begin(115200);  // Match this with Python script baud rate

  mylcd.Init_LCD();
  mylcd.Fill_Screen(0x0000); // Clear screen

  Serial.write(0xA5);  // Signal Python script to start
}

void loop() {
  if (Serial.available() >= TFT_WIDTH * TFT_HEIGHT * 2) {
    for (int y = 0; y < TFT_HEIGHT; y++) {
      for (int x = 0; x < TFT_WIDTH; x++) {
        while (Serial.available() < 2); // Wait for pixel
        uint8_t high = Serial.read();
        uint8_t low = Serial.read();
        uint16_t color = (high << 8) | low;
        mylcd.Set_Draw_color(color);
        mylcd.Draw_Pixel(x, y);
      }
    }

    Serial.write(0xA5);  // Tell Python we’re ready for the next frame
  }
}
