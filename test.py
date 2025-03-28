import ast
import json
import os
import subprocess
from datetime import datetime
from time import perf_counter
import psutil

from utilities.split_data import postprocess_output
from objects.request import Request
from sync_staff import initialize_driver_list,initialize_driver_timetable,sample_drivers,copy_driver_data_to_timetable,driver_excel_2_csv

config = []
NUM_OF_DAY_REPETION = None
DATES = None


def run_test_bo_doi_cong_nghiep(re_run=False):
    # Kiểm tra và tạo thư mục "data", "data/output", "data/log" nếu chưa tồn tại
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("data/output"):
        os.makedirs("data/output")
    if not os.path.exists("data/log"):
        os.makedirs("data/log")

    if re_run is False:
        current_time = "2025-02-19_10-49-26"
        if not os.path.exists("data"):
            os.makedirs("data")
        stdout_filename = f"data/output/{current_time}.txt"
        config_filename = f"data/log/config_{current_time}.txt"

        return -1, -1, stdout_filename, config_filename

    tin = perf_counter()

    # Lấy thời gian hiện tại và tạo tên file
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if not os.path.exists("data"):
        os.makedirs("data")
    stdout_filename = f"data/output/{current_time}.txt"
    config_filename = f"data/log/config_{current_time}.txt"

    # Chạy process và ghi stdout + config (thay vì stderr)
    with open(stdout_filename, "wb") as stdout_file, open(
        config_filename, "wb"
    ) as config_file:
        process = subprocess.Popen(
            ["python", "test_bo_doi_cong_nghiep.py"],
            stdout=stdout_file,
            stderr=config_file,
        )

        memory_usage = 0

        while process.poll() is None:  # Kiểm tra nếu tiến trình vẫn đang chạy
            try:
                memory_info = psutil.Process(process.pid).memory_info()
                memory_usage = max(
                    memory_usage, memory_info.rss
                )  # Lưu mức sử dụng bộ nhớ cao nhất
            except psutil.NoSuchProcess:
                break  # Quá trình đã kết thúc, thoát vòng lặp

        process.wait()  # Đảm bảo tiến trình đã kết thúc hoàn toàn

    return perf_counter() - tin, memory_usage, stdout_filename, config_filename


def read_config(config_filename):
    global config
    try:
        # Đọc file config
        with open(config_filename, "r", encoding="utf-8") as file:
            config_str = file.read()
        # Chuyển đổi nội dung file sang dictionary
        config = ast.literal_eval(config_str)
        # print("Config đọc được:", config)
        print("Đọc file config thành công!{}".format(config))
        global DATES, NUM_OF_DAY_REPETION
        NUM_OF_DAY_REPETION = config["NUM_OF_DAY_REPETION"]
        DATES = config["DATES"]
        return config

    except (SyntaxError, ValueError):
        print("Lỗi: Nội dung file config không hợp lệ!")
        return None
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {config_filename}!")
        return None


def read_output(output_filename):
    import utilities.read_output as read_output

    return read_output.read_and_save_json_output(filename=output_filename)


def read_requests(config):
    requests_files = []
    for day in DATES:
        request_filename = f"data/intermediate/{day}.json"
        try:
            with open(request_filename, "r", encoding="utf-8") as file:
                # Load JSON data from file
                data = json.load(file)
                # Convert data to list of Request objects
                requests = [Request.from_dict(u) for u in data]
                requests_files.append(requests)
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file {request_filename}!")
        except Exception as e:
            print(f"Lỗi khi đọc file {request_filename}: {e}")
            exit()
    print(requests_files)
    return requests_files


