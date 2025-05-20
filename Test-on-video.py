import cv2
from ultralytics import YOLO
import time

# Configuration
VIDEO_PATH = "videoplayback.mp4"  # Replace with your video path
MODEL_PATH = "Datasets/sample-v3/best.pt"  # Your trained model
CONF_THRESHOLD = 0.5  # Confidence threshold
SHOW_CONF = True  # Show confidence scores
OUTPUT_VIDEO = True  # Save processed video

# Load custom model
model = YOLO(MODEL_PATH)

# Open video file
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"Error opening video file {VIDEO_PATH}")
    exit()

# Get video properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Initialize video writer if needed
if OUTPUT_VIDEO:
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('Output/output-train.mp4', fourcc, fps, (frame_width, frame_height))

# For FPS calculation
prev_time = 0
new_time = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Perform detection
    results = model(frame, verbose=False, conf=CONF_THRESHOLD)
    
    # Process results
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Get bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Get confidence score
            conf = float(box.conf[0])
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add confidence text
            if SHOW_CONF:
                label = f"Car: {conf:.2f}"
                cv2.putText(frame, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    # Calculate FPS
    new_time = time.time()
    fps = 1/(new_time - prev_time)
    prev_time = new_time
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    # Show result
    cv2.imshow("Vehicle Detection", frame)
    
    # Write to output file
    if OUTPUT_VIDEO:
        out.write(frame)

    # Exit on 'q' press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
if OUTPUT_VIDEO:
    out.release()
cv2.destroyAllWindows()
print("Video processing completed!")