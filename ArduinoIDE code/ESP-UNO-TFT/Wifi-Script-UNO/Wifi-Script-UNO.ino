#include <LCDWIKI_GUI.h>
#include <LCDWIKI_KBV.h>

LCDWIKI_KBV mylcd(ILI9486, A3, A2, A1, A0, A4);  // Adjust if needed

void setup() {
  mylcd.Init_LCD();
  mylcd.Set_Rotation(1);
  Serial.begin(115200);
  Serial.write(0xA5);  // Ready signal
}

void loop() {
  while (Serial.available() < 320 * 240 * 2);  // Wait for full frame
  for (int y = 0; y < 240; y++) {
    for (int x = 0; x < 320; x++) {
      uint8_t hi = Serial.read();
      uint8_t lo = Serial.read();
      uint16_t color = (hi << 8) | lo;
      mylcd.Set_Draw_color(color);
      mylcd.Draw_Pixel(x, y);
    }
  }
  Serial.write(0xA5);  // Ready for next
}
