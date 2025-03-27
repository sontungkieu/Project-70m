import csv
import json
import os


def csv_to_json(input_csv, output_json):
    data = []
    try:
        with open(input_csv, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tmp = []
                for key, value in row.items():
                    try:
                        # Chuyển đổi value sang float và kiểm tra > 500
                        num_value = float(value)
                        if num_value > 500:
                            tmp.append(num_value)
                        else:
                            tmp.append(None)  # hoặc bạn có thể dùng 0 hoặc giá trị khác
                    except ValueError:
                        # Nếu không chuyển đổi được sang số, giữ nguyên giá trị
                        tmp.append(value)
                data.append(tmp[1:])  # Bỏ cột đầu tiên nếu cần
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