import ast
import json
import pandas as pd
from utilities.split_data import read_mapping
def read_output(filename):
    mapped_requests, mapping, inverse_mapping,node_id_to_request = read_mapping()
    # print(inverse_mapping)
    df = pd.read_csv("data/destinations.csv")
    try:
        with open(filename, "r", encoding="utf-8") as file:
            output = file.read()
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {filename}!")
        return None
    output = output.split("\n---")  # tách các ngày
    days = []
    json_data = {}
    for day_info in output[1:-2]:
        print("*"*20)
        day = day_info[:100].split()[1]
        print("*"*20)
        # day = day[2]# tách các xe
        day_info = day_info.split("\n")[11:]
        day_info = [s for s in day_info if s.strip()]  # loại bỏ các dòng trống
        # for u in day_info:
        #     print(u)
        json_day = []
        for i in range(0,len(day_info),3):
            vehicle_id = day_info[i] if i+3<len(day_info) else None
            string_routes = day_info[i+1] if i+3<len(day_info) else None
            string_max_distance = day_info[i+2] if i+3<len(day_info) else None
            string_total_distance = day_info[i] if i+3>=len(day_info) else None
            string_cumulative_historical_km = day_info[i+1] if i+3>=len(day_info) else None

            print(day_info[i],i, len(day_info))
            vehicle_id = int(vehicle_id.split(":")[0].split()[-1]) if vehicle_id else None
            max_distance = int(float(string_max_distance.split()[-1])) if string_max_distance else None 
            string_total_distance = int(float(string_total_distance.split()[-1])) if string_total_distance else None
            string_routes = [s.strip() for s in string_routes.split("->")] if string_routes else None
            cumulative_historical_km = ast.literal_eval(string_cumulative_historical_km.split(":")[-1]) if string_cumulative_historical_km else None
            def parse_node(s:str = 'Node 0 (Arrival Time: 0, Capacity: 0, Delivered: 0)'):
                s = s.split()
                node = s[1]
                arrival_time = int(s[4][:-1])
                capacity = int(s[6][:-1])
                delivered = int(s[8][:-1])
                request = node_id_to_request.get(str(node),None)
                # if not request:
                #     print("post_process.py:read_output:parse_node:node:",node, str(node))
                #     exit()
                node = inverse_mapping.get(node,"-1") if node!="0" else "0"
                return {
                    "node": node,
                    "destination":df["Name"].iloc[int(node)],
                    "arrival_time": arrival_time,
                    "capacity": capacity, #debug only
                    "delivered": delivered, #debug only
                    "request": request,
                }
            routes = [parse_node(s) for s in string_routes]if string_routes else None
            json_day.append( {
                "vehicle_id": vehicle_id,
                "max_distance": max_distance,
                "total_distance": string_total_distance,
                "routes": routes,
                "cumulative_historical_km": cumulative_historical_km,
            })

        json_data[day] = json_day


    print(json_data)
    return json_data


def read_output_old(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            output = file.read()
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {filename}!")
        return None
    output = output.split("\n---")  # tách các ngày
    days = []
    for day in output[1:]:
        # day = day[2]# tách các xe
        day = day.split("\n")[11:]
        day = [s for s in day if s.strip()]  # loại bỏ các dòng trống
        print(day)
        exit()
        vehicles = {}
        for vehicle in day[1:]:
            pre_name, vehicle = vehicle.split(
                ":", maxsplit=1
            )  # bỏ route for vehicle x:
            vehicle_id = int(pre_name.split(" ")[-1])  # lấy tên xe
            vehicle = vehicle.split("->")  # tách các node
            distance_of_route = -1
            list_of_route = []
            for info in vehicle:
                # chuẩn hoá info
                if isinstance(info.split("\n"), list) and len(info.split("\n")) > 1:
                    info = info.split("\n")
                    if len(info[0]) < 1:
                        info = info[1]
                    else:
                        if "D" in info[1]:
                            distance_of_route = int(info[1].split(" ")[-1])
                        info = info[0]
                # tách thông tin
                # print(f"info: {info}")
                info = info.split(" ")
                node = int(info[2])
                arrival_time = int(info[5][:-1])
                capacity = int(info[7][:-1])
                delivered = int(info[9][:-1])
                list_of_route.append(
                    {
                        "node": node,
                        "arrival_time": arrival_time,
                        "capacity": capacity,
                        "delivered": delivered,
                    }
                )

                # print(f"node: {node}")
                # print(f"arrival_time: {arrival_time}")
                # print(f"capacity: {capacity}")
                # print(f"delivered: {delivered}")

            vehicle = {
                "distance_of_route": distance_of_route,
                "list_of_route": list_of_route,
            }
            if distance_of_route > 0:
                vehicles[vehicle_id] = vehicle
            # print(max(day, key = lambda x: len(x)))
        day = {"vehicles": vehicles}
        days.append(day)
        # exit()
    return days


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


if __name__ == "__main__":
    # filename = r"data\stdout_output_2025-02-19_00-00-00.txt"
    # output = read_output(filename=filename)
    # print(output)
    # read_output(filename="data/output/2025-03-29_22-01-18.txt")
    read_and_save_json_output(filename="data/output/2025-03-29_22-01-18.txt")