# Much faster then previous one.

import requests
import threading
import serial
import struct
from PIL import Image
import io
import time

ESP32_URL = 'http://192.168.137.67/stream'
SERIAL_PORT = 'COM8'
BAUD = 2000000
WIDTH, HEIGHT = 480, 320

latest_jpg = None
decoded_frame = None
jpg_lock = threading.Lock()
frame_lock = threading.Lock()

def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3).to_bytes(2, 'big')

def stream_reader():
    global latest_jpg
    stream = requests.get(ESP32_URL, stream=True)
    buf = b''
    for chunk in stream.iter_content(chunk_size=4096):
        buf += chunk
        while True:
            start = buf.find(b'\xff\xd8')
            end = buf.find(b'\xff\xd9')
            if start != -1 and end != -1 and end > start:
                frame = buf[start:end+2]
                with jpg_lock:
                    latest_jpg = frame
                buf = buf[end+2:]
            else:
                break

def frame_decoder():
    global latest_jpg, decoded_frame
    while True:
        current_jpg = None
        with jpg_lock:
            if latest_jpg:
                current_jpg = latest_jpg
                latest_jpg = None

        if current_jpg:
            try:
                img = Image.open(io.BytesIO(current_jpg))
                img = img.resize((WIDTH, HEIGHT)).convert('RGB')
                with frame_lock:
                    decoded_frame = img
            except Exception as e:
                print(f"[ERROR] Decode failed: {e}")

        time.sleep(0.005)


def frame_sender(ser):
    global decoded_frame
    while True:
        frame = None
        with frame_lock:
            if decoded_frame:
                frame = decoded_frame.copy()  # Shallow copy for thread safety

        if frame:
            try:
                ser.flushOutput()
                ser.write(b'\xFF\xD8')
                ser.write(struct.pack('>H', WIDTH))
                ser.write(struct.pack('>H', HEIGHT))

                pixels = frame.load()
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        r, g, b = pixels[x, y]
                        ser.write(rgb888_to_rgb565(r, g, b))

            except Exception as e:
                print(f"[ERROR] Send failed: {e}")

        time.sleep(0.01)

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD)
    time.sleep(2)

    threading.Thread(target=stream_reader, daemon=True).start()
    threading.Thread(target=frame_decoder, daemon=True).start()
    frame_sender(ser)  # Run in main thread

if __name__ == "__main__":
    main()
