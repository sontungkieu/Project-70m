from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import csv
import re
import requests

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)

# List of permanent warehouses with their coordinates
WAREHOUSES = [
    ("1", "Warehouse 01", "Hanoi, Vietnam"),
    ("2", "Warehouse 02", "Ho Chi Minh, Vietnam")
]

def get_coordinates(address):
    """
    Uses Selenium to fetch latitude and longitude from Google Maps.
    """
    search_url = f"https://www.google.com/maps/search/{address.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+),', response.text)
        if match:
            lat, lng = match.groups()
            return float(lat), float(lng)
    
    return None  

def calculate_distance(origin_coords, destination_coords):
    """
    Uses Selenium to fetch the real travel distance from Google Maps.
    """
    origin = f"{origin_coords[0]},{origin_coords[1]}"
    destination = f"{destination_coords[0]},{destination_coords[1]}"
    driver.get("https://www.google.com/maps/dir/" + origin + "/" + destination)
    
    time.sleep(5)
    
    try:
        # Click on the element before extracting the distance
        button_element = driver.find_element(By.CLASS_NAME, "em41nd")
        button_element.click()
        time.sleep(2)
        
        distance_element = driver.find_element(By.XPATH, "//div[contains(@class, 'ivN21e tUEI8e fontBodyMedium')]")  
        distance = distance_element.text
    except:
        distance = "Not Found"
    
    return distance

def process_destinations(input_csv, output_csv):
    """
    Reads a CSV file with destinations, converts addresses to coordinates,
    and calculates distances to fixed warehouses.
    """
    destinations = []
    
    with open(input_csv, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            destinations.append((row[0], row[1], row[2]))  # ID, Name, Address
    
    with open(output_csv, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Warehouse ID", "Warehouse Name", "Destination ID", "Destination Name", "Distance (km)"])  
        
        for dest_id, dest_name, dest_address in destinations:
            dest_coords = get_coordinates(dest_address)
            if not dest_coords:
                print(f"Could not get coordinates for {dest_name}")
                continue
            
            for wh_id, wh_name, wh_address in WAREHOUSES:
                wh_coords = get_coordinates(wh_address)
                if not wh_coords:
                    print(f"Could not get coordinates for warehouse {wh_name}")
                    continue
                
                distance = calculate_distance(wh_coords, dest_coords)
                writer.writerow([wh_id, wh_name, dest_id, dest_name, distance])
    
    driver.quit()
    print(f"Distance data saved to {output_csv}")

# Example usage
process_destinations("destinations.csv", "distances.csv")
