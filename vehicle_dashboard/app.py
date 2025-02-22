from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
import urllib.request
import threading
import queue
import time
import requests
import os
import csv
from detection import detect_vehicles, draw_detections

app = Flask(__name__)

# Global variables
frame_queue = queue.Queue(maxsize=5)
current_frame = None
frame_lock = threading.Lock()
stream = None
bytes_data = b''

metrics_data = {
    "front_distance": 0,
    "back_distance": 0,
    "total_vehicle_count": 0,
    "overtaking": False
}

# Function to simulate ESP32 stream
def gen_frames():
    import cv2
    import urllib.request
    stream = urllib.request.urlopen('http://192.168.137.199/stream')
    bytes_data = b''
    while True:
        try:
            bytes_data += stream.read(4096)
            a = bytes_data.find(b'\xff\xd8')
            b = bytes_data.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes_data[a:b + 2]
                bytes_data = bytes_data[b + 2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except Exception as e:
            print(f"Error in video feed: {e}")
            break
def fetch_real_time_data():
    while True:
        try:
            response = requests.get(f"http://192.168.137.41/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                metrics_data.update({
                    "front_distance": data.get("front", 0),
                    "back_distance": data.get("back", 0),
                    "overtaking": data.get("overtaking", False)
                })
        except Exception as e:
            print(f"Sensor error: {e}")
        time.sleep(1)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/metrics')
def get_metrics():
    return jsonify(metrics_data)

@app.route('/logs')
def logs():
    if os.path.exists('vehicle_data.csv'):
        with open('vehicle_data.csv', 'r') as file:
            return jsonify(list(csv.DictReader(file)))
    return jsonify([])

if __name__ == '__main__':
    threading.Thread(target=fetch_real_time_data, daemon=True).start()
    app.run(debug=True)