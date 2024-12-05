import requests
import time

# ESP8266 Distance Sensor URLs
FRONT_SENSOR_URL = 'http://192.168.137.32/'  # Front sensor ESP8266 IP
BACK_SENSOR_URL = 'http://192.168.137.32/'  # Back sensor ESP8266 IP

def fetch_distance(sensor_url):
    try:
        # Fetch JSON data from the ESP8266 server
        response = requests.get(sensor_url)
        if response.status_code == 200:
            data = response.json()
            front_distance = data.get("front", 0)
            back_distance = data.get("back", 0)
            overtaking = data.get("overtaking", False)
            return front_distance, back_distance, overtaking
        else:
            print(f"Failed to fetch data from {sensor_url}, Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching data from {sensor_url}: {e}")
    return 0, 0, False

def main():
    while True:
        # Fetch data from both sensors
        front_distance, back_distance, front_overtaking = fetch_distance(FRONT_SENSOR_URL)
        back_distance, _, back_overtaking = fetch_distance(BACK_SENSOR_URL)

        # Display results
        print(f"Front Distance: {front_distance} cm")
        print(f"Back Distance: {back_distance} cm")
        print(f"Overtaking Detected (Front): {front_overtaking}")
        print(f"Overtaking Detected (Back): {back_overtaking}")

        # Warning system
        if front_distance < 50 and front_distance > 0:
            print("Warning: Vehicle too close at the front!")
        if back_distance < 50 and back_distance > 0:
            print("Warning: Vehicle too close at the back!")

        time.sleep(0.1)

if __name__ == "__main__":
    main()
