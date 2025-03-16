# app.py
from flask import Flask, render_template, Response, jsonify
import threading
import json
import numpy as np
import os
import csv
import requests
import time
import cv2
import queue
from detection import detect_vehicles, draw_detections
from stream_handler import FrameFetcher

app = Flask(__name__)

# Paths to your log files
LOG_FILE = 'vehicle_log.csv'

# Queues for real-time data and frames
data_queue = queue.Queue(maxsize=1)
frame_queue = queue.Queue(maxsize=5)

# Shared global dictionary for metrics data
metrics_data = {
    "front_distance": 0,
    "back_distance": 0,
    "total_vehicle_count": 0,
    "overtaking": False
}

# Initialize and start the frame fetcher
frame_fetcher = FrameFetcher(frame_queue, "http://192.168.137.26/stream")
frame_fetcher.start()

# Function to generate processed video frames with OpenCV detections
def processed_video_stream():
    while True:
        try:
            if not frame_queue.empty():
                frame = frame_queue.get()
                detections = detect_vehicles(frame)
                draw_detections(frame, detections)
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except Exception as e:
            print(f"Error in processed video stream: {e}")
            break

# Function to fetch metrics periodically
def fetch_real_time_data():
    global metrics_data
    ESP8266_IP = "192.168.137.149"
    ESP8266_URL = f"http://{ESP8266_IP}/"
    while True:
        try:
            response = requests.get(ESP8266_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                metrics_data["front_distance"] = data.get("front", 0)
                metrics_data["back_distance"] = data.get("back", 0)
                metrics_data["overtaking"] = data.get("overtaking", False)
            else:
                print(f"Error: Received status code {response.status_code} from ESP8266")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from ESP8266: {e}")
        metrics_data["total_vehicle_count"] += 1
        time.sleep(1)

@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify(metrics_data)

@app.route('/logs')
def logs():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                logs.append(row)
    return jsonify(logs)

@app.route('/video_feed/raw')
def raw_video_feed():
    return Response(frame_fetcher.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/opencv')
def opencv_video_feed():
    return Response(processed_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('dashboard.html')

if __name__ == '__main__':
    data_thread = threading.Thread(target=fetch_real_time_data, daemon=True)
    data_thread.start()
    app.run(debug=True)
