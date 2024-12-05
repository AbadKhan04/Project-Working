import cv2
import numpy as np
import time

# Configuration and Global Variables
YOLO_CONFIG = 'Datasets/yolov3-tiny.cfg'
YOLO_WEIGHTS = 'Datasets/yolov3-tiny.weights'
COCO_NAMES = 'Datasets/coco.names'
CONFIDENCE_THRESHOLD = 0.3
FRAME_RATE = 15

# Initialize YOLO model
def load_yolo():
    net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CONFIG)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    with open(COCO_NAMES, "r") as f:
        classes = [line.strip() for line in f.readlines()]
    return net, output_layers, classes

net, output_layers, classes = load_yolo()

# Function to detect vehicles
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

# Function to draw vehicle detections on the frame
def draw_detections(frame, detections):
    for idx, (label, confidence, x, y, w, h, cx, cy) in enumerate(detections):
        vehicle_id = f"{label}_{idx}"
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, f"{label} {confidence:.2f}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(frame, f"Speed: 0.00", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