def check(outputs, queries, config):
    print(outputs)
    print("Kiểm tra kết quả...")
    day_id = 0
    for output, querys in zip(outputs[1:], queries):  # zip by day
        print(f"Day {DATES[day_id]}")
        day_id += 1
        # init time frame and demand
        time_frame = [
            (0, 24 * config["TIME_SCALE"]) for _ in range(config["NUM_OF_NODES"])
        ]
        demand = [0 for _ in range(config["NUM_OF_NODES"])]
        delivered_weight = [0 for _ in range(config["NUM_OF_NODES"])]
        for query in querys[: config["NUM_OF_REQUEST_PER_DAY"]]:
            # print(f"type(query): {type(query)}")
            # print(query)
            # exit(0)
            time_frame[query.end_place[0]] = (
                query.timeframe[0] * config["TIME_SCALE"],
                query.timeframe[1] * config["TIME_SCALE"],
            )
            demand[query.end_place[0]] = int(query.weight * config["CAPACITY_SCALE"])

        output["vehicles"] = {
            vehicle_id: vehicle
            for vehicle_id, vehicle in output["vehicles"].items()
            if vehicle["distance_of_route"] > 0
        }

        for vehicle_id, vehicle in output["vehicles"].items():
            # print(f"vehicle_id: {vehicle_id}")
            precomputed_distance = vehicle["distance_of_route"]
            list_of_route = vehicle["list_of_route"]
            nodes = [route["node"] for route in list_of_route]
            arrival_time = [route["arrival_time"] for route in list_of_route]
            # capacity = [route["capacity"] for route in list_of_route]
            delivered = [route["delivered"] for route in list_of_route]
            print(precomputed_distance, nodes, delivered)
            for i, _ in enumerate(nodes[:-1]):
                if delivered[i] > 0:
                    if (
                        arrival_time[i] < time_frame[nodes[i]][0]
                        or arrival_time[i] > time_frame[nodes[i]][1]
                    ):
                        print(
                            f"Error: arrival time at node {nodes[i]} is not in time frame"
                        )
                        raise Exception(
                            f"Error: arrival time at node {nodes[i]} is not in time frame {arrival_time[i]} not in {time_frame[nodes[i]]}"
                        )
                    if delivered_weight[nodes[i]] + delivered[i] > demand[nodes[i]]:
                        print(
                            f"Error: delivered weight at node {nodes[i]} is greater than demand {delivered_weight[nodes[i]]} + {delivered[i]} > {demand[nodes[i]]}"
                        )
                        raise Exception(
                            f"Error: delivered weight at node {nodes[i]} is greater than demand {delivered_weight[nodes[i]]} + {delivered[i]} > {demand[nodes[i]]}"
                        )
                    delivered_weight[nodes[i]] += delivered[i]

        print(f"demand:           {demand}")
        print(f"delivered_weight: {delivered_weight}")
        # print(f"query len: {len(query)}")
        # print(f"num of request: {config['NUM_OF_REQUEST_PER_DAY']}")
        for i in range(config["NUM_OF_NODES"]):
            if delivered_weight[i] != demand[i]:
                print(
                    f"Error: delivered weight at node {i} is not equal to demand: real:{delivered_weight[i]} != {demand[i]}"
                )
                raise Exception(
                    f"Error: delivered weight at node {i} is not equal to demand: real:{delivered_weight[i]} != {demand[i]}"
                )
        print(f"Day {day_id} is correct")
    print("Kết quả đúng!")


if __name__ == "__main__":
    # init excel
    from config import DATES
    # from initExcel import init_excel
    # print(DATES[0])
    # init_excel(day=DATES[0], is_recreate=True)
    # init_excel(day=DATES[1], is_recreate=False)
    # init_excel(day=DATES[2], is_recreate=False)

    # điền dữ liệu vào 

    # read excel
    from read_excel import excel_to_requests_and_save
    requests = excel_to_requests_and_save(file_path="data/input/Lenh_Dieu_Xe.xlsx", sheet_name=DATES[0])
    requests = excel_to_requests_and_save(file_path="data/input/Lenh_Dieu_Xe.xlsx", sheet_name=DATES[1])
    requests = excel_to_requests_and_save(file_path="data/input/Lenh_Dieu_Xe.xlsx", sheet_name=DATES[2])
    # for day in DATES:
    #     driver_excel_2_csv(
    #         excel_file="data/input/Lenh_Dieu_Xe.xlsx",
    #         sheet_name="Tai_Xe",
    #         json_file="data/drivers.json",
    #         is_check_driver_availability=True,
    #         checkday=day,
    #     )
    # recompute map
    # process_destinations(r"data\destinations.csv", r"data\distance_matrix.csv")

    # (
    #     run_time,
    #     memory_usage,
    #     stdout_filename,
    #     config_filename,
    # ) = run_test_bo_doi_cong_nghiep(re_run=True)

    # processed_filename = processed_output_file=stdout_filename.split(".")[0] + "_processed.json"
    # # sau khi chạy
    # config_data = read_config(config_filename)
    # postprocess_output(output_file=stdout_filename, processed_output_file=processed_filename)
    # output_data = read_output(processed_filename)
    # requests_data = read_requests(config_data)

    # check(output_data, requests_data, config_data)

    # print(f"""ORTools run in {run_time:.2f}s, with config: \n{config_data}""")
    # print(f"Peak memory usage: {memory_usage / (1024 * 1024):.2f} MB")
    # print(f"Output saved to: {stdout_filename}")
    # print(f"Config saved to: {config_filename}")

    # # Kiểm tra


"""
intel i5-9300H 4 cores - 8 threads, 16GB RAM,
------------------------------------
ORTools run in 121.94s
Peak memory usage: 105.82 MB
------------------------------------
ORTools run in 111.54s
Peak memory usage: 104.83 MB
Output saved to: stdout_output_2025-02-12_10-31-06.txt, stderr_output_2025-02-12_10-31-06.txt
------------------------------------
"""
