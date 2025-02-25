import json
import random
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from utilities.load_requests import load_requests
from utilities.update_map import update_map
from utilities.split_data import split_requests  # Đảm bảo hàm này được import
from config import *  # Giả sử các hằng số như TIME_SCALE, CAPACITY_SCALE, AVG_VELOCITY, MAX_WAITING_TIME, MAX_TRAVEL_TIME, etc. đã được định nghĩa ở đây
from objects.driver import Driver
from objects.request import Request

# ---------------------------------------------------------------------------
# 1️⃣ KẾT NỐI FIREBASE ADMIN SDK
# ---------------------------------------------------------------------------
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------------------------------------------------------------------------
# 2️⃣ HÀM TẢI DỮ LIỆU TỪ FIRESTORE HOẶC FILE JSON
# ---------------------------------------------------------------------------
def load_data_from_firestore():
    """Lấy dữ liệu Requests và Drivers từ Firestore."""
    requests_ref = db.collection("Requests").stream()
    requests_data = [doc.to_dict() for doc in requests_ref]

    vehicles_ref = db.collection("Drivers").stream()
    vehicles_data = [doc.to_dict() for doc in vehicles_ref]

    return requests_data, vehicles_data

def load_data_from_files(distance_file="data/distance.json", request_file="data/requests.json", vehicle_file="data/vehicle.json"):
    """Tải dữ liệu từ các file JSON."""
    with open(distance_file, 'r', encoding='utf-8') as f:
        distance_matrix = json.load(f)

    with open(vehicle_file, 'r', encoding='utf-8') as f:
        vehicle_capacities = json.load(f)

    requests_data = load_requests(request_file)

    return distance_matrix, vehicle_capacities, requests_data

# ---------------------------------------------------------------------------
# 3️⃣ CẬP NHẬT MAP & CHUẨN BỊ DỮ LIỆU ĐẦU VÀO CHO THUẬT TOÁN
# ---------------------------------------------------------------------------
def prepare_data(requests_data, vehicles_data):
    """
    Cập nhật ma trận khoảng cách và chuẩn bị dữ liệu đầu vào cho thuật toán:
      - Chia nhỏ, ánh xạ các request qua hàm split_requests.
      - Cập nhật ma trận khoảng cách mới qua update_map.
      - Tính toán demands và time windows từ các request đã được chia nhỏ.
      - Lấy vehicle capacities từ danh sách tài xế (Drivers).
    """
    divided_mapped_requests, mapping, inverse_mapping = split_requests(requests_data)

    # Cập nhật khoảng cách giữa các điểm dựa trên mapping
    distance_matrix = update_map(divided_mapped_requests, mapping, inverse_mapping)

    n_nodes = len(distance_matrix)
    demands = [0 for _ in range(n_nodes)]
    time_windows = [(0, 24 * TIME_SCALE) for _ in range(n_nodes)]

    # Chuyển đổi thông tin từ từng request thành yêu cầu (demands, time windows)
    for req in divided_mapped_requests:
        # req được lưu dưới dạng dictionary, đảm bảo các key phù hợp: "end_place", "weight", "timeframe"
        end_place = req["end_place"][0]
        weight = req["weight"]
        demands[end_place] += int(weight * CAPACITY_SCALE)
        time_windows[end_place] = (
            req["timeframe"][0] * TIME_SCALE,
            req["timeframe"][1] * TIME_SCALE
        )

    # Lấy vehicle capacities từ trường "vehicle_load" của Drivers
    vehicle_capacities = [int(driver["vehicle_load"] * CAPACITY_SCALE) for driver in vehicles_data]

    return distance_matrix, demands, vehicle_capacities, time_windows

# ---------------------------------------------------------------------------
# 4️⃣ CHẠY THUẬT TOÁN OR-TOOLS
# ---------------------------------------------------------------------------
def solve_routing(distance_matrix, demands, vehicle_capacities, time_windows):
    """Thiết lập và chạy thuật toán tối ưu hóa lộ trình bằng OR-Tools."""
    num_vehicles = len(vehicle_capacities)
    depot = 0
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, depot)
    routing = pywrapcp.RoutingModel(manager)

    # Callback khoảng cách
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Thêm ràng buộc sức chứa
    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        return demands[node]
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,                      # slack
        vehicle_capacities,     # vehicle capacities
        True,                   # start cumul to zero
        "Capacity"
    )

    # Thêm ràng buộc thời gian: chuyển thời gian di chuyển thành số nguyên
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        # Tính thời gian đi giữa hai node (làm tròn xuống)
        return int(distance_matrix[from_node][to_node] / AVG_VELOCITY)
    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_callback_index,
        MAX_WAITING_TIME,
        MAX_TRAVEL_TIME,
        False,
        "Time"
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)
    return solution, manager, routing

# ---------------------------------------------------------------------------
# 5️⃣ LƯU KẾT QUẢ VÀO FIRESTORE
# ---------------------------------------------------------------------------
def save_results_to_firestore(solution, manager, routing):
    """Lưu kết quả tối ưu hóa (lộ trình của các xe) vào Firestore trong collection 'Routes'."""
    if not solution:
        print("❌ Không tìm thấy giải pháp!")
        return

    results = []
    for vehicle_id in range(manager.GetNumberOfVehicles()):
        index = routing.Start(vehicle_id)
        route_nodes = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route_nodes.append(node)
            index = solution.Value(routing.NextVar(index))
        results.append({"vehicle_id": vehicle_id, "route": route_nodes})

    job_id = str(datetime.utcnow().timestamp())
    db.collection("Routes").document(job_id).set({
        "job_id": job_id,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    })
    print(f"✅ Kết quả đã được lưu vào Firestore với job ID: {job_id}")

# ---------------------------------------------------------------------------
# 6️⃣ CHẠY THUẬT TOÁN TỐI ƯU LỘ TRÌNH
# ---------------------------------------------------------------------------
def run_optimization(use_firestore=False):
    """
    Chạy thuật toán tối ưu hóa lộ trình:
      - Nếu use_firestore=True, dữ liệu được tải từ Firestore (Requests và Drivers).
      - Ngược lại, dữ liệu được tải từ các file JSON.
    Sau đó, chuẩn bị dữ liệu, chạy OR-Tools và lưu kết quả vào Firestore.
    """
    if use_firestore:
        requests_data, vehicles_data = load_data_from_firestore()
    else:
        distance_matrix, vehicle_capacities, requests_data = load_data_from_files()
        # Giả lập danh sách tài xế nếu không lấy từ Firestore
        vehicles_data = [{"vehicle_load": 100} for _ in range(len(vehicle_capacities))]

    # Chuẩn bị dữ liệu đầu vào cho thuật toán
    distance_matrix, demands, vehicle_capacities, time_windows = prepare_data(requests_data, vehicles_data)

    solution, manager, routing = solve_routing(distance_matrix, demands, vehicle_capacities, time_windows)

    save_results_to_firestore(solution, manager, routing)

# ---------------------------------------------------------------------------
# 7️⃣ CHẠY KHI THỰC THI FILE
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_optimization(use_firestore=True)
