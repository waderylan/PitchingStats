import json
import requests


# Load JSON file
def load_json(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None


# Send data to Flask API
def send_to_flask(json_data, url="http://127.0.0.1:5000/compute-stats"):
    try:
        response = requests.post(url, json=json_data)
        if response.status_code == 200:
            print("Response from Flask:")
            print(json.dumps(response.json(), indent=4))
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error sending request: {e}")


if __name__ == "__main__":
    file_path = r"C:\Users\Rylan Wade\Downloads\3_9_25_game2_pitching_data.json"  # Change this to your JSON file path
    json_data = load_json(file_path)

    if json_data:
        send_to_flask(json_data)
