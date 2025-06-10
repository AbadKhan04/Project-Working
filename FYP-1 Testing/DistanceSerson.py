import requests
import time

# Replace with the IP of your ESP8266
url = 'http://192.168.137.206/'  # ESP8266 IP

while True:
    try:
        # Send request to the ESP8266 server
        response = requests.get(url)
        
        # Check if the response is successful
        if response.status_code == 200:
            distance = response.text.strip()

            # Remove any "cm" from the distance string, if present
            distance = distance.replace(' cm', '')

            # Convert the distance to float, and ignore zero or invalid values
            try:
                distance_value = float(distance)
                
                if distance_value > 0:
                    print(f"Distance: {distance_value} cm")

                    # Warning system for distances less than 50 cm
                    if distance_value < 50:
                        print("Warning: Vehicle too close!")
                else:
                    print("No valid distance detected (0 cm)")

            except ValueError:
                print(f"Invalid distance format: '{distance}'")
        
        # Wait for 1 second before the next request
        time.sleep(1)

    except Exception as e:
        print(f"Error: {e}")
