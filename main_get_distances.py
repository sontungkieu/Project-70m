import requests
import csv

# Replace with your actual API key
API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"

# Permanent warehouse locations
WAREHOUSES = [
    ("1", "Warehouse 01", "2387+MW9 Thuan Thanh, Bac Ninh, Viet Nam"),
    ("2", "Warehouse 02", "528F+Q52, Tien Du, Bac Ninh, Viet Nam")
]

def get_coordinates(address):
    """
    Fetches latitude and longitude using Google Geocoding API.
    """
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"
    response = requests.get(url).json()
    
    if response["status"] == "OK":
        location = response["results"][0]["geometry"]["location"]
        return float(location["lat"]), float(location["lng"])
    
    return None  # Return None if geocoding fails

def batch_calculate_distance(origins, destinations, use_traffic=False):
    """
    Uses Google Distance Matrix API to calculate driving distances (car travel only).
    :param origins: List of (lat, lng) tuples for warehouse locations.
    :param destinations: List of (lat, lng) tuples for destination locations.
    :param use_traffic: If True, includes real-time traffic data.
    :return: 2D list of distances (text format like "12.3 km").
    """
    
    # Convert coordinates to API format
    origins_str = "|".join([f"{lat},{lng}" for lat, lng in origins])
    destinations_str = "|".join([f"{lat},{lng}" for lat, lng in destinations])
    
    # Google Distance Matrix API URL
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
    
    # Request parameters
    params = {
        "origins": origins_str,
        "destinations": destinations_str,
        "mode": "driving",  # Always use driving mode (car travel)
        "key": API_KEY
    }
    
    # Enable traffic-based calculations if required
    if use_traffic:
        params["departure_time"] = "now"  # Uses live traffic data

    # API request
    response = requests.get(url, params=params).json()

    # Handle API response errors
    if response["status"] != "OK":
        print(f"Error in API response: {response.get('error_message', 'Unknown error')}")
        return None

    # Extract distances
    distances = []
    for i, row in enumerate(response["rows"]):
        row_distances = []
        for j, element in enumerate(row["elements"]):
            if element["status"] == "OK":
                row_distances.append(element["distance"]["text"])  # Example: "12.3 km"
            else:
                row_distances.append("Not Found")
        distances.append(row_distances)

    return distances

def process_destinations(input_csv, output_csv, use_traffic=False):
    """
    Reads a CSV file with destinations, converts addresses to coordinates,
    and calculates driving distances to fixed warehouses using batch requests.
    """
    destinations = []

    # Read input CSV file and geocode destinations
    with open(input_csv, mode="r", encoding="utf-8", errors="replace") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            dest_id, dest_name, dest_address = row[0], row[1], row[2]
            dest_coords = get_coordinates(dest_address)
            if dest_coords:
                destinations.append((dest_id, dest_name, dest_address, dest_coords))
            else:
                print(f"Could not get coordinates for {dest_name}")

    # Geocode warehouse locations (only once)
    warehouse_coords = []
    for wh_id, wh_name, wh_address in WAREHOUSES:
        wh_coords = get_coordinates(wh_address)
        if wh_coords:
            warehouse_coords.append((wh_id, wh_name, wh_address, wh_coords))
        else:
            print(f"Could not get coordinates for warehouse {wh_name}")

    # Perform batch distance calculations (optimized for car travel)
    origin_points = [wh[3] for wh in warehouse_coords]  # Warehouse coordinates
    destination_points = [dest[3] for dest in destinations]  # Destination coordinates

    # Call batch distance function (car travel only)
    distance_matrix = batch_calculate_distance(origin_points, destination_points, use_traffic)

    # Write output CSV file
    with open(output_csv, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Warehouse ID", "Warehouse Name", "Destination ID", "Destination Name", "Distance (km)"])

        for i, (wh_id, wh_name, wh_address, wh_coords) in enumerate(warehouse_coords):
            for j, (dest_id, dest_name, dest_address, dest_coords) in enumerate(destinations):
                writer.writerow([wh_id, wh_name, dest_id, dest_name, distance_matrix[i][j]])

    print(f"Distance data saved to {output_csv}")

# Example usage (Car travel only, with traffic data)
process_destinations("destinations.csv", "distances.csv", use_traffic=True)
