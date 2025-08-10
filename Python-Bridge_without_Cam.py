import os
import requests
import threading
import serial
import struct
from PIL import Image
import io
import time

# ============ CONFIGURATION ============
FOLDER_PATH = os.path.expanduser('~\OneDrive\Pictures\Lamborghini Pics')  # Auto-points to Pictures folder
SERIAL_PORT = 'COM8'
BAUD = 2000000
WIDTH, HEIGHT = 480, 320
IMAGE_CHANGE_INTERVAL = 2  # seconds between images
# =======================================

latest_jpg = None
decoded_frame = None
jpg_lock = threading.Lock()
frame_lock = threading.Lock()

def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3).to_bytes(2, 'big')

def image_folder_reader():
    global latest_jpg
    supported_exts = ('.jpg', '.jpeg', '.png', '.bmp')

    # Get all image files in folder
    image_files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith(supported_exts)]
    image_files.sort()  # Optional: sort alphabetically

    if not image_files:
        print("[ERROR] No image files found in:", FOLDER_PATH)
        return

    index = 0
    while True:
        try:
            image_path = os.path.join(FOLDER_PATH, image_files[index])
            with open(image_path, 'rb') as f:
                data = f.read()
                with jpg_lock:
                    latest_jpg = data

            index = (index + 1) % len(image_files)
        except Exception as e:
            print(f"[ERROR] Reading image failed: {e}")

        time.sleep(IMAGE_CHANGE_INTERVAL)

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
                frame = decoded_frame.copy()

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

    threading.Thread(target=image_folder_reader, daemon=True).start()
    threading.Thread(target=frame_decoder, daemon=True).start()
    frame_sender(ser)

if __name__ == "__main__":
    main()
