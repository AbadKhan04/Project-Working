import cv2
import urllib.request
import numpy as np

# URL of ESP32-CAM stream
url = 'http://<ESP32-CAM-IP>/stream'

# OpenCV setup for vehicle detection
vehicle_cascade = cv2.CascadeClassifier('cars.xml')

def stream_video():
    while True:
        img_resp = urllib.request.urlopen(url)
        img_np = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        frame = cv2.imdecode(img_np, -1)
        
        # Convert frame to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Vehicle detection
        vehicles = vehicle_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in vehicles:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Show the stream
        cv2.imshow("ESP32-CAM Stream", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()

stream_video()
