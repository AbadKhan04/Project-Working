#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();  // TFT instance

void setup() {
  Serial.begin(115200);
  tft.begin();
  tft.setRotation(1);  // Landscape
  tft.fillScreen(TFT_BLACK);

  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawString("ESP32 + ILI9341 Test", 20, 30);

  delay(1000);

  // Draw test shapes
  tft.fillCircle(60, 120, 30, TFT_RED);
  tft.fillRect(110, 100, 60, 40, TFT_BLUE);
  tft.drawLine(0, 0, tft.width(), tft.height(), TFT_GREEN);
  tft.drawLine(tft.width(), 0, 0, tft.height(), TFT_GREEN);
}

void loop() {
  // Nothing to loop for basic test
}
