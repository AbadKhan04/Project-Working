import cv2

# ESP32-CAM stream URL (Replace with your ESP32-CAM IP)
url = 'http://192.168.137.18/stream'

# Start capturing video from the ESP32-CAM
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Cannot open ESP32-CAM stream from ESP32-CAM")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    # Display the frame
    cv2.imshow("ESP32-CAM Stream", frame)

    # Press 'q' to quit the window
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object
cap.release()
cv2.destroyAllWindows()
