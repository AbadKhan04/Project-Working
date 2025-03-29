#include <SPI.h>
#include <Ethernet.h>
#include "esp_camera.h"

#define SCK  14
#define MISO 12
#define MOSI 13
#define SS   2
#define W5500_RST 15  // Reset pin for W5500


  // Serial.println("🔍 Checking W5500...");
  //   Serial.println("❌ W5500 NOT FOUND! Check connections.");
  // Serial.println("✅ W5500 Connected!");
  // Serial.print("📡 IP Address: ");


// W5500 Settings
byte mac[] = { 0xA0, 0xB7, 0x65, 0x25, 0xBE, 0x08 }; // Your ESP32 MAC Address
IPAddress ip(192, 168, 100, 28);  // Change to your network settings
EthernetServer server(80);

// W5500 Pin Reset Function
void resetW5500() {
    pinMode(W5500_RST, OUTPUT);
    digitalWrite(W5500_RST, LOW);
    delay(200);
    digitalWrite(W5500_RST, HIGH);
    delay(200);
    Serial.println("W5500 Reset Done");
}

// // Camera Pins (AI-Thinker ESP32-CAM)
// #define PWDN_GPIO_NUM    32
// #define RESET_GPIO_NUM   -1
// #define XCLK_GPIO_NUM     0
// #define SIOD_GPIO_NUM    26
// #define SIOC_GPIO_NUM    27
// #define Y9_GPIO_NUM      35
// #define Y8_GPIO_NUM      34
// #define Y7_GPIO_NUM      39
// #define Y6_GPIO_NUM      36
// #define Y5_GPIO_NUM      21
// #define Y4_GPIO_NUM      19
// #define Y3_GPIO_NUM      18
// #define Y2_GPIO_NUM       5
// #define VSYNC_GPIO_NUM   25
// #define HREF_GPIO_NUM    23
// #define PCLK_GPIO_NUM    22

// Initialize Camera
void startCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = 5;
    config.pin_d1 = 18;
    config.pin_d2 = 19;
    config.pin_d3 = 21;
    config.pin_d4 = 36;
    config.pin_d5 = 39;
    config.pin_d6 = 34;
    config.pin_d7 = 35;
    config.pin_xclk = 0;
    config.pin_pclk = 22;
    config.pin_vsync = 25;
    config.pin_href = 23;
    config.pin_sscb_sda = 26;
    config.pin_sscb_scl = 27;
    config.pin_pwdn = 32;
    config.pin_reset = -1;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    if (psramFound()) {
        config.frame_size = FRAMESIZE_QVGA;
        config.jpeg_quality = 10;
        config.fb_count = 2;
    } else {
        config.frame_size = FRAMESIZE_CIF;
        config.jpeg_quality = 12;
        config.fb_count = 1;
    }

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.println("Camera initialization failed!");
        return;
    }
    Serial.println("Camera initialized successfully!");
}

void setup() {
    Serial.begin(115200);
    Serial.println("\nESP32-CAM Ethernet Streaming");

    // Reset W5500
    resetW5500();

    // Start SPI for Ethernet
    SPI.begin(SCK, MISO, MOSI, SS);

    // Start Ethernet
    Ethernet.init(SS);
    if (Ethernet.begin(mac) == 0) {
        Serial.println("Failed to configure Ethernet using DHCP");
        Ethernet.begin(mac, ip);
    }

    Serial.print("Ethernet connected! IP Address: ");
    Serial.println(Ethernet.localIP());

    // Start Camera
    startCamera();

    // Start Web Server
    server.begin();
    Serial.println("Web server started");
}

void loop() {
    EthernetClient client = server.available();
    if (client) {
        String request = client.readStringUntil('\r');
        client.flush();
        Serial.println("Client Connected: " + request);

        if (request.indexOf("/stream") != -1) {
            sendCameraStream(client);
        } else {
            sendHTML(client);
        }

        client.stop();
        Serial.println("Client Disconnected");
    }
}

void sendCameraStream(EthernetClient &client) {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: multipart/x-mixed-replace; boundary=frame");
    client.println();

    while (client.connected()) {
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed!");
            continue;
        }

        client.println("--frame");
        client.println("Content-Type: image/jpeg");
        client.println("Content-Length: " + String(fb->len));
        client.println();
        client.write(fb->buf, fb->len);
        client.println();
        esp_camera_fb_return(fb);

        delay(100); // Adjust for smoother streaming
    }
}



// HTML Page
void sendHTML(EthernetClient &client) {
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/html");
    client.println();
    client.println("<html><body>");
    client.println("<h2>ESP32-CAM Ethernet Stream</h2>");
    client.println("<img src='/stream' width='320' height='240'>");
    client.println("</body></html>");

    Serial.println("HTML Page Sent");
}
