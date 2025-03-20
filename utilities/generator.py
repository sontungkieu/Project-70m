import json
import os
import random
import sys
from datetime import datetime, timedelta

import numpy as np

from objects.request import Request

# Thêm thư mục gốc của dự án (nơi chứa folder "objects") vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def gen_map(NUM_OF_NODES=30, seed=42):
    np.random.seed(seed)

    # 1. Sinh ngẫu nhiên ma trận n x n trong khoảng [0.5, 100]
    matrix = np.random.uniform(0.5, 100, (NUM_OF_NODES, NUM_OF_NODES))
    # Làm cho ma trận đối xứng
    matrix = (matrix + matrix.T) / 2
    # Đặt đường chéo bằng 0 (khoảng cách từ một nút đến chính nó)
    np.fill_diagonal(matrix, 0)

    # Chuyển về list để ghi JSON
    matrix_list = matrix.tolist()

    # Determine the absolute path of the current file (in utilities)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up one directory to get the project root
    project_root = os.path.abspath(os.path.join(current_file_dir, ".."))
    # Construct the path to the 'data' directory
    data_dir = os.path.join(project_root, "data")

    # Create the 'data' directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Write the generated matrix to 'data/distance.json'
    with open(os.path.join(data_dir, "distance.json"), "w") as jsonfile:
        json.dump(matrix_list, jsonfile)


def gen_list_vehicle(NUM_OF_VEHICLES, seed=42):
    # Given value
    metric = [9.7, 24.2, 26.7, 32, 38.2, 54]
    # Set the seed for reproducibility
    np.random.seed(seed)
    # Generate a list of n random numbers in the range [0, 5]
    if NUM_OF_VEHICLES <= 3:
        xe_s = [
            metric[u] for u in [0] * 2 + [1] * 1 + [2] * 0 + [3] * 0 + [4] * 0 + [5] * 0
        ][:NUM_OF_VEHICLES]
    elif NUM_OF_VEHICLES <= 10:
        xe_s = [
            metric[u] for u in [0] * 3 + [1] * 2 + [2] * 2 + [3] * 1 + [4] * 1 + [5] * 1
        ][:NUM_OF_VEHICLES]
    else:
        xe_s = [
            metric[u]
            for u in [0] * 0 + [1] * 4 + [2] * 14 + [3] * 0 + [4] * 3 + [5] * 20
        ][:NUM_OF_VEHICLES]

    # Determine the absolute path of the current file (in utilities)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up one directory to get the project root
    project_root = os.path.abspath(os.path.join(current_file_dir, ".."))
    # Construct the path to the 'data' directory
    data_dir = os.path.join(project_root, "data")

    # Create the 'data' directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Save the list to a JSON file using the json library
    with open(os.path.join(data_dir, "vehicle.json"), "w") as jsonfile:
        json.dump(xe_s, jsonfile, separators=(",", ":"))


def gen_requests_and_save(
    num_requests=10,
    file_sufices="",
    NUM_OF_NODES=55,
    start_from_0=True,
    seed=42,
):
    """
    Tạo một số lượng yêu cầu giao hàng ngẫu nhiên và lưu vào tệp JSON.

    Parameters:
    -----------
    num_requests : int, optional (default=10)
        - Số lượng yêu cầu giao hàng cần tạo.

    file_sufices : str, optional (default="")
        - Hậu tố được thêm vào tên tệp JSON.
        - Nếu không cung cấp, tệp sẽ có tên mặc định là "requests.json".
        - Nếu cung cấp, tệp sẽ có dạng "requests<file_sufices>.json".

    Returns:
    --------
    requests: list
        - Danh sách các yêu cầu giao hàng được tạo, mỗi yêu cầu có định dạng giống như kết quả của `gen_request()`.

    Notes:
    ------
    - Hàm này sẽ tạo một tệp JSON có tên "requests<file_sufices>.json" trong thư mục 'data/intermediate'.
    - Nếu các thư mục chưa tồn tại, sẽ thông báo và tạo các thư mục cần thiết.
    """
    random.seed(seed)

    # Giả sử Request là một class đã được định nghĩa ở nơi khác
    requests = [
        Request.generate(NUM_OF_NODES=NUM_OF_NODES, start_from_0=start_from_0)
        for i in range(num_requests * 2)
    ]
    have_request = [0 for i in range(NUM_OF_NODES)]
    filtered_requests = []
    for u in requests:
        if have_request[u.end_place[0]] == 1:
            continue
        have_request[u.end_place[0]] = 1
        filtered_requests.append(u.to_list())
    requests = filtered_requests[:num_requests]

    # Xác định thư mục hiện tại của file (giả sử file này nằm trong thư mục utilities)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    # Lấy thư mục gốc của dự án
    project_root = os.path.abspath(os.path.join(current_file_dir, ".."))
    # Đường dẫn tới thư mục 'data'
    data_dir = os.path.join(project_root, "data")

    # Kiểm tra và tạo thư mục 'data' nếu chưa tồn tại
    if not os.path.exists(data_dir):
        print(f"Thư mục '{data_dir}' không tồn tại. Đang tạo thư mục.")
        os.makedirs(data_dir)

    # Xây dựng đường dẫn tới thư mục 'data/intermediate'
    intermediate_dir = os.path.join(data_dir, "intermediate")
    if not os.path.exists(intermediate_dir):
        print(f"Thư mục '{intermediate_dir}' không tồn tại. Đang tạo thư mục.")
        os.makedirs(intermediate_dir)

    # Lưu các yêu cầu vào file JSON trong thư mục 'data/intermediate'
    file_path = os.path.join(intermediate_dir, f"requests{file_sufices}.json")
    with open(file_path, "w") as file:
        json.dump(requests, file, separators=(",", ": "))

    return requests



if __name__ == "__main__":
    gen_map()
    gen_list_vehicle(5)
    gen_requests_and_save(file_sufices="0", NUM_OF_NODES=10)
