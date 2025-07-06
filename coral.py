import requests

try:
    response = requests.get("http://127.0.0.1:5555/")
    print(f"API status: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("Coral API is not running")