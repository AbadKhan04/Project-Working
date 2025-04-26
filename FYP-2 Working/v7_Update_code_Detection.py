import cv2                  
import numpy as np          
import urllib.request
import threading
import queue
import time
import csv
import requests
import os

# Configuration
ESP32_STREAM_URL = 'http://192.168.137.199/stream'
FRONT_SENSOR_URL = 'http://192.168.137.41/'
BACK_SENSOR_URL = 'http://192.168.137.41/'
YOLO_CONFIG = 'Datasets/yolov3-tiny.cfg'
YOLO_WEIGHTS = 'Datasets/yolov3-tiny.weights'
COCO_NAMES = 'Datasets/coco.names'
CSV_LOG_FILE = 'vehicle_log.csv'
FRAME_RATE = 15
DETECTION_INTERVAL = 0.5
QUEUE_MAXSIZE = 5
CONFIDENCE_THRESHOLD = 0.3
DISTANCE_WARNING_THRESHOLD = 50

# Global variables
frame_queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
vehicle_positions = {}
tracked_vehicles = set()
last_detection_time = time.time()
total_vehicle_count = 0
previous_distance = 0 
current_distance = 0
last_speed_calc_time = time.time()

# Load Model and COCO classes
def load_yolo():
    net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CONFIG)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    with open(COCO_NAMES, "r") as f:
        classes = [line.strip() for line in f.readlines()]
    return net, output_layers, classes

net, output_layers, classes = load_yolo()

# Logging
def initialize_csv():
    if not os.path.exists(CSV_LOG_FILE): 
        with open(CSV_LOG_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Vehicle_ID", "Type", "Speed", "Overtaking_Event"])

initialize_csv()

def log_event(vehicle_id, vehicle_type, speed, overtaking=False):
    with open(CSV_LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), vehicle_id, vehicle_type, f"{speed:.2f}", overtaking])

def fetch_distances():
    try:
        response = requests.get(FRONT_SENSOR_URL)
        front_data = response.json() if response.status_code == 200 else {}
        response = requests.get(BACK_SENSOR_URL)
        back_data = response.json() if response.status_code == 200 else {}
        return front_data.get("front", 0), back_data.get("back", 0)
    except Exception as e:
        print(f"Error fetching distances: {e}")
        return 0, 0

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
            if confidence > CONFIDENCE_THRESHOLD and classes[class_id] in ['car', 'bus', 'truck', 'bicycle', 'motorbike']:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                detections.append((classes[class_id], confidence, x, y, w, h, center_x, center_y))
    return detections

def estimate_speed(vehicle_id, current_pos):
    if vehicle_id in vehicle_positions:
        prev_pos = vehicle_positions[vehicle_id]
        distance = np.sqrt((current_pos[0] - prev_pos[0])**2 + (current_pos[1] - prev_pos[1])**2)
        speed = distance * FRAME_RATE
        vehicle_positions[vehicle_id] = current_pos
    else:
        vehicle_positions[vehicle_id] = current_pos
        speed = 0
    return speed

def draw_detections(frame, detections):
    for idx, (label, confidence, x, y, w, h, cx, cy) in enumerate(detections):
        vehicle_id = f"{label}_{idx}"
        if vehicle_id not in tracked_vehicles:
            tracked_vehicles.add(vehicle_id)
            global total_vehicle_count
            total_vehicle_count += 1

        speed = estimate_speed(vehicle_id, (cx, cy))
        log_event(vehicle_id, label, speed)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, f"{label} {confidence:.2f}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(frame, f"Speed: {speed:.2f}", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

# Calculate own speed
def calculate_own_speed(previous_distance, current_distance, time_elapsed):
    if time_elapsed > 0:
        speed_mps = (current_distance - previous_distance) / time_elapsed 
        speed_kmph = speed_mps * 3.6 
        return speed_mps, speed_kmph
    else:
        return 0, 0

# Frame Fetching
def frame_fetcher():
    try:
        stream = urllib.request.urlopen(ESP32_STREAM_URL)
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
    except Exception as e:
        print(f"Error in frame fetcher: {e}")

# Frame fetching in a thread
fetch_thread = threading.Thread(target=frame_fetcher, daemon=True)
fetch_thread.start()

# Main Loop
while True:
    if not frame_queue.empty():
        frame = frame_queue.get()
        current_time = time.time()

        # Calculating own speed
        time_elapsed = current_time - last_speed_calc_time
        own_speed_mps, own_speed_kmph = calculate_own_speed(previous_distance, current_distance, time_elapsed)
        previous_distance = current_distance
        last_speed_calc_time = current_time

        # Run detections periodically
        detections = []
        if current_time - last_detection_time >= DETECTION_INTERVAL:
            detections = detect_vehicles(frame)
            last_detection_time = current_time

        # Draw detections
        draw_detections(frame, detections)

        # Fetch distance sensor data
        front_distance, back_distance = fetch_distances()

        # Warnings
        if front_distance < DISTANCE_WARNING_THRESHOLD:
            cv2.putText(frame, "Warning: Front too close!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        if back_distance < DISTANCE_WARNING_THRESHOLD:
            cv2.putText(frame, "Warning: Back too close!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Display total vehicle count and own speed
        cv2.putText(frame, f"Total Vehicles: {total_vehicle_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Your Speed: {own_speed_kmph:.2f} km/h", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow('ESP32-CAM Stream', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
