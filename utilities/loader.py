import json
import os

from objects.request import Request
from objects.driver import Driver

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

def load_drivers(file_path="data/drivers.json", is_converted_to_list=False):
    # Construct the path to the JSON file
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # The file contains a JSON array (list) of drivers
            drivers_list = json.load(file)
            # Convert each driver dictionary to Driver object using from_dict
            drivers_list = [Driver.from_dict(driver) for driver in drivers_list]
            
            if is_converted_to_list:
                # Sort by name and then by cccd
                drivers_list.sort(key=lambda x: (x.name, x.cccd))
                # Extract vehicle_loads and available_times
                vehicle_loads = [driver.vehicle_load for driver in drivers_list]
                available_times_s = [driver.available_times for driver in drivers_list]
                return drivers_list, vehicle_loads, available_times_s
            else:
                return drivers_list
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return [] if not is_converted_to_list else ([], [], [])

def accept_accumulated_distance():
    """
    Chấp nhận khoảng cách tích lũy
    postprocessing, inverse_mapping, 
    load_drivers, cộng khoảng cách, ghi đè driver
    """
    pass

if __name__ == "__main__":
    requests_list = load_requests()
    print("List of requests:")
    print(requests_list)
    # Load requests (giữ nguyên code của bạn)
    requests_list = load_requests("data/requests0.json")
    print("List of requests:")
    print(requests_list)
    
    # Load drivers (không convert)
    print("\nList of drivers (not converted):")
    drivers_list = load_drivers("data/drivers.json", is_converted_to_list=False)
    for driver in drivers_list:
        print(driver)
    
    # Load drivers (converted to lists)
    print("\nList of drivers (converted to lists):")
    drivers_list, vehicle_loads, available_times_s = load_drivers("data/drivers.json", is_converted_to_list=True)
    print("Drivers:")
    for driver in drivers_list:
        print(driver)
    print("Vehicle loads:", vehicle_loads)
    print("Available times:", available_times_s)