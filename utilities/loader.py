import json
import os
import logging

from objects.request import Request
from objects.driver import Driver
from config import *

def load_requests(file_path):
    # Construct the path to the JSON file
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # The file contains a JSON array (list) of requests
            requests_list = json.load(file)[:45]
            # print(f"loader.py:load_requests: len {len(requests_list)} :{requests_list}")
            requests_list = [Request.from_dict(req) for req in requests_list]
            requests_list.sort(key=lambda x: x.request_id)
            for i in range(len(requests_list)):
                requests_list[i].weight *= CAPACITY_SCALE
                requests_list[i].timeframe = [requests_list[i].timeframe[0] * TIME_SCALE, requests_list[i].timeframe[1] * TIME_SCALE]
            return requests_list
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_drivers(file_path="data/drivers.json", is_converted_to_dict=False):
    """
    Load driver data from a JSON file and convert it to Driver objects or processed lists.
    
    Args:
        file_path (str): Path to the JSON file (default: "data/drivers.json")
        is_converted_to_dict (bool): If True, return data as separate lists (default: False)
    
    Returns:
        If is_converted_to_dict=False: list of Driver objects
        If is_converted_to_dict=True: tuple of (drivers_list, vehicle_loads, available_times_s)
    """
    # logging.info(f"loader.py:load_drivers:file_path: {file_path}")
    # logging.info(f"loader.py:load_drivers:is_converted_to_dict: {is_converted_to_dict}")
    global NUM_OF_VEHICLES

    # Log absolute file path for debugging
    abs_path = os.path.abspath(file_path)
    # logging.info(f"loader.py:load_drivers:absolute_path: {abs_path}")

    # Check if file exists
    if not os.path.exists(file_path):
        logging.error(f"File not found at {file_path}")
        return [] if not is_converted_to_dict else ([], [], [])

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # logging.info(f"loader.py:load_drivers:open file {file_path}")
            
            # Read and log raw content
            raw_content = file.read().strip()
            # logging.info(f"loader.py:load_drivers:raw_content: '{raw_content}'")
            
            if not raw_content:
                logging.error(f"File {file_path} is empty")
                return [] if not is_converted_to_dict else ([], [], [])
            
            # Reset file pointer and parse JSON
            file.seek(0)
            drivers_list = json.load(file)
            # logging.info(f"loader.py:load_drivers:parsed_json: {drivers_list}")
            
            # Validate JSON structure
            if not isinstance(drivers_list, list):
                logging.error(f"Invalid JSON format in {file_path}: Expected a list, got {type(drivers_list)}")
                return [] if not is_converted_to_dict else ([], [], [])
            
            # Convert to Driver objects
            drivers_list = [Driver.from_dict(driver) for driver in drivers_list]
            drivers_list.sort(key=lambda x:(x.name,x.cccd,x.phone_number))
            # logging.info(f"loader.py:load_drivers:converted_drivers: {drivers_list}")
            
            # Process drivers
            for i in range(len(drivers_list)):
                drivers_list[i].vehicle_load = int(drivers_list[i].vehicle_load*CAPACITY_SCALE)
                for key in drivers_list[i].available_times.keys():
                    # print("loader.py:load_drivers:available_times:", drivers_list[i].available_times)
                    # print("loader.py:load_drivers:available_times[key]:", drivers_list[i].available_times[key])
                    for j in range(len(drivers_list[i].available_times[key])):
                        # "type(drivers_list[i].vehicle_load[key]))
                        if isinstance(drivers_list[i].available_times[key][j], list):
                            drivers_list[i].available_times[key][j] = [int(x * TIME_SCALE) for x in drivers_list[i].available_times[key][j]]
            
            NUM_OF_VEHICLES = len(drivers_list)
            # logging.info(f"loader.py:load_drivers:NUM_OF_VEHICLES: {NUM_OF_VEHICLES}")
            
            if is_converted_to_dict:
                drivers_list.sort(key=lambda x: (x.name, x.cccd))
                vehicle_loads = [driver.vehicle_load for driver in drivers_list]
                available_times_s = [driver.available_times for driver in drivers_list]
                
                # logging.info(f"loader.py:load_drivers:vehicle_loads: {vehicle_loads}")
                # logging.info(f"loader.py:load_drivers:available_times_s: {available_times_s}")
                return drivers_list, vehicle_loads, available_times_s
            else:
                return drivers_list
                
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error in {file_path}: {str(e)}")
    except FileNotFoundError:
        logging.error(f"Cannot find file {file_path}")
    except PermissionError:
        logging.error(f"Permission denied accessing {file_path}")
    except AttributeError as e:
        logging.error(f"Driver object attribute error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error reading {file_path}: {str(e)}", exc_info=True)  # Include stack trace
    
    return [] if not is_converted_to_dict else ([], [], [])

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
    drivers_list = load_drivers("data/drivers.json", is_converted_to_dict=False)
    for driver in drivers_list:
        print(driver)
    
    # Load drivers (converted to lists)
    print("\nList of drivers (converted to lists):")
    drivers_list, vehicle_loads, available_times_s = load_drivers("data/drivers.json", is_converted_to_dict=True)
    print("Drivers:")
    for driver in drivers_list:
        print(driver)
    print("Vehicle loads:", vehicle_loads)
    print("Available times:", available_times_s)