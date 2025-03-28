import json
import random
import logging
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

import utilities.generator as generator
import utilities.load_requests as load_requests
from objects.driver import Driver
from objects.request import Request
from utilities.split_data import split_customers, split_requests
from utilities.update_map import update_map

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Đọc cấu hình từ config.json
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Gán các hằng số từ config
NUM_OF_VEHICLES = config["NUM_OF_VEHICLES"]
NUM_OF_NODES = config["NUM_OF_NODES"]
NUM_OF_REQUEST_PER_DAY = config["NUM_OF_REQUEST_PER_DAY"]
NUM_OF_DAY_REPETION = config["NUM_OF_DAY_REPETION"]
DISTANCE_SCALE = config["DISTANCE_SCALE"]
CAPACITY_SCALE = config["CAPACITY_SCALE"]
TIME_SCALE = config["TIME_SCALE"]
MAX_ROUTE_SIZE = config["MAX_ROUTE_SIZE"]
MAX_TRAVEL_DISTANCE = config["MAX_TRAVEL_DISTANCE"]
AVG_VELOCITY = config["AVG_VELOCITY"]
MAX_TRAVEL_TIME = config["MAX_TRAVEL_TIME"]
MAX_WAITING_TIME = config["MAX_WAITING_TIME"]
GLOBAL_SPAN_COST_COEFFICIENT = config["GLOBAL_SPAN_COST_COEFFICIENT"]
MU = config["MU"]
LAMBDA = config["LAMBDA"]
SEARCH_STRATEGY = config["SEARCH_STRATEGY"]
DEPOT_VEHICLE_COUNTS = config["DEPOT_VEHICLE_COUNTS"]
DATES = config["DATES"]

# Thêm THRESHOLD_KM và NU_PENALTY (mặc định nếu không có trong config)
THRESHOLD_KM = config.get("THRESHOLD_KM", 100)  # mặc định 100 km
NU_PENALTY = config.get("NU_PENALTY", 10)

# Chọn chiến lược tìm lời giải ban đầu
search_strategy = [
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
    routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
][SEARCH_STRATEGY]

def load_data(distance_file="data/distance.json", request_file="data/intermediate/{day}.json", vehicle_file="data/vehicle.json", real_mode=False, day=""):
    """Tải dữ liệu định tuyến cho một ngày."""
    with open(vehicle_file, "r", encoding="utf-8") as f:
        vehicle_capacities = [int(u * CAPACITY_SCALE) for u in json.load(f)]
    num_vehicles = len(vehicle_capacities)
    
    request_file = request_file.format(day=day)
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
    
    transit_callback_index = routing.RegisterTransitCallback(
        lambda from_idx, to_idx: data["distance_matrix"][manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]
    )
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    routing.AddDimension(transit_callback_index, 0, MAX_TRAVEL_DISTANCE, True, "Distance")
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)
    
    stops_callback_index = routing.RegisterTransitCallback(lambda from_idx, to_idx: 1)
    routing.AddDimension(stops_callback_index, 0, MAX_ROUTE_SIZE, True, "Stops")
    
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

def solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty):
    """Giải bài toán định tuyến."""
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = search_strategy
    
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
        logger.warning("Không tìm thấy lời giải với chiến lược ban đầu (%s). Thử thay thế...", search_strategy)
        # Thử chiến lược SAVINGS làm chiến lược thay thế
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.SAVINGS
        solution = routing.SolveWithParameters(search_parameters)
        if not solution:
            logger.error("Không tìm thấy lời giải với chiến lược thay thế.")
            return None, None
    
    daily_distances = []
    distance_dimension = routing.GetDimensionOrDie("Distance")
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        max_distance = 0
        while not routing.IsEnd(index):
            max_distance = max(max_distance, solution.Value(distance_dimension.CumulVar(index)))
            index = solution.Value(routing.NextVar(index))
        daily_distances.append(max_distance)
    return solution, daily_distances

def solve_daily_routing(data, historical_km, lambda_penalty, mu_penalty):
    """Giải định tuyến cho một ngày."""
    routing, manager, capacity_dimension, time_dimension = create_routing_model(data)
    solution, daily_distances = solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty)
    return solution, manager, daily_distances, routing

def print_daily_solution(data, manager, routing, solution):
    """Trả về kết quả định tuyến dưới dạng dictionary."""
    time_dimension = routing.GetDimensionOrDie("Time")
    capacity_dimension = routing.GetDimensionOrDie("Capacity")
    total_distance = 0
    vehicles = {}
    
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route_distance = 0
        list_of_route = []
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival = solution.Value(time_dimension.CumulVar(index))
            current_cap = solution.Value(capacity_dimension.CumulVar(index))
            next_index = solution.Value(routing.NextVar(index))
            delivered = 0
            if node not in data["depots"]:
                delivered = current_cap - solution.Value(capacity_dimension.CumulVar(next_index))
            list_of_route.append({"node": node, "arrival_time": arrival, "delivered": delivered})
            prev = index
            index = next_index
            route_distance += data["distance_matrix"][manager.IndexToNode(prev)][manager.IndexToNode(index)]
        
        node = manager.IndexToNode(index)
        arrival = solution.Value(time_dimension.CumulVar(index))
        list_of_route.append({"node": node, "arrival_time": arrival, "delivered": 0})
        vehicles[v] = {"list_of_route": list_of_route, "distance_of_route": route_distance}
        total_distance += route_distance
    
    return {"vehicles": vehicles, "total_distance": total_distance}

def multi_day_routing_gen_request(num_days, lambda_penalty, mu_penalty):
    """Định tuyến nhiều ngày với yêu cầu tự sinh."""
    historical_km = None
    list_of_seed = []
    results = []
    
    for day in DATES:
        logger.info("--- Day %s ---", day)
        seed = random.randint(10, 1000)
        list_of_seed.append(seed)
        generator.gen_requests_and_save(NUM_OF_REQUEST_PER_DAY, file_sufices=str(day), NUM_OF_NODES=NUM_OF_NODES, seed=seed)
        
        distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data(day=day)
        if not historical_km:
            historical_km = [0] * num_vehicles
        data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
        
        solution, manager, daily_distances, routing = solve_daily_routing(data, historical_km, lambda_penalty, mu_penalty)
        if solution:
            day_result = print_daily_solution(data, manager, routing, solution)
            results.append(day_result)
            for v in range(data["num_vehicles"]):
                historical_km[v] += daily_distances[v]
            logger.info("Updated historical km: %s", historical_km)
        else:
            results.append({"vehicles": {}, "total_distance": 0})
    
    logger.info("Seeds used: %s", list_of_seed)
    return historical_km, results

if __name__ == "__main__":
    if config["IS_TESTING"]:
        generator.gen_map(NUM_OF_NODES=NUM_OF_NODES, seed=42)
        generator.gen_list_vehicle(NUM_OF_VEHICLES=NUM_OF_VEHICLES, seed=42)
        historical_km, results = multi_day_routing_gen_request(num_days=NUM_OF_DAY_REPETION, lambda_penalty=LAMBDA, mu_penalty=MU)
        # Lưu kết quả vào file trong thư mục data/test
        import os
        from datetime import datetime
        output_dir = "data/test"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = f"{output_dir}/output_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        logger.info("Output saved to: %s", output_file)
        print(f"Output saved to: {output_file}")
    else:
        # Nếu không ở chế độ test, có thể gọi một hàm khác
        pass
    if historical_km:
        print(f"\nmax km: {max(historical_km)}, min km: {min(historical_km)}, sum km: {sum(historical_km)}")
