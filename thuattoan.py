import json
import random
import logging
import argparse
from datetime import datetime
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

import utilities.generator as generator
import utilities.load_requests as load_requests
from config import *  # Giả sử config.py định nghĩa các hằng số cần thiết như SEARCH_STRATEGY, CAPACITY_SCALE, DISTANCE_SCALE, ...
from objects.driver import Driver
from objects.request import Request
from utilities.split_data import split_customers, split_requests
from utilities.update_map import update_map

# --- Sửa lỗi NU_PENALTY: định nghĩa giá trị mặc định cho NU_PENALTY nếu chưa có ---
try:
    NU_PENALTY
except NameError:
    NU_PENALTY = 1  # Bạn có thể điều chỉnh giá trị này cho phù hợp với bài toán của mình

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chọn chiến lược tìm lời giải ban đầu
search_strategy = [
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
    routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
][SEARCH_STRATEGY]

def load_data(distance_file="data/distance.json", request_file="data/intermediate/{TODAY}.json", vehicle_file="data/vehicle.json", real_mode=False):
    """Tải dữ liệu định tuyến cho một ngày."""
    with open(vehicle_file, "r", encoding="utf-8") as f:
        vehicle_capacities = [int(u * CAPACITY_SCALE) for u in json.load(f)]
    num_vehicles = len(vehicle_capacities)
    
    requests_data = load_requests.load_requests(request_file)
    if real_mode:
        divided_mapped_requests, mapping, inverse_mapping = split_requests(requests_data)
        distance_matrix = update_map(divided_mapped_requests, mapping, inverse_mapping)
    else:
        with open(distance_file, "r", encoding="utf-8") as f:
            distance_matrix = [[int(u * DISTANCE_SCALE) for u in v] for v in json.load(f)]
    
    num_nodes = len(distance_matrix)
    demands = [0] * num_nodes
    time_windows = [(0, 24 * TIME_SCALE)] * num_nodes
    for request in requests_data:
        end_place = request.end_place[0]
        demands[end_place] += int(request.weight * CAPACITY_SCALE)
        time_windows[end_place] = (request.timeframe[0] * TIME_SCALE, request.timeframe[1] * TIME_SCALE)
    
    logger.info("Đã tải dữ liệu: %s nodes, %s vehicles", num_nodes, num_vehicles)
    return distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles

def create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, depot_vehicle_counts):
    """Tạo mô hình dữ liệu cho định tuyến."""
    data = {
        "distance_matrix": distance_matrix,
        "demands": demands,
        "vehicle_capacities": vehicle_capacities,
        "num_vehicles": sum(depot_vehicle_counts),
        "depot_vehicle_counts": depot_vehicle_counts,
        "depots": [0, 1],
        "time_windows": time_windows
    }
    data, node_mapping = split_customers(data)
    logger.debug("Node mapping: %s", node_mapping)
    return data

