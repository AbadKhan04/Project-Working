import cv2
import threading
import queue
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt  # Add this line at the top with other imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import random
import numpy as np
import urllib.request

# Configuration
ESP32_STREAM_URL = 'http://192.168.137.33/stream'  # Update with your camera's URL
QUEUE_MAXSIZE = 5
DISTANCE_WARNING_THRESHOLD = 50

# Shared Variables
frame_queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
front_distance = 0
back_distance = 0
running = False

# Frame Fetching
def frame_fetcher():
    global running
    try:
        stream = urllib.request.urlopen(ESP32_STREAM_URL)
        bytes_data = b''
        while running:
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

# Distance Simulation (Replace with actual sensor data fetching logic)
def distance_sensor_simulation():
    global front_distance, back_distance
    while running:
        front_distance = random.randint(20, 100)  # Simulated distance values
        back_distance = random.randint(20, 100)
        time.sleep(0.5)

# GUI Updates and Rendering
class VehicleDetectionDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Vehicle Detection Dashboard")
        self.root.geometry("1200x800")

        # Main Frames
        self.video_frame = tk.Label(root, text="Video Stream")
        self.video_frame.grid(row=0, column=0, rowspan=4, columnspan=2, padx=10, pady=10)

        self.control_frame = ttk.Frame(root, borderwidth=2, relief="groove")
        self.control_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        self.chart_frame = ttk.Frame(root, borderwidth=2, relief="groove")
        self.chart_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)

        self.warning_label = tk.Label(root, text="", font=("Arial", 16), fg="red")
        self.warning_label.grid(row=3, column=2, pady=10)

        # Control Buttons
        self.start_btn = ttk.Button(self.control_frame, text="Start Stream", command=self.start_stream)
        self.start_btn.pack(pady=5)

        self.stop_btn = ttk.Button(self.control_frame, text="Stop Stream", command=self.stop_stream)
        self.stop_btn.pack(pady=5)

        # Placeholder Chart
        self.fig, self.ax = plt.subplots(figsize=(4, 3))
        self.chart = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.chart.get_tk_widget().pack()
        self.ax.bar(["Cars", "Bikes", "Trucks"], [5, 3, 2])

        self.update_chart()

    def start_stream(self):
        global running
        if not running:
            running = True
            threading.Thread(target=frame_fetcher, daemon=True).start()
            threading.Thread(target=distance_sensor_simulation, daemon=True).start()
            self.update_video()

    def stop_stream(self):
        global running
        running = False
        self.warning_label.config(text="Stream Stopped")

    def update_video(self):
        if not running:
            return

        if not frame_queue.empty():
            frame = frame_queue.get()
            # Draw warning on frame
            if front_distance < DISTANCE_WARNING_THRESHOLD:
                cv2.putText(frame, "Front Warning!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if back_distance < DISTANCE_WARNING_THRESHOLD:
                cv2.putText(frame, "Back Warning!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Convert frame for Tkinter
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            self.video_frame.config(image=img)
            self.video_frame.image = img

        self.root.after(10, self.update_video)

    def update_chart(self):
        # Simulate live updates for chart
        self.ax.clear()
        vehicle_types = ["Cars", "Bikes", "Trucks"]
        counts = [random.randint(1, 10) for _ in vehicle_types]
        self.ax.bar(vehicle_types, counts, color=["blue", "green", "orange"])
        self.chart.draw()
        self.root.after(2000, self.update_chart)  # Update chart every 2 seconds

# Run the Application
root = tk.Tk()
app = VehicleDetectionDashboard(root)
root.mainloop()
