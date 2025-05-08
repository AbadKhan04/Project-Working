import cv2
import numpy as np
import urllib.request
import threading
import queue

# ESP32 Stream URL (adjust IP if different)
url = 'http://192.168.137.199/stream'

# Queue for frames to separate capture and processing
frame_queue = queue.Queue(maxsize=5)

# Load YOLO network
net = cv2.dnn.readNet('Datasets/yolov3-tiny.weights', 'Datasets/yolov3-tiny.cfg')
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load COCO class names
with open("Datasets/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Function to detect vehicles using YOLO
def detect_vehicles(frame):
    height, width, channels = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)
    
    # Vehicle count and bounding box details
    vehicle_count = 0
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            # Filter only for 'car', 'bus', 'truck'
            if confidence > 0.3 and classes[class_id] in ['car', 'bus', 'truck', 'bicycle', 'motorbike']:
                vehicle_count += 1
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, classes[class_id], (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
    return frame, vehicle_count

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
total_vehicle_count = 0
while True:
    if not frame_queue.empty():
        frame = frame_queue.get()
        # Detect and count vehicles
        frame, vehicle_count = detect_vehicles(frame)

        # Increment total vehicle count
        total_vehicle_count += vehicle_count
        cv2.putText(frame, f"Total Vehicles Count: {total_vehicle_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Show the frame
        cv2.imshow('ESP32-CAM Stream', frame)
        
        # Press 'q' to quit the stream
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