def create_routing_model(data):
    """Tạo mô hình định tuyến từ dữ liệu."""
    num_vehicles = data["num_vehicles"]
    num_depot_A = data["depot_vehicle_counts"][0]
    start_nodes = [data["depots"][0] if v < num_depot_A else data["depots"][1] for v in range(num_vehicles)]
    end_nodes = start_nodes[:]
    
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), num_vehicles, start_nodes, end_nodes)
    routing = pywrapcp.RoutingModel(manager)
    
    # Callback tính khoảng cách
    transit_callback_index = routing.RegisterTransitCallback(
        lambda from_idx, to_idx: data["distance_matrix"][manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]
    )
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Thêm dimension cho khoảng cách
    routing.AddDimension(transit_callback_index, 0, MAX_TRAVEL_DISTANCE, True, "Distance")
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)
    
    # Thêm dimension cho số điểm dừng
    stops_callback_index = routing.RegisterTransitCallback(lambda from_idx, to_idx: 1)
    routing.AddDimension(stops_callback_index, 0, MAX_ROUTE_SIZE, True, "Stops")
    
    # Thêm dimension cho dung lượng
    demand_callback_index = routing.RegisterUnaryTransitCallback(
        lambda from_idx: 0 if manager.IndexToNode(from_idx) in data["depots"] else -data["demands"][manager.IndexToNode(from_idx)]
    )
    routing.AddDimensionWithVehicleCapacity(demand_callback_index, 0, data["vehicle_capacities"], False, "Capacity")
    capacity_dimension = routing.GetDimensionOrDie("Capacity")
    for v in range(num_vehicles):
        start = routing.Start(v)
        end = routing.End(v)
        capacity_dimension.CumulVar(start).SetRange(0, data["vehicle_capacities"][v])
        capacity_dimension.CumulVar(end).SetRange(0, 0)
    for i in range(routing.Size()):
        capacity_dimension.CumulVar(i).SetRange(0, max(data["vehicle_capacities"]))
    
    # Thêm dimension cho thời gian
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        velocity = AVG_VELOCITY
        service_time = 0 if from_node in data["depots"] else 1
        travel_time = data["distance_matrix"][from_node][to_node] / velocity
        return int(travel_time + service_time)
    transit_time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(transit_time_callback_index, MAX_WAITING_TIME, MAX_TRAVEL_TIME, False, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    for idx, window in enumerate(data["time_windows"]):
        index = manager.NodeToIndex(idx)
        time_dimension.CumulVar(index).SetRange(window[0], window[1])
    
    return routing, manager, capacity_dimension, time_dimension

THRESHOLD_KM = 10
def solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty):
    """Giải bài toán định tuyến."""
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = search_strategy
    
    # Tính fixed_cost cho từng xe
    num_depot_A = data["depot_vehicle_counts"][0]
    total_km_A = sum(historical_km[:num_depot_A])
    total_km_B = sum(historical_km[num_depot_A:])
    min_capacity = min(data["vehicle_capacities"])
    
    for v in range(data["num_vehicles"]):
        base_cost = lambda_penalty * historical_km[v] + mu_penalty * (data["vehicle_capacities"][v] - min_capacity)
        extra_cost = 0
        if total_km_B - total_km_A > THRESHOLD_KM:
            extra_cost = -NU_PENALTY * (total_km_B - total_km_A) if v < num_depot_A else NU_PENALTY * (total_km_B - total_km_A)
        elif total_km_A - total_km_B > THRESHOLD_KM:
            extra_cost = -NU_PENALTY * (total_km_A - total_km_B) if v >= num_depot_A else NU_PENALTY * (total_km_A - total_km_B)
        routing.SetFixedCostOfVehicle(int(base_cost + extra_cost), v)
    
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        logger.warning("Không tìm thấy lời giải!")
        return None, None
    
    daily_distances = []
    distance_dimension = routing.GetDimensionOrDie("Distance")
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route_distance = 0
        while not routing.IsEnd(index):
            route_distance = max(route_distance, solution.Value(distance_dimension.CumulVar(index)))
            index = solution.Value(routing.NextVar(index))
        daily_distances.append(route_distance)
    return solution, daily_distances

def solve_daily_routing(data, historical_km, lambda_penalty, mu_penalty):
    """Giải định tuyến cho một ngày."""
    routing, manager, capacity_dimension, time_dimension = create_routing_model(data)
    solution, daily_distances = solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty)
    return solution, manager, daily_distances, routing

def generate_solution_output(data, manager, routing, solution):
    """Tạo cấu trúc JSON cho kết quả định tuyến."""
    time_dimension = routing.GetDimensionOrDie("Time")
    capacity_dimension = routing.GetDimensionOrDie("Capacity")
    vehicles_output = {}
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route = []
        route_distance = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival = solution.Value(time_dimension.CumulVar(index))
            current_cap = solution.Value(capacity_dimension.CumulVar(index))
            next_index = solution.Value(routing.NextVar(index))
            delivered = 0
            if node not in data["depots"]:
                delivered = current_cap - solution.Value(capacity_dimension.CumulVar(next_index))
            route.append({
                "node": node,
                "arrival_time": arrival,
                "capacity": current_cap,
                "delivered": delivered
            })
            route_distance += data["distance_matrix"][node][manager.IndexToNode(next_index)]
            index = next_index
        # Thêm thông tin của node cuối cùng
        node = manager.IndexToNode(index)
        arrival = solution.Value(time_dimension.CumulVar(index))
        final_cap = solution.Value(capacity_dimension.CumulVar(index))
        route.append({
            "node": node,
            "arrival_time": arrival,
            "capacity": final_cap,
            "delivered": 0
        })
        vehicles_output[f"vehicle_{v}"] = {
            "list_of_route": route,
            "distance_of_route": route_distance
        }
    return {"vehicles": vehicles_output}

