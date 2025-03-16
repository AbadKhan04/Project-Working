#include <TFT_eSPI.h>  // Include TFT_eSPI library
#include <SPI.h>

TFT_eSPI tft = TFT_eSPI();  // Create TFT object

void setup() {
    tft.init();
    tft.setRotation(3);  // Adjust based on orientation

    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setTextSize(2);
    
    tft.setCursor(10, 10);
    tft.println("ESP32-CAM ILI9488");
    delay(2000);

    // Draw test graphics
    tft.fillRect(10, 50, 100, 50, TFT_RED);
    delay(500);
    tft.fillRect(120, 50, 100, 50, TFT_BLUE);
    delay(500);
    tft.fillRect(10, 120, 210, 50, TFT_GREEN);
}

void loop() {
    tft.setCursor(10, 200);
    tft.setTextColor(random(0xFFFF));
    tft.println("Hello World!");
    delay(1000);
}
