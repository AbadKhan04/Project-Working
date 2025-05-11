import cv2
import serial
import struct
import time

# Setup
SERIAL_PORT = 'COM8'  # Update to your port
BAUD_RATE = 115200
WIDTH = 480
HEIGHT = 320

def rgb888_to_rgb565(r, g, b):
    r = int(r)
    g = int(g)
    b = int(b)
    rgb = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return rgb.to_bytes(2, 'big')  # Use 'little' if needed for color swap


# Serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
time.sleep(2)  # Allow Arduino to reset

# Open default webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Resize to TFT resolution
    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Optional: Flip image if needed
    # frame = cv2.rotate(frame, cv2.ROTATE_180)

    # Send header (marker + width + height)
    ser.write(b'\xFF\xD8')
    ser.write(struct.pack('>H', WIDTH))
    ser.write(struct.pack('>H', HEIGHT))

    # Send RGB565 data row by row
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = frame[y, x]
            ser.write(rgb888_to_rgb565(r, g, b))

    # Optional delay (~8 FPS)
    time.sleep(0.1)
