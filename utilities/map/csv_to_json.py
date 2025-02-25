import csv
import json
import os

def csv_to_json(input_csv, output_json):
    data = []
    try:
        with open(input_csv, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            tmp = []
            for row in reader:
                for key,value in row.items():
                    tmp.append(value)
                data.append(tmp[1:])
            print(data)
            # exit()
        
        print(data)
        # Ensure the output folder exists
        output_folder = os.path.dirname(output_json)
        if output_folder and not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        with open(output_json, mode="w", encoding="utf-8") as jsonfile:
            json.dump(data, jsonfile, separators=(",", ":"), ensure_ascii=False)
        
        print(f"Data successfully converted from {input_csv} to {output_json}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    input_csv = os.path.join("data", "distance_matrix.csv")
    output_json = os.path.join("data", "distance.json")
    csv_to_json(input_csv, output_json)