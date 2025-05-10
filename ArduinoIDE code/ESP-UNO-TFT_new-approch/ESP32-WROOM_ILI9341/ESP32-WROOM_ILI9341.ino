#include <WiFi.h>
#include <WiFiUdp.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <JPEGDecoder.h>

#define TFT_CS    12
#define TFT_DC    13
#define TFT_RST   2
#define TFT_MOSI  16
#define TFT_SCLK  14

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

WiFiUDP udp;
const uint16_t localPort = 1069;

const char* ssid = "DESKTOP-F614S19";
const char* password = "Error404";

// Buffer to accumulate image
const int bufferSize = 30 * 1024;
uint8_t jpgBuffer[bufferSize];
int bufferIndex = 0;

unsigned long lastPacketTime = 0;
const int packetTimeout = 100; // ms

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("ESP32-WROOM IP: ");
  Serial.println(WiFi.localIP());

  udp.begin(localPort);

  tft.begin();
  tft.setRotation(1); // Landscape
  tft.fillScreen(ILI9341_BLACK);
  tft.setTextColor(ILI9341_GREEN);
  tft.setTextSize(2);
  tft.setCursor(20, 120);
  tft.print("Waiting for stream...");
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    if (bufferIndex + packetSize < bufferSize) {
      udp.read(jpgBuffer + bufferIndex, packetSize);
      bufferIndex += packetSize;
    } else {
      Serial.println("Buffer overflow, skipping frame");
      bufferIndex = 0;
    }
    lastPacketTime = millis();
  }

  // If no packet for 100ms and buffer has data, decode
  if (bufferIndex > 0 && millis() - lastPacketTime > packetTimeout) {
    Serial.println("Decoding JPEG...");
    decodeAndDisplay(jpgBuffer, bufferIndex);
    bufferIndex = 0;
  }
}

void decodeAndDisplay(uint8_t *data, int length) {
  if (JpegDec.decodeArray(data, length) == 0) {
    Serial.println("JPEG decode failed");
    return;
  }

  int x = (tft.width() - JpegDec.width) / 2;
  int y = (tft.height() - JpegDec.height) / 2;

  tft.fillScreen(ILI9341_BLACK);

  // Draw image using drawPixel
  while (JpegDec.read()) {
    uint16_t* pImg = JpegDec.pImage;
    int mcuX = JpegDec.MCUx * JpegDec.MCUWidth + x;
    int mcuY = JpegDec.MCUy * JpegDec.MCUHeight + y;

    for (int row = 0; row < JpegDec.MCUHeight; row++) {
      for (int col = 0; col < JpegDec.MCUWidth; col++) {
        int tftX = mcuX + col;
        int tftY = mcuY + row;
        if (tftX >= 0 && tftX < tft.width() && tftY >= 0 && tftY < tft.height()) {
          uint16_t color = *pImg++;
          tft.drawPixel(tftX, tftY, color);
        } else {
          pImg++; // Still need to move pointer
        }
      }
    }
  }
}

