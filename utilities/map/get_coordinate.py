import re
import requests
import csv

def get_coordinates(location):
    search_url = f"https://www.google.com/maps/search/{location.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+),', response.text)
        if match:
            lat, lng = match.groups()
            return float(lat), float(lng)
    
    return None  

def save_to_csv(locations, filename):
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Location", "Latitude", "Longitude"])
            
            for location in locations:
                coordinates = get_coordinates(location)
                if coordinates is not None:  # Check if coordinates exist
                    writer.writerow([location, coordinates[0], coordinates[1]])
                else:
                    writer.writerow([location, "Not Found", "Not Found"])
        
        print(f"Coordinates successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to file: {e}")

