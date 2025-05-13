# Not work the way i want

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

frame_lock = threading.Lock()
serial_lock = threading.Lock()
latest_frame = None

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
                with frame_lock:
                    latest_frame = frame
                buf = buf[end+2:]
            else:
                break

def render_frame(jpg_data, ser):
    try:
        img = Image.open(io.BytesIO(jpg_data))
        img = img.resize((WIDTH, HEIGHT)).convert('RGB')

        with serial_lock:  # Ensure only one render writes to serial at a time
            ser.write(b'\xFF\xD8')
            ser.write(struct.pack('>H', WIDTH))
            ser.write(struct.pack('>H', HEIGHT))

            pixels = img.load()
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    r, g, b = pixels[x, y]
                    ser.write(rgb888_to_rgb565(r, g, b))

    except Exception as e:
        print(f"[ERROR] Frame render failed: {e}")

def main():
    global latest_frame
    print("[INFO] Starting stream with concurrent rendering (shared serial port)")
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD)
        time.sleep(2)  # Allow time to initialize

        # Start frame stream reader thread
        threading.Thread(target=stream_reader, daemon=True).start()

        while True:
            frame = None
            with frame_lock:
                if latest_frame:
                    frame = latest_frame
                    latest_frame = None

            if frame:
                # Start a new render thread (no port conflict now)
                threading.Thread(target=render_frame, args=(frame, ser), daemon=True).start()

            time.sleep(0.1)  # Small delay to prevent CPU overload

    except Exception as e:
        print(f"[FATAL] Could not open serial port: {e}")

if __name__ == "__main__":
    main()
