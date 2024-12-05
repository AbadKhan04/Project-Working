import cv2
import threading
import queue
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import random
import numpy as np
import urllib.request
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configuration
ESP32_STREAM_URL = 'http://192.168.137.52/stream'  # Replace with your camera URL
QUEUE_MAXSIZE = 5
DISTANCE_WARNING_THRESHOLD = 50

# Shared Variables
frame_queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
front_distance = 0
back_distance = 0
running = False
vehicle_log = []

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
        if running:  # Suppress errors only if running is False
            print(f"Error in frame fetcher: {e}")

# Distance Simulation
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

        # Theme variable
        self.theme = "Light"

        # Main Frames
        self.video_frame = tk.Label(root, text="Video Stream", bg="white")
        self.video_frame.grid(row=0, column=0, rowspan=4, columnspan=2, padx=10, pady=10)

        self.control_frame = tk.Frame(root, bg="lightgray", relief="groove")
        self.control_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        self.chart_frame = tk.Frame(root, bg="lightgray", relief="groove")
        self.chart_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)

        self.warning_label = tk.Label(root, text="", font=("Arial", 16), fg="red", bg="white")
        self.warning_label.grid(row=3, column=2, pady=10)

        self.log_text = tk.Text(root, height=10, width=40, wrap=tk.WORD, bg="white", fg="black")
        self.log_text.grid(row=4, column=0, columnspan=3, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)

        # Control Buttons
        self.start_btn = ttk.Button(self.control_frame, text="Start Stream", command=self.start_stream)
        self.start_btn.pack(pady=5)

        self.stop_btn = ttk.Button(self.control_frame, text="Stop Stream", command=self.stop_stream)
        self.stop_btn.pack(pady=5)

        self.reset_btn = ttk.Button(self.control_frame, text="Reset Stats", command=self.reset_stats)
        self.reset_btn.pack(pady=5)

        self.change_theme_btn = ttk.Button(self.control_frame, text="Change Theme", command=self.change_theme)
        self.change_theme_btn.pack(pady=5)

        # Placeholder Chart
        self.fig, self.ax = plt.subplots(figsize=(4, 3))
        self.chart = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.chart.get_tk_widget().pack()
        self.ax.bar(["Cars", "Bikes", "Trucks"], [5, 3, 2])

        self.update_chart()

        # Close event handling
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_stream(self):
        global running
        if not running:
            running = True
            self.warning_label.config(text="")  # Clear warning
            self.log_event("Stream started.")
            threading.Thread(target=frame_fetcher, daemon=True).start()
            threading.Thread(target=distance_sensor_simulation, daemon=True).start()
            self.update_video()

    def stop_stream(self):
        global running
        running = False
        self.log_event("Stream stopped.")
        self.warning_label.config(text="Stream Stopped")

    def reset_stats(self):
        self.log_event("Stats reset.")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def change_theme(self):
        if self.theme == "Light":
            self.dark_theme()
        else:
            self.light_theme()

    def log_event(self, event):
        vehicle_log.append(event)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{event}\n")
        self.log_text.config(state=tk.DISABLED)

    def update_video(self):
        global running
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

    def light_theme(self):
        self.root.configure(bg="white")
        self.video_frame.config(bg="white")
        self.control_frame.config(bg="lightgray")
        self.chart_frame.config(bg="lightgray")
        self.warning_label.config(bg="white", fg="red")
        self.log_text.config(bg="white", fg="black")
        self.theme = "Light"

    def dark_theme(self):
        self.root.configure(bg="black")
        self.video_frame.config(bg="black")
        self.control_frame.config(bg="darkgray")
        self.chart_frame.config(bg="darkgray")
        self.warning_label.config(bg="black", fg="red")
        self.log_text.config(bg="black", fg="white")
        self.theme = "Dark"

    def on_close(self):
        global running
        running = False
        self.root.destroy()  # Properly close the application window


# Run the Application
root = tk.Tk()
app = VehicleDetectionDashboard(root)
root.mainloop()
