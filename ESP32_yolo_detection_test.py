import cv2
import numpy as np
import urllib.request
import threading
import queue
import time

# CONFIGURATION
ESP32_CAM_STREAM_URL = 'http://192.168.137.225/stream'
FRAME_RATE = 15

# Queue for frames
frame_queue = queue.Queue(maxsize=5)

# Load YOLOv3-tiny
net = cv2.dnn.readNet('Datasets/yolov3-tiny.weights', 'Datasets/yolov3-tiny.cfg')
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load COCO classes
with open("Datasets/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

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
                detections.append((classes[class_id], confidence, x, y, w, h))
    return detections

# Frame fetcher thread
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

# Start frame fetcher thread
threading.Thread(target=frame_fetcher, daemon=True).start()

# Main loop
while True:
    if not frame_queue.empty():
        frame = frame_queue.get()
        detections = detect_vehicles(frame)

        for (label, conf, x, y, w, h) in detections:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        cv2.imshow("YOLO Detection - ESP32-CAM", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
