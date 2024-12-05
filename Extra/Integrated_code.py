import cv2

# Replace with your ESP32-CAM stream URL
esp32_url = 'http://<ESP32_CAM_IP>/stream'

# Load pre-trained car classifier (Haar cascade)
car_cascade = cv2.CascadeClassifier('cars.xml')

# Open the video stream
cap = cv2.VideoCapture(esp32_url)

if not cap.isOpened():
    print("Cannot open stream")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to capture frame")
        break

    # Convert to grayscale (for Haar cascade detection)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect cars in the frame
    cars = car_cascade.detectMultiScale(gray, 1.1, 1)

    # Draw rectangles around detected cars
    for (x, y, w, h) in cars:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

    # Display the resulting frame
    cv2.imshow('ESP32-CAM Stream with Car Detection', frame)

    # Press 'q' on the keyboard to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()