def print_daily_solution(data, manager, routing, solution):
    """In lời giải cho một ngày (in ra console)."""
    output_data = generate_solution_output(data, manager, routing, solution)
    for vehicle, info in output_data["vehicles"].items():
        logger.info("Route for %s: %s", vehicle, info["list_of_route"])
        logger.info("Distance: %s", info["distance_of_route"])
    total_distance = sum(info["distance_of_route"] for info in output_data["vehicles"].values())
    logger.info("Total distance of all routes: %s", total_distance)

def multi_day_routing_gen_request(num_days, lambda_penalty, mu_penalty):
    """Định tuyến nhiều ngày với yêu cầu tự sinh."""
    historical_km = None
    list_of_seed = []
    
    for day in DATES:
        logger.info("--- Day %s ---", day)
        seed = random.randint(10, 1000)
        list_of_seed.append(seed)
        generator.gen_requests_and_save(NUM_OF_REQUEST_PER_DAY, file_sufices=str(day), NUM_OF_NODES=NUM_OF_NODES, seed=seed)
        
        distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data(request_file=f"data/intermediate/{day}.json")
        if not historical_km:
            historical_km = [0] * num_vehicles
        data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
        
        solution, manager, daily_distances, routing = solve_daily_routing(data, historical_km, lambda_penalty, mu_penalty)
        if solution:
            print_daily_solution(data, manager, routing, solution)
            for v in range(data["num_vehicles"]):
                historical_km[v] += daily_distances[v]
            logger.info("Updated historical km: %s", historical_km)
    
    logger.info("Seeds used: %s", list_of_seed)
    return historical_km

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve routing problem and output JSON result.")
    parser.add_argument("--output", type=str, help="Path to output JSON file", required=False)
    args = parser.parse_args()
    
    # Tạo thư mục cần thiết cho output
    from pathlib import Path
    Path("data/test").mkdir(parents=True, exist_ok=True)
    
    if IS_TESTING:
        generator.gen_map(NUM_OF_NODES=NUM_OF_NODES, seed=42)
        generator.gen_list_vehicle(NUM_OF_VEHICLES=NUM_OF_VEHICLES, seed=42)
        historical_km = multi_day_routing_gen_request(num_days=NUM_OF_DAY_REPETION, lambda_penalty=LAMBDA, mu_penalty=MU)
    else:
        # Xử lý dữ liệu thực tế cho một ngày
        TODAY = datetime.now().strftime("%Y-%m-%d")
        distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data(request_file=f"data/intermediate/{TODAY}.json")
        historical_km = [0] * num_vehicles
        data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
        solution, manager, daily_distances, routing = solve_daily_routing(data, historical_km, LAMBDA, MU)
        if solution:
            print_daily_solution(data, manager, routing, solution)
    
    # Tạo output JSON từ lời giải, nếu có lời giải
    output_data = {}
    if 'solution' in locals() and solution is not None:
        output_data = generate_solution_output(data, manager, routing, solution)
    else:
        logger.error("Không có lời giải hợp lệ để xuất kết quả.")
    
    # Xác định đường dẫn file output
    if args.output:
        output_filename = args.output
    else:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"data/test/output_{current_time}.json"
    
    # Ghi kết quả vào file output
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    logger.info("Output saved to %s", output_filename)
    
    # In config (nếu cần) ra stderr
    import sys
    config["RUNTIME"] = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    print(config, file=sys.stderr)
