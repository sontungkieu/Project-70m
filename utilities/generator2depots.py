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
    # Sinh ngẫu nhiên ma trận n x n trong khoảng [0.5, 100]
    matrix = np.random.uniform(0.5, 100, (NUM_OF_NODES, NUM_OF_NODES))
    # Làm cho ma trận đối xứng
    matrix = (matrix + matrix.T) / 2
    # Đặt đường chéo bằng 0 (khoảng cách từ một nút đến chính nó)
    np.fill_diagonal(matrix, 0)
    matrix_list = matrix.tolist()

    # Xác định đường dẫn thư mục 'data'
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_file_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Ghi ma trận vào file distance.json
    with open(os.path.join(data_dir, "distance.json"), "w") as jsonfile:
        json.dump(matrix_list, jsonfile)


def gen_list_vehicle(NUM_OF_VEHICLES, seed=42):
    metric = [9.7, 24.2, 26.7, 32, 38.2, 54]
    np.random.seed(seed)
    if NUM_OF_VEHICLES <= 3:
        xe_s = [metric[u] for u in [0] * 2 + [1] * 1][:NUM_OF_VEHICLES]
    elif NUM_OF_VEHICLES <= 10:
        xe_s = [metric[u] for u in [0] * 3 + [1] * 2 + [2] * 2 + [3] * 1 + [4] * 1 + [5] * 1][:NUM_OF_VEHICLES]
    else:
        xe_s = [metric[u] for u in [0] * 0 + [1] * 4 + [2] * 14 + [3] * 0 + [4] * 3 + [5] * 20][:NUM_OF_VEHICLES]

    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_file_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    with open(os.path.join(data_dir, "vehicle.json"), "w") as jsonfile:
        json.dump(xe_s, jsonfile, separators=(",", ":"))


def gen_requests_and_save(
    num_requests=10,
    file_sufices="",
    NUM_OF_NODES=55,
    start_from_0=True,
    seed=42,
    depots=[0, 1]
):
    """
    Tạo một số lượng yêu cầu giao hàng ngẫu nhiên và lưu vào file JSON.
    Yêu cầu có điểm kết thúc thuộc depots sẽ bị loại bỏ.

    Parameters:
      - num_requests: số lượng yêu cầu cần tạo.
      - file_sufices: hậu tố cho tên file JSON.
      - NUM_OF_NODES: số lượng nodes.
      - start_from_0: nếu True, điểm bắt đầu là [0].
      - seed: seed cho random.
      - depots: danh sách các depot (mặc định [0, 1]).

    Returns:
      - requests: danh sách các yêu cầu dưới dạng list.
    """
    random.seed(seed)
    # Tạo yêu cầu, truyền depots vào để Request.generate (đã được sửa để nhận tham số này)
    requests = [
        Request.generate(NUM_OF_NODES=NUM_OF_NODES, start_from_0=start_from_0, depots=depots)
        for i in range(num_requests * 2)
    ]
    have_request = [0 for i in range(NUM_OF_NODES)]
    filtered_requests = []
    for u in requests:
        # Loại bỏ yêu cầu có điểm kết thúc thuộc depot
        if u.end_place[0] in depots:
            continue
        if have_request[u.end_place[0]] == 1:
            continue
        have_request[u.end_place[0]] = 1
        filtered_requests.append(u.to_list())
    requests = filtered_requests[:num_requests]

    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_file_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Lưu yêu cầu vào thư mục 'data/intermediate'
    with open(os.path.join(data_dir, f"intermediate/{file_sufices}.json"), "w") as file:
        json.dump(requests, file, separators=(",", ": "))
    return requests


if __name__ == "__main__":
    # Tạo map (ma trận khoảng cách)
    gen_map()
    # Tạo danh sách xe (ví dụ 5 xe)
    gen_list_vehicle(5)
    # Tạo yêu cầu giao hàng, với 2 depot là [0, 1]
    gen_requests_and_save(file_sufices="0", NUM_OF_NODES=10, depots=[0, 1])
