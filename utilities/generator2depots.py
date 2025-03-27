import json
import os
import random
import sys
from datetime import datetime, timedelta

import numpy as np

from objects.request import Request

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    import sys
    sys.path.insert(0, project_root)

def gen_map(NUM_OF_NODES=34, seed=42):
    np.random.seed(seed)
    matrix = np.random.uniform(0.5, 100, (NUM_OF_NODES, NUM_OF_NODES))
    matrix = (matrix + matrix.T) / 2
    np.fill_diagonal(matrix, 0)
    matrix_list = matrix.tolist()

    data_dir = os.path.join(project_root, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    with open(os.path.join(data_dir, "distance.json"), "w", encoding="utf-8") as jsonfile:
        json.dump(matrix_list, jsonfile, ensure_ascii=False, indent=2)
    print(f"Distance matrix generated with {NUM_OF_NODES} nodes.")

def gen_list_vehicle(NUM_OF_VEHICLES, seed=42):
    metric = [9.7, 24.2, 26.7, 32, 38.2, 54]
    np.random.seed(seed)
    if NUM_OF_VEHICLES <= 3:
        xe_s = [metric[u] for u in [0]*2 + [1]*1][:NUM_OF_VEHICLES]
    elif NUM_OF_VEHICLES <= 10:
        xe_s = [metric[u] for u in [0]*3 + [1]*2 + [2]*2 + [3]*1 + [4]*1 + [5]*1][:NUM_OF_VEHICLES]
    else:
        xe_s = [metric[u] for u in [0]*0 + [1]*4 + [2]*14 + [3]*0 + [4]*3 + [5]*20][:NUM_OF_VEHICLES]

    data_dir = os.path.join(project_root, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    with open(os.path.join(data_dir, "vehicle.json"), "w") as jsonfile:
        json.dump(xe_s, jsonfile, separators=(",", ":"))
    print(f"Vehicle list generated with {NUM_OF_VEHICLES} vehicles.")

def gen_requests_and_save(num_requests=10, file_sufices="", NUM_OF_NODES=34, seed=42, depots=[0,1,2,3,4,5], split_index=17):
    """
    Sinh yêu cầu giao hàng ngẫu nhiên và lưu vào file JSON.
    Sử dụng forced_depot để đảm bảo phân bố đều giữa các depot.
    """
    random.seed(seed)
    all_requests = []
    num_depots = len(depots)
    per_depot = num_requests // num_depots
    remainder = num_requests % num_depots

    for d in depots:
        depot_reqs = []
        for i in range(per_depot * 2):
            r = Request.generate(
                NUM_OF_NODES=NUM_OF_NODES,
                start_from_depot=True,
                small_weight=True,
                depots=depots,
                forced_depot=d,
                split_index=split_index,
            )
            depot_reqs.append(r)
        # Lọc các yêu cầu theo end_place để đảm bảo tính duy nhất
        unique_reqs = {}
        for r in depot_reqs:
            ep = r.end_place[0]
            if ep not in unique_reqs:
                unique_reqs[ep] = r
        selected = list(unique_reqs.values())[:per_depot]
        all_requests.extend(selected)

    if remainder > 0:
        extra_reqs = []
        for i in range(remainder * 2):
            r = Request.generate(
                NUM_OF_NODES=NUM_OF_NODES,
                start_from_depot=True,
                small_weight=True,
                depots=depots,
                split_index=split_index,
            )
            extra_reqs.append(r)
        extra_unique = {}
        for r in extra_reqs:
            ep = r.end_place[0]
            if ep not in extra_unique:
                extra_unique[ep] = r
        extra_selected = list(extra_unique.values())[:remainder]
        all_requests.extend(extra_selected)

    random.shuffle(all_requests)

    data_dir = os.path.join(project_root, "data")
    intermediate_dir = os.path.join(data_dir, "intermediate")
    if not os.path.exists(intermediate_dir):
        os.makedirs(intermediate_dir)

    output_filename = os.path.join(intermediate_dir, f"{file_sufices}.json")
    with open(output_filename, "w", encoding="utf-8") as file:
        json.dump([r.to_dict() for r in all_requests], file, separators=(",", ": "))
    print(f"Requests generated and saved to {output_filename} with {len(all_requests)} requests.")
    return all_requests

if __name__ == "__main__":
    gen_map(NUM_OF_NODES=34, seed=42)
    gen_list_vehicle(NUM_OF_VEHICLES=5, seed=42)
    gen_requests_and_save(num_requests=10, file_sufices="0", NUM_OF_NODES=34, seed=42, depots=[0,1,2,3,4,5], split_index=17)
