import cv2
import numpy as np      # 20-Nov-2024   Delay minor, detection good (speed not calculation)
import urllib.request
import threading
import queue
import time
import csv

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

# Vehicle tracking and speed estimation
vehicle_positions = {}
tracked_vehicles = set()
frame_rate = 15  # Adjust frame rate to match your stream
last_detection_time = time.time()

# Initialize CSV logging
csv_file = "vehicle_log.csv"
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Vehicle_ID", "Type", "Speed", "Overtaking_Event"])

# Function to log events
def log_event(vehicle_id, vehicle_type, speed, overtaking=False):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), vehicle_id, vehicle_type, f"{speed:.2f}", overtaking])

# Function to detect vehicles using YOLO
def detect_vehicles(frame):
    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    detections = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.3 and classes[class_id] in ['car', 'bus', 'truck', 'bicycle', 'motorbike']:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                detections.append((classes[class_id], confidence, x, y, w, h, center_x, center_y))
    return detections

# Function to estimate speed based on positions
def estimate_speed(vehicle_id, current_pos):
    if vehicle_id in vehicle_positions:
        previous_pos = vehicle_positions[vehicle_id]
        distance = np.sqrt((current_pos[0] - previous_pos[0]) ** 2 + (current_pos[1] - previous_pos[1]) ** 2)
        speed = distance * frame_rate  # Scale appropriately
        vehicle_positions[vehicle_id] = current_pos
    else:
        vehicle_positions[vehicle_id] = current_pos
        speed = 0
    return speed

# Function to detect overtaking
def detect_overtaking(detections):
    overtaking_events = []
    for i, (_, _, x1, y1, w1, h1, cx1, cy1) in enumerate(detections):
        for j, (_, _, x2, y2, w2, h2, cx2, cy2) in enumerate(detections):
            if i != j and cx1 > cx2 and abs(y1 - y2) < (h1 + h2) // 2:
                overtaking_events.append((i, j))
    return overtaking_events

# Frame fetcher thread
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

# Start frame fetching
fetch_thread = threading.Thread(target=frame_fetcher)
fetch_thread.daemon = True
fetch_thread.start()

# Main loop
total_vehicle_count = 0
while True:
    if not frame_queue.empty():
        frame = frame_queue.get()
        current_time = time.time()
        
        # Detect vehicles every 0.5 seconds to save resources
        if current_time - last_detection_time >= 0.5:
            detections = detect_vehicles(frame)
            last_detection_time = current_time

        # Track and annotate vehicles
        for idx, (label, confidence, x, y, w, h, cx, cy) in enumerate(detections):
            vehicle_id = f"{label}_{idx}"
            if vehicle_id not in tracked_vehicles:
                tracked_vehicles.add(vehicle_id)
                total_vehicle_count += 1

            speed = estimate_speed(vehicle_id, (cx, cy))
            log_event(vehicle_id, label, speed)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {confidence:.2f}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, f"Speed: {speed:.2f}", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        overtaking_events = detect_overtaking(detections)
        for i, j in overtaking_events:
            log_event(f"{detections[i][0]}_{i}", detections[i][0], 0, overtaking=True)

        # Display vehicle count
        cv2.putText(frame, f"Total Vehicles: {total_vehicle_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('ESP32-CAM Stream', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
