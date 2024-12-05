import requests
import time

# Replace with the IP of your ESP8266
url = 'http://192.168.100.198/'  # ESP8266 IP

while True:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            distance = response.text
            print(f"Distance: {distance} cm")

            # Example: Adding a distance-based warning system
            if float(distance) < 50:  # Threshold distance for warning
                print("Warning: Vehicle too close!")

        time.sleep(1)

    except Exception as e:
        print(f"Error: {e}")
