import requests
import serial
from PIL import Image
import io
import time

# Config
ESP32_URL = 'http://192.168.137.140/stream'  # Replace with your ESP32 IP
SERIAL_PORT = 'COM8'  # Change to your Arduino COM port
BAUD = 115200

def jpeg_stream(url):
    stream = requests.get(url, stream=True)
    boundary = b'--frame'
    buf = b''

    for chunk in stream.iter_content(chunk_size=1024):
        buf += chunk
        while True:
            start = buf.find(b'\xff\xd8')  # JPEG start
            end = buf.find(b'\xff\xd9')    # JPEG end
            if start != -1 and end != -1 and end > start:
                jpg = buf[start:end + 2]
                yield jpg
                buf = buf[end + 2:]
            else:
                break

def send_to_arduino(img_data):
    img = Image.open(io.BytesIO(img_data))
    img = img.resize((320, 240)).convert('RGB')  # Resize & convert
    ser = serial.Serial(SERIAL_PORT, BAUD)
    while ser.read() != b'\xA5':
        continue  # Wait for ready signal from Arduino
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = img.getpixel((x, y))
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            ser.write(rgb565.to_bytes(2, 'big'))
    ser.close()

def main():
    try:
        for frame in jpeg_stream(ESP32_URL):
            try:
                send_to_arduino(frame)
            except Exception as e:
                print("Error sending image to Arduino:", e)
    except KeyboardInterrupt:
        print("\nStream interrupted by Admin. Closing...")
    finally:
        print("Cleaning up...")
        # Optionally, close any resources if needed

if __name__ == "__main__":
    main()
