import cv2
from ultralytics import YOLO
import time
import tkinter as tk  # For screen size detection

# Configuration
VIDEO_PATH = "test_video.mp4"  # Replace with your video path
MODEL_PATH = "Datasets/sample-v5/best.pt"
CONF_THRESHOLD = 0.5
SHOW_CONF = True
OUTPUT_VIDEO = True

# Get screen dimensions
root = tk.Tk()
screen_width = root.winfo_screenwidth() - 100  # Allow space for window borders
screen_height = root.winfo_screenheight() - 100
root.destroy()

# Load model
model = YOLO(MODEL_PATH)

# Open video
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"Error opening video file {VIDEO_PATH}")
    exit()

# Get video properties
orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Calculate display size
width_ratio = screen_width / orig_width
height_ratio = screen_height / orig_height
scale = min(width_ratio, height_ratio, 1)  # Don't scale up small videos
display_size = (int(orig_width * scale), int(orig_height * scale))

# Initialize video writer (original size)
if OUTPUT_VIDEO:
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('Output/output_video.mp4', fourcc, fps, (orig_width, orig_height))

# FPS calculation
prev_time = 0
new_time = 0

# Create resizable window
cv2.namedWindow("Vehicle Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Vehicle Detection", display_size[0], display_size[1])

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Detection
    results = model(frame, verbose=False, conf=CONF_THRESHOLD)
    
    # Annotations
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            
            # Original size annotations
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), int(2/scale))
            if SHOW_CONF:
                label = f"Car: {conf:.2f}"
                cv2.putText(frame, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6/scale, (0,255,0), int(2/scale))

    # FPS counter
    new_time = time.time()
    fps_text = f"FPS: {1/(new_time - prev_time):.1f}"
    prev_time = new_time
    cv2.putText(frame, fps_text, (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8/scale, (0,255,0), int(2/scale))

    # Save original size frame
    if OUTPUT_VIDEO:
        out.write(frame)

    # Resize for display
    display_frame = cv2.resize(frame, display_size)

    # Show resized frame
    cv2.imshow("Vehicle Detection", display_frame)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
if OUTPUT_VIDEO:
    out.release()
cv2.destroyAllWindows()
print("Processing complete!")