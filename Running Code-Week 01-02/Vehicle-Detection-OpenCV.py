import cv2
import numpy as np
import urllib.request

# ESP32 Stream URL (adjust IP if different)
# url = 'http://192.168.100.12/stream'
url = 'http://192.168.137.55/stream'  # ESP8266 IP http://192.168.137.55

# Function to detect vehicles using OpenCV
def detect_vehicles(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Load the pre-trained car classifier
    car_cascade = cv2.CascadeClassifier('car.xml')  # Use relative path for car.xml

    # Detect vehicles
    cars = car_cascade.detectMultiScale(gray, 1.1, 1)

    for (x, y, w, h) in cars:
        # Draw rectangle around detected vehicles
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return frame, len(cars)

# Function to get the video stream from ESP32
def get_stream():
    stream = urllib.request.urlopen(url)
    bytes_data = b''
    
    while True:
        bytes_data += stream.read(1024)
        a = bytes_data.find(b'\xff\xd8')  # Start of JPEG
        b = bytes_data.find(b'\xff\xd9')  # End of JPEG

        if a != -1 and b != -1:
            jpg = bytes_data[a:b + 2]
            bytes_data = bytes_data[b + 2:]
            
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

            if frame is not None:
                # Detect vehicles and show count
                frame, vehicle_count = detect_vehicles(frame)
                cv2.putText(frame, f"Vehicles Detected: {vehicle_count}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Display the frame
                cv2.imshow('ESP32-CAM Stream', frame)

                # Press 'q' to quit the stream
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    cv2.destroyAllWindows()

# Start video stream
get_stream()
