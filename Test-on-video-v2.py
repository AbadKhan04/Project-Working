import cv2
from ultralytics import YOLO
import time
import tkinter as tk
import os

# Configuration
VIDEO_PATH = r"D:\Abad Khan\Final Year Project-2024\Project Working\test_video.mp4"  # Adjust path
MODEL_PATH = r"D:\Abad Khan\Final Year Project-2024\Project Working\Datasets\sample-v5\best.pt"
CONF_THRESHOLD = 0.5
SHOW_CONF = True
OUTPUT_VIDEO = True

# Setup screen size
root = tk.Tk()
screen_width = root.winfo_screenwidth() - 100
screen_height = root.winfo_screenheight() - 100
root.destroy()

# Load model
model = YOLO(MODEL_PATH)

# Open video
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"[ERROR] Cannot open video: {VIDEO_PATH}")
    exit()

# Video properties
orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Resize display
scale = min(screen_width / orig_width, screen_height / orig_height, 1)
display_size = (int(orig_width * scale), int(orig_height * scale))

# Output video
if OUTPUT_VIDEO:
    os.makedirs("Output", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('Output/output_video.mp4', fourcc, fps, (orig_width, orig_height))

# Initialize window
cv2.namedWindow("Vehicle Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Vehicle Detection", display_size[0], display_size[1])

paused = False
prev_time = 0

frame_id = 0
while cap.isOpened():
    if not paused:
        ret, frame = cap.read()
        if not ret:
            break
        frame_id += 1

        # Detect
        results = model(frame, conf=CONF_THRESHOLD, verbose=False)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), int(2/scale))
                if SHOW_CONF:
                    label = f"Car: {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6/scale, (0, 255, 0), int(2/scale))

        # FPS display
        new_time = time.time()
        fps_text = f"FPS: {1 / (new_time - prev_time):.1f}"
        prev_time = new_time
        cv2.putText(frame, fps_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8/scale, (0, 255, 0), int(2/scale))

        # Save output
        if OUTPUT_VIDEO:
            out.write(frame)

        # Resize for display
        display_frame = cv2.resize(frame, display_size)

    # Show the frame (either paused or updated)
    cv2.imshow("Vehicle Detection", display_frame)

    key = cv2.waitKey(10) & 0xFF

    if key == ord('q'):
        break
    elif key == ord(' '):  # pause/resume
        paused = not paused
    elif key == ord('s'):  # save frame
        filename = f"Output/frame_{frame_id}.png"
        cv2.imwrite(filename, frame)
        print(f"[INFO] Frame saved as {filename}")
    elif key == 83:  # right arrow (forward 5 sec)
        frame_skip = int(fps * 5)
        frame_id += frame_skip
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    elif key == 81:  # left arrow (backward 5 sec)
        frame_skip = int(fps * 5)
        frame_id = max(0, frame_id - frame_skip)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

# Cleanup
cap.release()
if OUTPUT_VIDEO:
    out.release()
cv2.destroyAllWindows()
print("✅ Video processing complete!")
