import requests
import serial
import struct
from PIL import Image
import io
import time

# ESP32 stream URL and Arduino serial
ESP32_URL = 'http://192.168.137.52/stream'  # Your ESP32-CAM stream URL
SERIAL_PORT = 'COM8'                         # Your Arduino UNO port
BAUD = 921600
WIDTH, HEIGHT = 480, 320

# Convert RGB888 to RGB565
def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3).to_bytes(2, 'big')

# MJPEG stream reader
def jpeg_stream(url):
    stream = requests.get(url, stream=True)
    boundary = b'--frame'
    buf = b''

    for chunk in stream.iter_content(chunk_size=1024):
        buf += chunk
        while True:
            start = buf.find(b'\xff\xd8')
            end = buf.find(b'\xff\xd9')
            if start != -1 and end != -1 and end > start:
                yield buf[start:end+2]
                buf = buf[end+2:]
            else:
                break

def send_to_arduino(jpg_data, ser):
    try:
        img = Image.open(io.BytesIO(jpg_data))
        img = img.resize((WIDTH, HEIGHT)).convert('RGB')

        # Send header: 0xFF 0xD8 + width + height
        ser.write(b'\xFF\xD8')
        ser.write(struct.pack('>H', WIDTH))
        ser.write(struct.pack('>H', HEIGHT))

        # Send pixel data
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = img.getpixel((x, y))
                ser.write(rgb888_to_rgb565(r, g, b))
    except Exception as e:
        print(f"[ERROR] Image send failed: {e}")

def main():
    print("[INFO] Starting Stream Bridge...")
    ser = serial.Serial(SERIAL_PORT, BAUD)
    time.sleep(2)  # Let Arduino reset

    try:
        for frame in jpeg_stream(ESP32_URL):
            send_to_arduino(frame, ser)
            time.sleep(0.1)  # ~8 FPS
    except KeyboardInterrupt:
        print("\n[INFO] Stream interrupted by user.")
    finally:
        ser.close()
        print("[INFO] Serial connection closed.")

if __name__ == "__main__":
    main()
