import cv2
from ultralytics import YOLO
import time
import threading
import queue

# Configuration
VIDEO_PATH = "test_video.mp4"
MODEL_PATH = "Datasets/sample-v5/best.pt"
CONF_THRESHOLD = 0.5
OUTPUT_VIDEO = True
SHOW_DISPLAY = False  # Turn off for maximum speed
USE_GPU = True  # Requires CUDA-compatible GPU

# Optimization parameters
FRAME_SKIP = 2  # Process every 3rd frame
BATCH_SIZE = 4  # Process multiple frames together if GPU memory allows
QUEUE_SIZE = 8  # Buffer for parallel processing

# Initialize model with GPU if available
model = YOLO(MODEL_PATH)
if USE_GPU:
    model.to('cuda')

# Frame queue for parallel processing
frame_queue = queue.Queue(maxsize=QUEUE_SIZE)

def video_reader():
    """Threaded video reader for better I/O performance"""
    cap = cv2.VideoCapture(VIDEO_PATH)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % (FRAME_SKIP + 1) == 0:
            while frame_queue.qsize() >= QUEUE_SIZE:
                time.sleep(0.01)
            frame_queue.put((frame_count, frame))
        frame_count += 1
    cap.release()
    frame_queue.put((None, None))

# Start video reader thread
threading.Thread(target=video_reader, daemon=True).start()

# Get video properties
cap = cv2.VideoCapture(VIDEO_PATH)
orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()

# Initialize video writer
if OUTPUT_VIDEO:
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('Output/output_video.mp4', fourcc, fps/(FRAME_SKIP+1), (orig_width, orig_height))

# Processing loop
processed_frames = 0
start_time = time.time()
batch_frames = []

while True:
    frame_id, frame = frame_queue.get()
    if frame is None:
        break
    
    batch_frames.append((frame_id, frame))
    
    # Process in batches for better GPU utilization
    if len(batch_frames) >= BATCH_SIZE:
        # Prepare batch
        batch = [f[1] for f in batch_frames]
        
        # Run detection
        results = model(batch, verbose=False, conf=CONF_THRESHOLD)
        
        # Process results
        for i, result in enumerate(results):
            frame_id, frame = batch_frames[i]
            boxes = result.boxes
            
            # Draw detections if needed
            if OUTPUT_VIDEO or SHOW_DISPLAY:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Write to output
            if OUTPUT_VIDEO:
                out.write(frame)
            
            # Show progress
            processed_frames += 1
            if processed_frames % 10 == 0:
                elapsed = time.time() - start_time
                fps = processed_frames / elapsed
                remaining = (total_frames - processed_frames) / fps
                print(f"Processed {processed_frames}/{total_frames} frames | "
                      f"FPS: {fps:.1f} | "
                      f"ETA: {remaining//60:.0f}m {remaining%60:.0f}s")
        
        batch_frames.clear()

# Cleanup
if OUTPUT_VIDEO:
    out.release()
    
if SHOW_DISPLAY:
    cv2.destroyAllWindows()

print(f"Processing complete! Total time: {time.time()-start_time:.2f} seconds")