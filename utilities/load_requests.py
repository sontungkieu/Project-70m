import json
import os
from objects.request import Request

def load_requests(file_path):
    # Construct the path to the JSON file
    # file_path = os.path.join("data", "requests0.json")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # The file contains a JSON array (list) of requests
            requests_list = json.load(file)
            requests_list = [Request.from_list(req) for req in requests_list]
            return requests_list
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

if __name__ == "__main__":
    requests_list = load_requests()
    print("List of requests:")
    print(requests_list)