import json
import logging
from pathlib import Path
from subprocess import Popen
from time import perf_counter
from datetime import datetime
import subprocess
import psutil

from objects.request import Request
from utilities.read_output import read_and_save_json_output

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_bo_doi_cong_nghiep(config_data):
    """
    Chạy thuật toán qua subprocess và ghi output theo định dạng yêu cầu.
    """
    start_time = perf_counter()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Tạo các thư mục cần thiết
    for folder in ["data", "data/output", "data/log", "data/test"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    stdout_filename = f"data/output/{current_time}.txt"
    log_filename = f"data/log/log_{current_time}.txt"
    test2depot_output_file = f"data/test/output_{current_time}.json"  # File output từ thuật toán
    
    # Chạy thuật toán và ghi log
    with open(stdout_filename, "w", encoding="utf-8") as stdout_file:
        with open(log_filename, "wb") as log_file:
            process = Popen(
                ["python3", "thuattoan.py", "--output", test2depot_output_file],
                stdout=subprocess.PIPE,
                stderr=log_file
            )
            memory_usage = 0
            while process.poll() is None:
                try:
                    mem_info = psutil.Process(process.pid).memory_info()
                    memory_usage = max(memory_usage, mem_info.rss)
                except psutil.NoSuchProcess:
                    break
            process.wait()
            if process.returncode != 0:
                logger.error("Quá trình chạy thuattoan.py kết thúc với lỗi, return code: %s", process.returncode)
        
        # Đọc output từ file mà thuattoan.py ghi
        try:
            with open(test2depot_output_file, "r", encoding="utf-8") as output_file:
                output_content = output_file.read()
                stdout_file.write(output_content)
            logger.info("Đã ghi output từ %s vào %s", test2depot_output_file, stdout_filename)
        except FileNotFoundError:
            logger.error("Không tìm thấy file output: %s", test2depot_output_file)
            stdout_file.write("Error: Output file not found.\n")

    run_time = perf_counter() - start_time
    return run_time, memory_usage, stdout_filename, log_filename

def read_config():
    """
    Đọc file cấu hình từ config.json và trả về dictionary config.
    """
    config_filename = "config.json"
    try:
        with open(config_filename, "r", encoding="utf-8") as file:
            config = json.load(file)
        logger.info("Đọc file config thành công! Config: %s", config)
        
        # Kiểm tra các khóa bắt buộc
        required_keys = ["NUM_OF_DAY_REPETION", "DATES", "TIME_SCALE", "NUM_OF_NODES", "NUM_OF_REQUEST_PER_DAY", "CAPACITY_SCALE"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise KeyError(f"Thiếu các khóa cần thiết trong config: {missing_keys}")
        
        config.setdefault("depots", [0, 1])
        return config
    except json.JSONDecodeError as e:
        logger.error("Lỗi: Nội dung file config không hợp lệ - %s", e)
        return None
    except FileNotFoundError:
        logger.error("Lỗi: Không tìm thấy file %s", config_filename)
        return None

def read_output(output_filename):
    """
    Đọc kết quả output từ file và trả về dữ liệu.
    """
    try:
        data = read_and_save_json_output(filename=output_filename)
        logger.info("Đọc file output thành công: %s", output_filename)
        return data
    except Exception as e:
        logger.error("Lỗi khi đọc file output %s: %s", output_filename, e)
        return None

def read_requests(config):
    """
    Đọc các file yêu cầu và trả về danh sách đối tượng Request.
    """
    requests_files = []
    for day in config["DATES"]:
        request_filename = f"data/intermediate/{day}.json"
        if not Path(request_filename).exists():
            logger.error("Lỗi: Không tìm thấy file %s", request_filename)
            continue
        try:
            with open(request_filename, "r", encoding="utf-8") as file:
                data_list = json.load(file)
                requests = [Request.from_list(item) for item in data_list]
                requests_files.append(requests)
        except Exception as e:
            logger.error("Lỗi khi đọc file %s: %s", request_filename, e)
    if requests_files:
        logger.info("Đã đọc xong các file yêu cầu.")
    return requests_files

def check(outputs, queries, config):
    """
    Kiểm tra kết quả output so với yêu cầu.
    """
    expected_days = len(queries)
    actual_days = len(outputs) - 1  # Giả định outputs[0] là header/meta
    
    if actual_days != expected_days:
        logger.error("Độ dài outputs và queries không khớp: %d vs %d", actual_days, expected_days)
        logger.error("Dữ liệu outputs có thể không đủ cho %d ngày trong config: %s", expected_days, config["DATES"])
        logger.debug("Nội dung outputs: %s", outputs)
        return False
    
    logger.info("Output: %s", outputs)
    logger.info("Kiểm tra kết quả...")
    depots = config.get("depots", [0, 1])
    day_id = 0
    
    for output, querys in zip(outputs[1:], queries):
        logger.info("Day %s", config["DATES"][day_id])
        day_id += 1
        time_frame = [(0, 24 * config["TIME_SCALE"]) for _ in range(config["NUM_OF_NODES"])]
        demand = [0] * config["NUM_OF_NODES"]
        delivered_weight = [0] * config["NUM_OF_NODES"]
        
        for query in querys[:config["NUM_OF_REQUEST_PER_DAY"]]:
            if query.end_place[0] in depots:
                continue
            node = query.end_place[0]
            time_frame[node] = (query.timeframe[0] * config["TIME_SCALE"], query.timeframe[1] * config["TIME_SCALE"])
            demand[node] = int(query.weight * config["CAPACITY_SCALE"])
        
        output["vehicles"] = {vid: veh for vid, veh in output["vehicles"].items() if veh["distance_of_route"] > 0}
        for vehicle_id, vehicle in output["vehicles"].items():
            nodes = [route["node"] for route in vehicle["list_of_route"]]
            arrival_time = [route["arrival_time"] for route in vehicle["list_of_route"]]
            delivered = [route["delivered"] for route in vehicle["list_of_route"]]
            logger.debug("Vehicle %s: %s", vehicle_id, nodes)
            
            for i in range(len(nodes) - 1):
                if nodes[i] in depots:
                    continue
                if delivered[i] > 0:
                    if not (time_frame[nodes[i]][0] <= arrival_time[i] <= time_frame[nodes[i]][1]):
                        raise Exception(f"Error: arrival time at node {nodes[i]} not in {time_frame[nodes[i]]}")
                    if delivered_weight[nodes[i]] + delivered[i] > demand[nodes[i]]:
                        raise Exception(f"Error: delivered weight at node {nodes[i]} exceeds demand")
                    delivered_weight[nodes[i]] += delivered[i]
        
        logger.debug("Demand: %s", demand)
        logger.debug("Delivered weight: %s", delivered_weight)
        for i in range(config["NUM_OF_NODES"]):
            if i in depots:
                continue
            if delivered_weight[i] != demand[i]:
                raise Exception(f"Error: delivered weight at node {i} ({delivered_weight[i]}) != demand ({demand[i]})")
        logger.info("Day %s is correct", day_id)
    logger.info("Kết quả đúng!")
    return True

if __name__ == "__main__":
    config_data = read_config()
    if config_data:
        run_time, memory_usage, stdout_filename, log_filename = run_test_bo_doi_cong_nghiep(config_data)
        output_data = read_output(stdout_filename)
        requests_data = read_requests(config_data)
        if output_data and requests_data:
            is_valid = check(output_data, requests_data, config_data)
            if is_valid:
                logger.info("ORTools run in %.2f s, with config: %s", run_time, config_data)
                logger.info("Peak memory usage: %.2f MB", memory_usage / (1024 * 1024))
            logger.info("Output saved to: %s", stdout_filename)
            logger.info("Log saved to: %s", log_filename)
        else:
            logger.error("Không thể đọc output hoặc requests.")
    else:
        logger.error("Không thể đọc config.")
