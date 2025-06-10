# Work fine now, good to go
# test logs not over write now

import os
import cv2
import numpy as np
import urllib.request
import threading
import queue
import time
import csv
import json
import requests

# CONFIGURATION
ESP32_CAM_STREAM_URL = 'http://192.168.137.117/stream'
NODEMCU_JSON_URL = 'http://192.168.137.175/'  # Replace with your NodeMCU IP
FRAME_RATE = 15
CSV_LOG_FILE = "vehicle_log.csv"

# Queue for frames
frame_queue = queue.Queue(maxsize=5)

# Load YOLOv3-tiny
net = cv2.dnn.readNet('Datasets/yolov3-tiny.weights', 'Datasets/yolov3-tiny.cfg')
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load COCO classes
with open("Datasets/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Vehicle tracking
vehicle_positions = {}
tracked_vehicles = set()
last_detection_time = time.time()


# Create CSV file and headers
file_exists = os.path.isfile(CSV_LOG_FILE)
with open(CSV_LOG_FILE, mode='a', newline='') as file:
    writer = csv.writer(file)
    # Write headers only if the file is new
    if not file_exists:
        writer.writerow(["Timestamp", "Vehicle_ID", "Vehicle_Type", "Speed", "Front_Distance", "Back_Distance", "Overtaking"])

# Logging function
def log_event(vehicle_id, vehicle_type, speed, front, back, overtaking=False):
    with open(CSV_LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            str(vehicle_id),
            str(vehicle_type),
            f"{speed:.2f}",
            str(front),
            str(back),
            bool(overtaking)
        ])
        file.flush()  # Optional: Ensures data is written to disk immediately


latest_distance_data = {"front": 0, "back": 0, "overtaking": False}

def distance_updater():
    global latest_distance_data
    while True:
        try:
            response = requests.get(NODEMCU_JSON_URL, timeout=2.0)
            if response.status_code == 200:
                data = response.json()

                front_raw = data.get("front")
                back_raw = data.get("back")

                front = int(front_raw) if isinstance(front_raw, (int, float)) else 0
                back = int(back_raw) if isinstance(back_raw, (int, float)) else 0

                latest_distance_data["front"] = front 
                latest_distance_data["back"] = back

                # Infer overtaking based on back distance
                if back >= 80:
                    inferred_overtaking = True
                elif 70 <= back < 80:
                    inferred_overtaking = True
                elif 60 <= back < 70:
                    inferred_overtaking = False
                else:
                    inferred_overtaking = False
                print(f"[Distance] Front: {front}, Back: {back}, Overtaking: {inferred_overtaking}")

                latest_distance_data["overtaking"] = inferred_overtaking
            else:
                raise ValueError(f"Bad HTTP response: {response.status_code}")
        except Exception as e:
            print(f"[Distance Fetch Error] {e}")
            latest_distance_data["front"] = 0
            latest_distance_data["back"] = 0
            latest_distance_data["overtaking"] = False

        time.sleep(1.0)


# YOLO Detection
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

# Speed Estimation
def estimate_speed(vehicle_id, current_pos):
    if vehicle_id in vehicle_positions:
        prev_pos = vehicle_positions[vehicle_id]
        distance = np.sqrt((current_pos[0] - prev_pos[0]) ** 2 + (current_pos[1] - prev_pos[1]) ** 2)
        speed = distance * FRAME_RATE
        vehicle_positions[vehicle_id] = current_pos
    else:
        vehicle_positions[vehicle_id] = current_pos
        speed = 0
    return speed

# Frame fetching thread
def frame_fetcher():
    stream = urllib.request.urlopen(ESP32_CAM_STREAM_URL)
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

# Start threads
threading.Thread(target=frame_fetcher, daemon=True).start()
threading.Thread(target=distance_updater, daemon=True).start()

# Main loop
total_vehicle_count = 0
detections = []

while True:
    if not frame_queue.empty():
        frame = frame_queue.get()
        current_time = time.time()

        if current_time - last_detection_time >= 0.5:
            detections = detect_vehicles(frame)
            last_detection_time = current_time

        # Get sensor data
        front_dist = latest_distance_data.get("front", 0)
        back_dist = latest_distance_data.get("back", 0)
        overtaking_flag = latest_distance_data.get("overtaking", False)

        for idx, (label, conf, x, y, w, h, cx, cy) in enumerate(detections):
            vehicle_id = f"{label}_{idx}"
            if vehicle_id not in tracked_vehicles:
                tracked_vehicles.add(vehicle_id)
                total_vehicle_count += 1

            speed = estimate_speed(vehicle_id, (cx, cy))

            # Annotate
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, f"Speed: {speed:.1f}", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Log
            log_event(vehicle_id, label, speed, front_dist, back_dist, overtaking_flag)

        # Display extra info
        cv2.putText(frame, f"Total Vehicles: {total_vehicle_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(frame, f"Front: {latest_distance_data['front']} cm", (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 100), 2)
        cv2.putText(frame, f"Back: {latest_distance_data['back']} cm", (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
        if bool(overtaking_flag):
            cv2.putText(frame, "OVERTAKING DETECTED", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("ESP32-CAM Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
