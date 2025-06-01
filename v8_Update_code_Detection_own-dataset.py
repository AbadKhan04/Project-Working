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
from ultralytics import YOLO

# CONFIGURATION
ESP32_CAM_STREAM_URL = 'http://192.168.137.152/stream'
NODEMCU_JSON_URL = 'http://192.168.137.59/'
FRAME_RATE = 15
CSV_LOG_FILE = "vehicle_log.csv"
MODEL_PATH = 'Datasets/best.pt'  # Custom model path

# Queue for frames
frame_queue = queue.Queue(maxsize=5)

# Load custom YOLOv8 model
model = YOLO(MODEL_PATH)
classes = ["car"]  # Single class based on your training

# Vehicle tracking
vehicle_positions = {}
tracked_vehicles = set()
last_detection_time = time.time()

# Create CSV file and headers
file_exists = os.path.isfile(CSV_LOG_FILE)
with open(CSV_LOG_FILE, mode='a', newline='') as file:
    writer = csv.writer(file)
    if not file_exists:
        writer.writerow(["Timestamp", "Vehicle_ID", "Vehicle_Type", "Speed", "Front_Distance", "Back_Distance", "Overtaking"])

# Logging function (unchanged)
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
        file.flush()

# Distance updater thread (unchanged)
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
                if back >= 80:
                    inferred_overtaking = True
                elif 70 <= back < 80:
                    inferred_overtaking = True
                elif 60 <= back < 70:
                    inferred_overtaking = False
                else:
                    inferred_overtaking = False
                latest_distance_data["overtaking"] = inferred_overtaking
            else:
                raise ValueError(f"Bad HTTP response: {response.status_code}")
        except Exception as e:
            print(f"[Distance Fetch Error] {e}")
            latest_distance_data["front"] = 0
            latest_distance_data["back"] = 0
            latest_distance_data["overtaking"] = False
        time.sleep(1.0)

# Updated YOLOv8 detection function
def detect_vehicles(frame):
    results = model(frame, verbose=False)  # Disable prediction logging
    detections = []
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            
            if classes[cls_id] == "car" and conf > 0.5:
                w = x2 - x1
                h = y2 - y1
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                detections.append(("car", conf, x1, y1, w, h, cx, cy))
    
    return detections

# Speed estimation (unchanged)
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

# Frame fetching thread (unchanged)
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

# Start threads (unchanged)
threading.Thread(target=frame_fetcher, daemon=True).start()
threading.Thread(target=distance_updater, daemon=True).start()

# Main loop (updated visualization)
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
            cv2.putText(frame, f"{label} {conf:.2f}", (x, y - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, f"Speed: {speed:.1f}", (x, y - 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Log
            log_event(vehicle_id, label, speed, front_dist, back_dist, overtaking_flag)

        # Display extra info (unchanged)
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