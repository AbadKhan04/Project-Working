import cv2
import numpy as np
import urllib.request
import threading
import queue

# ESP32 Stream URL (adjust IP if different)
url = 'http://192.168.137.94/stream'

# Queue for frames to separate capture and processing
frame_queue = queue.Queue(maxsize=5)

# Load YOLO network
net = cv2.dnn.readNet('Datasets/yolov3-tiny.weights', 'Datasets/yolov3-tiny.cfg')
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load COCO class names
with open("Datasets/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# To store vehicle positions and speeds across frames
vehicle_positions = {}
frame_rate = 15  # Adjust frame rate to match your stream

# Function to detect vehicles using YOLO
def detect_vehicles(frame):
    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)
    
    vehicle_count = 0
    detections = []
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
                
                # Save detection details
                detections.append((classes[class_id], confidence, x, y, w, h, center_x, center_y))
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, classes[class_id], (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
    return frame, detections

# Function to estimate speed based on frame positions
def estimate_speed(vehicle_id, current_pos):
    if vehicle_id in vehicle_positions:
        previous_pos = vehicle_positions[vehicle_id]
        distance = np.sqrt((current_pos[0] - previous_pos[0]) ** 2 + (current_pos[1] - previous_pos[1]) ** 2)
        speed = distance * frame_rate
        vehicle_positions[vehicle_id] = current_pos
    else:
        vehicle_positions[vehicle_id] = current_pos
        speed = 0
    return speed

# Function to detect overtaking by analyzing bounding box positions
def detect_overtaking(detections, frame):
    for i, (_, _, x1, y1, w1, h1, cx1, cy1) in enumerate(detections):
        for j, (_, _, x2, y2, w2, h2, cx2, cy2) in enumerate(detections):
            if i != j:
                # Check if one vehicle is overtaking another (based on x-coordinates)
                if cx1 > cx2 and abs(y1 - y2) < (h1 + h2) // 2:
                    cv2.putText(frame, "Overtaking!", (x1, y1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return frame

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

# Main loop for vehicle detection, counting, and speed estimation
total_vehicle_count = 0
while True:
    if not frame_queue.empty():
        frame = frame_queue.get()
        
        # Detect vehicles and count them
        frame, detections = detect_vehicles(frame)
        vehicle_count = len(detections)
        total_vehicle_count += vehicle_count
        
        # Display total vehicle count
        cv2.putText(frame, f"Total Vehicles Count: {total_vehicle_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Speed estimation and overtaking detection
        for idx, (label, confidence, x, y, w, h, cx, cy) in enumerate(detections):
            vehicle_id = f"{label}_{idx}"  # Unique ID for each detected vehicle
            speed = estimate_speed(vehicle_id, (cx, cy))
            cv2.putText(frame, f"Speed: {speed:.2f}", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        frame = detect_overtaking(detections, frame)

        # Show the frame
        cv2.imshow('ESP32-CAM Stream', frame)
        
        # Press 'q' to quit the stream
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
