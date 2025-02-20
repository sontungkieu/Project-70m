import requests
import csv
import time

# 🔹 Replace with your actual Goong.io API key
GOONG_API_KEY = "REDACTED"

def is_plus_code(address):
    """Detects if an address is a Plus Code (contains '+', but is not a full address)."""
    return "+" in address and "," not in address  # No comma means it's likely a Plus Code

def get_coordinates(address, retry=3):
    """
    Fetches latitude and longitude using Goong.io Geocoding API.
    Converts Plus Codes into coordinates if necessary.
    """
    url = f"https://rsapi.goong.io/Geocode?address={address}&api_key={GOONG_API_KEY}"

    for attempt in range(retry):
        response = requests.get(url).json()
        
        if response["status"] == "OK":
            location = response["results"][0]["geometry"]["location"]
            return float(location["lat"]), float(location["lng"])
        
        print(f" Geocoding failed for '{address}', retrying ({attempt+1}/{retry})...")
        time.sleep(2)  # Wait before retrying

    print(f"Could not geocode address: {address}")
    return None  # Return None if geocoding fails after retries
def batch_calculate_distance(origins, destinations):
    """
    Uses Goong.io Distance Matrix API to calculate distances for multiple origins and destinations.
    Removes 'km' from the output.
    """
    origins_str = "|".join([f"{lat},{lng}" for lat, lng in origins])
    destinations_str = "|".join([f"{lat},{lng}" for lat, lng in destinations])

    url = f"https://rsapi.goong.io/DistanceMatrix"

    params = {
        "origins": origins_str,
        "destinations": destinations_str,
        "vehicle": "car",
        "api_key": GOONG_API_KEY
    }

    try:
        response = requests.get(url, params=params, verify=False).json()
    except requests.exceptions.SSLError:
        print("❌ SSL Error: Could not verify SSL connection to Goong.io.")
        return None

    # Debugging: Print API response
    print("🔍 API Response:", response)

    if "rows" not in response or not response["rows"]:
        print(f"❌ API Error: 'rows' key is missing. Check API key or request format.")
        return None

    distances = []
    for i, row in enumerate(response["rows"]):
        row_distances = []
        if "elements" not in row or not row["elements"]:
            print(f"⚠️ Missing 'elements' in row {i}")
            continue

        for j, element in enumerate(row["elements"]):
            if "status" not in element or element["status"] != "OK":
                row_distances.append("Not Found")
            else:
                # ✅ Remove "km" and convert to a number
                distance_text = element["distance"]["text"]
                numeric_distance = distance_text.replace(" km", "")  # ✅ Remove "km"
                numeric_distance = numeric_distance.replace(" m", "")  # ✅ Remove "m"
                row_distances.append(numeric_distance)

        distances.append(row_distances)

    return distances

def process_destinations(input_csv, output_csv):
    """
    Reads a CSV file with destinations, converts addresses to coordinates,
    and calculates pairwise distances using Goong.io API.
    """
    destinations = []

    # Read input CSV file
    with open(input_csv, mode="r", encoding="utf-8", errors="replace") as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header row
        for row in reader:
            dest_id, dest_name, dest_address = row[0], row[1], row[2]

            # Convert Plus Codes to coordinates if needed
            if "+" in dest_address:
                print(f"🔍 Converting Plus Code: {dest_address} → Coordinates")
                dest_coords = get_coordinates(dest_address)
            else:
                dest_coords = get_coordinates(dest_address)

            if dest_coords:
                destinations.append((dest_id, dest_name, dest_address, dest_coords))
            else:
                print(f"⚠️ Could not get coordinates for {dest_name}")

    num_destinations = len(destinations)

    # Ensure we only pass valid coordinates to the API
    valid_destinations = [d[3] for d in destinations if d[3] is not None]

    # Call Goong API for distances
    distances = batch_calculate_distance(valid_destinations, valid_destinations)

    if not distances:
        print("❌ Error: No distances received from API.")
        return  # Stop execution if no data is received

    # ✅ Debugging: Print Matrix Before Writing
    print("\n✅ Final Distance Matrix:")
    for row in distances:
        print(row)

    # ✅ Write output CSV file (Distance Matrix Format)
    try:
        with open(output_csv, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Write headers (IDs of destinations)
            writer.writerow(["ID/ID"] + [dest[0] for dest in destinations])

            # Write rows (Distance matrix values)
            for i in range(num_destinations):
                row = [destinations[i][0]] + distances[i]
                writer.writerow(row)

        print(f"✅ Distance matrix saved successfully to {output_csv}")

    except Exception as e:
        print(f"❌ Error writing to file: {e}")

  

process_destinations("destinations.csv", "distance_matrix.csv")
