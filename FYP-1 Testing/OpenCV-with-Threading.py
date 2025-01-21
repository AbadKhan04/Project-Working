import cv2
import numpy as np
import urllib.request
import threading
import queue

# ESP32 Stream URL (adjust IP if different)
url = 'http://192.168.137.62/stream'

# Queue for frames to separate capture and processing
frame_queue = queue.Queue(maxsize=5)

# Vehicle detection cascade classifier
car_cascade = cv2.CascadeClassifier('car.xml')

# Function to detect vehicles using OpenCV
def detect_vehicles(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cars = car_cascade.detectMultiScale(gray, 1.2, 2)  # Adjust parameters as needed
    for (x, y, w, h) in cars:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return frame, cars

# Function to fetch frames from ESP32
def frame_fetcher():
    stream = urllib.request.urlopen(url)
    bytes_data = b''
    while True:
        bytes_data += stream.read(4096)  # Larger chunk for reduced delay
        a = bytes_data.find(b'\xff\xd8')
        b = bytes_data.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes_data[a:b + 2]
            bytes_data = bytes_data[b + 2:]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if not frame_queue.full():
                frame_queue.put(frame)

# Start frame fetching in a separate thread
fetch_thread = threading.Thread(target=frame_fetcher)
fetch_thread.daemon = True
fetch_thread.start()

# Vehicle detection and counting in main loop
vehicle_count = 0
while True:
    if not frame_queue.empty():
        frame = frame_queue.get()
        # Detect and count vehicles
        frame, cars = detect_vehicles(frame)

        # Display vehicle count on the frame
        vehicle_count += len(cars)  # Increment count by detected cars
        cv2.putText(frame, f"Vehicles Count: {vehicle_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Show the frame
        cv2.imshow('ESP32-CAM Stream', frame)
        
        # Press 'q' to quit the stream
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
