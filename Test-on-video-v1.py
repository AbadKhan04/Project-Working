import cv2
from ultralytics import YOLO
import time
import tkinter as tk
import os

# Configuration
VIDEO_PATH = "test_video.mp4"  # Replace with your video path
MODEL_PATH = "D:\\Abad Khan\\Final Year Project-2024\\Project Working\\Datasets\\sample-v5\\best.pt"
CONF_THRESHOLD = 0.5
SHOW_CONF = True
OUTPUT_VIDEO = True

# Check paths
if not os.path.isfile(VIDEO_PATH):
    print(f"[ERROR] Video not found: {VIDEO_PATH}")
    exit()
if not os.path.isfile(MODEL_PATH):
    print(f"[ERROR] Model not found: {MODEL_PATH}")
    exit()

# Get screen size
root = tk.Tk()
screen_width = root.winfo_screenwidth() - 100
screen_height = root.winfo_screenheight() - 100
root.destroy()

# Load model
model = YOLO(MODEL_PATH)

# Open video
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"[ERROR] Cannot open video file {VIDEO_PATH}")
    exit()

# Get video properties
orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps

# Scale to screen
scale = min(screen_width / orig_width, screen_height / orig_height, 1)
display_size = (int(orig_width * scale), int(orig_height * scale))

# Video writer
if OUTPUT_VIDEO:
    os.makedirs("Output", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter("Output/output_video.mp4", fourcc, fps, (orig_width, orig_height))

# Create window
cv2.namedWindow("Vehicle Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Vehicle Detection", display_size[0], display_size[1])

# Playback control
paused = False
frame_skip = int(fps * 10)  # 10 seconds forward
prev_time = time.time()

while cap.isOpened():
    if not paused:
        ret, frame = cap.read()
        if not ret:
            break

        # Run detection
        results = model(frame, verbose=False, conf=CONF_THRESHOLD)

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), int(2 / scale))
                if SHOW_CONF:
                    cv2.putText(frame, f"Car: {conf:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6 / scale, (0, 255, 0), int(2 / scale))

        # FPS display
        new_time = time.time()
        fps_text = f"FPS: {1 / (new_time - prev_time):.1f}"
        prev_time = new_time
        cv2.putText(frame, fps_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8 / scale, (0, 255, 0), int(2 / scale))

        # Save full-size frame
        if OUTPUT_VIDEO:
            out.write(frame)

        # Resize for screen
        display_frame = cv2.resize(frame, display_size)
        cv2.imshow("Vehicle Detection", display_frame)

    # Key events
    key = cv2.waitKey(10) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('p'):
        paused = not paused
        print("[INFO] Paused" if paused else "[INFO] Resumed")
    elif key == ord('f'):
        current = cap.get(cv2.CAP_PROP_POS_FRAMES)
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(current + frame_skip, total_frames - 1))
        print(f"[INFO] Skipped forward to {cap.get(cv2.CAP_PROP_POS_MSEC) / 1000:.2f}s")

# Cleanup
cap.release()
if OUTPUT_VIDEO:
    out.release()
cv2.destroyAllWindows()
print("✅ Processing complete.")
