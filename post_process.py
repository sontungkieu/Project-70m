import ast
import json
import pandas as pd
from utilities.split_data import read_mapping
import os
# def read_output(filename):
#     mapped_requests, mapping, inverse_mapping,node_id_to_request = read_mapping()
#     df = pd.read_csv("data/destinations.csv")
#     try:
#         with open(filename, "r", encoding="utf-8") as file:
#             output = file.read()
#     except FileNotFoundError:
#         print(f"Lỗi: Không tìm thấy file {filename}!")
#         return None
#     output = output.split("\n---")
#     print(len(output))  # tách các ngày
#     days = []
#     json_data = {}
#     for day_info in output[1:]:
#         print("*"*20)
#         day = day_info[:100].split()[1]
#         print("*"*20)
#         # day = day[2]# tách các xe
#         day_info = day_info.split("\n")[11:]
#         day_info = [s for s in day_info if s.strip()]  # loại bỏ các dòng trống
#         # for u in day_info:
#         #     print(u)
#         json_day = []
#         for i in range(0,len(day_info),3):
#             vehicle_id = day_info[i] if "Route for vehicle" in day_info[i] else None
#             string_routes = day_info[i+1] if "Node 0 (Arrival Time:" in day_info[i+1] else None
#             string_max_distance = day_info[i+2] if i+2<len(day_info) and "Distance of the route:" in day_info[i+2]  else None
#             string_total_distance = day_info[i] if "Total" in day_info[i] else None
#             string_cumulative_historical_km = day_info[i+1] if "[" in day_info[i+1] and "]" in day_info[i+1] else None

#             # print(day_info[i],i, len(day_info))
#             # print(f"string_max_distance: {string_max_distance}")
#             vehicle_id = int(vehicle_id.split(":")[0].split()[-1]) if vehicle_id else None
#             max_distance = int(float(string_max_distance.split()[-1])) if string_max_distance else None 
#             string_total_distance = int(float(string_total_distance.split()[-1])) if string_total_distance else None
#             string_routes = [s.strip() for s in string_routes.split("->")] if string_routes else None
#             cumulative_historical_km = ast.literal_eval(string_cumulative_historical_km.split(":")[-1]) if string_cumulative_historical_km else None
#             def parse_node(s:str = 'Node 0 (Arrival Time: 0, Capacity: 0, Delivered: 0)'):
#                 s = s.split()
#                 node = s[1]
#                 arrival_time = int(s[4][:-1])
#                 capacity = int(s[6][:-1])
#                 delivered = int(s[8][:-1])
#                 request = node_id_to_request.get(str(node),None)
#                 # if not request:
#                 #     print("post_process.py:read_output:parse_node:node:",node, str(node))
#                 #     exit()
#                 node = inverse_mapping.get(node,"-1") if node!="0" else "0"
#                 return {
#                     "node": node,
#                     "destination":df["Name"].iloc[int(node)],
#                     "arrival_time": arrival_time,
#                     "capacity": capacity, #debug only
#                     "delivered": delivered, #debug only
#                     "request": request,
#                 }
#             routes = [parse_node(s) for s in string_routes]if string_routes else None
#             json_day.append( {
#                 "vehicle_id": vehicle_id,
#                 "max_distance": max_distance,
#                 "total_distance": string_total_distance,
#                 "routes": routes,
#                 "cumulative_historical_km": cumulative_historical_km,
#             })

#         json_data[day] = json_day

#     return json_data
def read_output(filename):
    import re
    mapped_requests, mapping, inverse_mapping, node_id_to_request = read_mapping()
    df = pd.read_csv("data/destinations.csv")

    if not os.path.exists(filename):
        print(f"❌ Không tìm thấy file: {filename}")
        return None

    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    if not lines:
        print("❌ File đầu ra rỗng!")
        return None

    json_data = {}
    current_day = None
    current_lines = []

    for line in lines:
        if line.strip().startswith("--- Day"):
            if current_day and current_lines:
                json_data[current_day] = parse_day_lines(current_lines, df, inverse_mapping, node_id_to_request)
                current_lines = []
            # Lấy ngày từ dòng
            match = re.search(r"--- Day (\d{2}\.\d{2}\.\d{4}) ---", line.strip())
            if match:
                current_day = match.group(1)
                print(f"📅 Đang xử lý ngày: {current_day}")
        else:
            current_lines.append(line)

    # Xử lý ngày cuối cùng
    if current_day and current_lines:
        json_data[current_day] = parse_day_lines(current_lines, df, inverse_mapping, node_id_to_request)

    return json_data if json_data else None


def parse_day_lines(lines, df, inverse_mapping, node_id_to_request):
    json_day = []
    lines = [s for s in lines if s.strip()]

    for i in range(0, len(lines)):
        if not lines[i].startswith("Route for vehicle"):
            continue
        try:
            vehicle_id = int(lines[i].split(":")[0].split()[-1])
            route_line = lines[i + 1]
            max_dist_line = lines[i + 2]

            string_routes = [s.strip() for s in route_line.split("->")]
            max_distance = int(float(max_dist_line.split()[-1]))

            def parse_node(s):
                s = s.split()
                node = s[1]
                arrival_time = int(s[4][:-1])
                capacity = int(s[6][:-1])
                delivered = int(s[8][:-1])
                request = node_id_to_request.get(str(node), None)
                node = inverse_mapping.get(node, "-1") if node != "0" else "0"
                return {
                    "node": node,
                    "destination": df["Name"].iloc[int(node)],
                    "arrival_time": arrival_time,
                    "capacity": capacity,
                    "delivered": delivered,
                    "request": request,
                }

            routes = [parse_node(s) for s in string_routes]

            json_day.append({
                "vehicle_id": vehicle_id,
                "max_distance": max_distance,
                "total_distance": max_distance,
                "routes": routes,
                "cumulative_historical_km": None,
            })

        except Exception as e:
            print(f"❌ Lỗi khi phân tích dòng {i}: {e}")
            continue

    return json_day



def read_and_save_json_output(
    filename=r"data\stdout_output_2025-02-19_00-00-00.txt",
):
    output = read_output(filename=filename)
    if output is not None:
        import json
        import os

        # Ensure the 'data/test' folder exists
        test_folder = os.path.join("data", "test")
        if not os.path.exists(test_folder):
            os.makedirs(test_folder)
        with open(
            os.path.join(test_folder, "2025-02-19_00-00-00.json"),
            "w",
            encoding="utf-8",
        ) as jsonfile:
            json.dump(output, jsonfile, indent=4)
    return output

# def recalculate_accumulated

if __name__ == "__main__":
    # filename = r"data\stdout_output_2025-02-19_00-00-00.txt"
    # output = read_output(filename=filename)
    # print(output)
    # read_output(filename="data/output/2025-03-29_22-01-18.txt")
    # read_and_save_json_output(filename="data/output/2025-03-29_22-01-18.txt")
    read_output(filename = r"data\output\2025-03-30_00-52-50.txt")