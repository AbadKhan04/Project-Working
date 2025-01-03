from flask import Flask, render_template, Response, jsonify
import threading
import json
import numpy as np
import os
import csv
from queue import Queue
import requests
import time
import cv2
import queue
import urllib.request
from detection import detect_vehicles, draw_detections

app = Flask(__name__)

# Paths to your log files
LOG_FILE = 'vehicle_log.csv'

# Queue to hold real-time data
data_queue = Queue(maxsize=1)
# Shared global dictionary for metrics data
frame_queue = queue.Queue(maxsize=10)
metrics_data = {
    "front_distance": 0,
    "back_distance": 0,
    "total_vehicle_count": 0,
    "overtaking": False
}
ESP32_STREAM_URL = 'http://192.168.137.76/stream'

# Function to fetch frames from ESP32
def fetch_frames():
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
        print(f"Error fetching frames: {e}")

# Start frame fetching in a thread
fetch_thread = threading.Thread(target=fetch_frames, daemon=True)
fetch_thread.start()

# Generator for raw frames
def gen_raw_frames():
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# Generator for OpenCV-processed frames
def gen_opencv_frames():
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()

            # Example OpenCV processing: Convert to grayscale
            processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_GRAY2BGR)

            # Encoding the processed frame
            _, buffer = cv2.imencode('.jpg', processed_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


# Function to fetch metrics periodically
# Thread to fetch real-time data
def fetch_real_time_data():
    global metrics_data

    ESP8266_IP = "192.168.137.115"  # Replace with your ESP8266's IP address
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

        # Simulate total vehicle count increment (if needed)
        metrics_data["total_vehicle_count"] += 1
        time.sleep(1)  # Adjust the interval as needed


# API to provide metrics from JSON or real-time
@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify(metrics_data)  # Serve metrics data as JSON

# API to provide log data from CSV
@app.route('/logs')
def logs():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                logs.append(row)
    return jsonify(logs)


# Route for video feed
@app.route('/video_feed/raw')
def raw_video_feed():
    return Response(gen_raw_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/opencv')
def opencv_video_feed():
    return Response(gen_opencv_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Main dashboard route
@app.route('/')
def index():
    return render_template('dashboard.html')

if __name__ == '__main__':
    # Start real-time data thread
    data_thread = threading.Thread(target=fetch_real_time_data, daemon=True)
    data_thread.start()

    # Run the Flask app
    app.run(debug=True)
