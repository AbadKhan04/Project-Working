# Final code, ready to show.

import requests
import threading
import serial
import struct
from PIL import Image
import io
import time

ESP32_URL = 'http://192.168.137.34/stream'
SERIAL_PORT = 'COM8'
BAUD = 2000000
WIDTH, HEIGHT = 480, 320

latest_frame = None
lock = threading.Lock()

def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3).to_bytes(2, 'big')

def stream_reader():
    global latest_frame
    stream = requests.get(ESP32_URL, stream=True)
    buf = b''

    for chunk in stream.iter_content(chunk_size=4096):
        buf += chunk
        while True:
            start = buf.find(b'\xff\xd8')
            end = buf.find(b'\xff\xd9')
            if start != -1 and end != -1 and end > start:
                frame = buf[start:end+2]
                with lock:
                    latest_frame = frame
                buf = buf[end+2:]
            else:
                break

def send_to_arduino(jpg_data, ser):
    try:
        img = Image.open(io.BytesIO(jpg_data))
        img = img.resize((WIDTH, HEIGHT)).convert('RGB')

        ser.flushOutput()
        ser.write(b'\xFF\xD8')
        ser.write(struct.pack('>H', WIDTH))
        ser.write(struct.pack('>H', HEIGHT))

        pixels = img.load()
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = pixels[x, y]
                ser.write(rgb888_to_rgb565(r, g, b))

    except Exception as e:
        print(f"[ERROR] Image send failed: {e}")

def main():
    global latest_frame
    ser = serial.Serial(SERIAL_PORT, BAUD)
    time.sleep(2)

    threading.Thread(target=stream_reader, daemon=True).start()

    while True:
        frame_to_send = None
        with lock:
            if latest_frame:
                frame_to_send = latest_frame
                latest_frame = None

        if frame_to_send:
            send_to_arduino(frame_to_send, ser)
            time.sleep(0.05)  

if __name__ == "__main__":
    main()
