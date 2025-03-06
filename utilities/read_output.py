def read_output(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            output = file.read()
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {filename}!")
        return None
    output = output.split("\n---")  # tách các ngày
    days = []
    for day in output:
        day = day.split("\nRoute")  # tách các xe
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
    print("hukgakigasehukgkhufewaeb")
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
