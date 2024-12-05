import cv2
import numpy as np
import urllib.request
import threading
import queue

# ESP32 Stream URL (adjust IP if different)
url = 'http://192.168.137.254/stream'

# Queue for frames to separate capture and processing
frame_queue = queue.Queue(maxsize=5)

# Load MobileNet SSD model
net = cv2.dnn.readNetFromCaffe('deploy.prototxt', 'mobilenet_iter_73000.caffemodel')

# Define vehicle classes from the COCO dataset (only "car", "bus", and "truck" for simplicity)
vehicle_classes = {7: 'car', 5: 'bus', 2: 'bicycle', 6: 'train'}
# Define COCO class labels the model can detect
# class_labels = {
#     2: "car",
#     3: "motorbike",
#     5: "bus",
#     7: "truck"
# }

# Function to detect vehicles using MobileNet SSD
def detect_vehicles(frame):
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    vehicles = []

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        class_id = int(detections[0, 0, i, 1])

        if confidence > 0.5 and class_id in vehicle_classes:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (x, y, x1, y1) = box.astype("int")
            vehicles.append((x, y, x1 - x, y1 - y))
            cv2.rectangle(frame, (x, y), (x1, y1), (0, 255, 0), 2)
            label = f"{vehicle_classes[class_id]}: {int(confidence * 100)}%"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return frame, vehicles

# Function to fetch frames from ESP32
def frame_fetcher():
    stream = urllib.request.urlopen(url)
    bytes_data = b''
    while True:
        bytes_data += stream.read(4096)
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
        frame, vehicles = detect_vehicles(frame)

        # Update vehicle count
        vehicle_count += len(vehicles)
        cv2.putText(frame, f"Vehicles Count: {vehicle_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Show the frame
        cv2.imshow('ESP32-CAM Stream', frame)

        # Press 'q' to quit the stream
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
