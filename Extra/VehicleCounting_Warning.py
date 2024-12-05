vehicle_count = 0

def stream_video_with_counting():
    global vehicle_count
    while True:
        img_resp = urllib.request.urlopen(url)
        img_np = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        frame = cv2.imdecode(img_np, -1)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        vehicles = vehicle_cascade.detectMultiScale(gray, 1.1, 4)
        
        for (x, y, w, h) in vehicles:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        vehicle_count += len(vehicles)
        print(f"Total Vehicles Detected: {vehicle_count}")
        
        cv2.imshow("ESP32-CAM Stream with Counting", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()

integrated_system()
