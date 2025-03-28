
import sys
import json
import random
import logging
import argparse
from datetime import datetime
from pathlib import Path
import os
import pickle
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import utilities.load_requests as load_requests
from config import *  # Cấu hình: IS_TESTING, LAMBDA, MU, CAPACITY_SCALE, DISTANCE_SCALE, TIME_SCALE, AVG_VELOCITY, MAX_TRAVEL_DISTANCE, MAX_ROUTE_SIZE, MAX_WAITING_TIME, MAX_TRAVEL_TIME; SUPER_DEPOT, depots_actual
from objects.request import Request
from utilities.split_data import split_customers, split_requests
from utilities.update_map import update_map

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

search_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

def load_data_super(distance_file="data/distance.json",
                    request_file="data/intermediate/{TODAY}.json",
                    vehicle_file="data/vehicle.json",
                    real_mode=True):
    """
    Load data cho super depot approach. Giả sử file distance đã bao gồm super depot (node 0) 
    và các depot thực nằm ở các node khác (ví dụ: 1,2,3,4,5,6).
    """
    with open(distance_file, "r", encoding="utf-8") as f:
        distance_matrix = json.load(f)
    distance_matrix = [[int(u * DISTANCE_SCALE) for u in row] for row in distance_matrix]
    num_nodes = len(distance_matrix)
    
    with open(vehicle_file, "r", encoding="utf-8") as f:
        vehicle_capacities = json.load(f)
    vehicle_capacities = [int(u * CAPACITY_SCALE) for u in vehicle_capacities]
    num_vehicles = len(vehicle_capacities)
    
    requests_data = load_requests.load_requests(request_file)
    demands = [0] * num_nodes
    time_windows = [(0, 24 * TIME_SCALE) for _ in range(num_nodes)]
    for req in requests_data:
        end_place = req.end_place[0]
        demands[end_place] += int(req.weight * CAPACITY_SCALE)
        time_windows[end_place] = (req.timeframe[0] * TIME_SCALE, req.timeframe[1] * TIME_SCALE)
    
    logger.info("Super Depot: Loaded data: %d nodes, %d vehicles", num_nodes, num_vehicles)
    return distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles

def create_data_model_super(distance_matrix, demands, vehicle_capacities, time_windows):
    """
    Tạo data model cho super depot.
    Ta giả sử rằng:
      - SUPER_DEPOT là node 0 (dummy depot)
      - data["depots_actual"] chứa các depot thực (ví dụ: [1,2,3,4,5,6])
    """
    data = {
        "distance_matrix": distance_matrix,
        "demands": demands,
        "vehicle_capacities": vehicle_capacities,
        "num_vehicles": len(vehicle_capacities),
        "time_windows": time_windows,
        "super_depot": SUPER_DEPOT,   # Ví dụ SUPER_DEPOT = 0, được định nghĩa trong config.py
        "depots_actual": depots_actual  # Ví dụ: [1,2,3,4,5,6]
    }
    # Ở super depot approach, không cần gọi split_customers nếu bạn cho rằng depot không thay đổi.
    logger.info("Super Depot: Data model created with %d nodes.", len(data["demands"]))
    return data

def create_routing_model_super(data):
    """
    Xây dựng Routing Model cho super depot.
    - Tất cả xe xuất phát từ SUPER_DEPOT (ví dụ: node 0).
    - Điểm kết thúc cũng là SUPER_DEPOT.
    - Bắt buộc mỗi xe phải ghé qua ít nhất 1 depot thực bằng cách thêm disjunction cho các node thuộc depots_actual.
    """
    num_vehicles = data["num_vehicles"]
    super_depot = data["super_depot"]
    start_nodes = [super_depot] * num_vehicles
    end_nodes = [super_depot] * num_vehicles
    logger.info("Super Depot: All vehicles start from super depot %d.", super_depot)
    
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), num_vehicles, start_nodes, end_nodes)
    routing = pywrapcp.RoutingModel(manager)
    
    # Callback khoảng cách
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]
    transit_cb_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)
    
    routing.AddDimension(transit_cb_idx, 0, MAX_TRAVEL_DISTANCE, True, "Distance")
    routing.GetDimensionOrDie("Distance").SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)
    
    # Dimension "Stops"
    stops_cb_idx = routing.RegisterTransitCallback(lambda f, t: 1)
    routing.AddDimension(stops_cb_idx, 0, MAX_ROUTE_SIZE, True, "Stops")
    
    # Dimension "Capacity"
    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        # Nếu là super depot hoặc là depot thực thì không tăng tải
        return 0 if node == data["super_depot"] or node in data["depots_actual"] else -data["demands"][node]
    demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(demand_cb_idx, 0, data["vehicle_capacities"], False, "Capacity")
    cap_dim = routing.GetDimensionOrDie("Capacity")
    for v in range(num_vehicles):
        s = routing.Start(v)
        e = routing.End(v)
        cap_dim.CumulVar(s).SetRange(0, data["vehicle_capacities"][v])
        cap_dim.CumulVar(e).SetRange(0, 0)
    
    # Dimension "Time"
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        velocity = AVG_VELOCITY
        service_time = 0 if from_node == data["super_depot"] or from_node in data["depots_actual"] else 1
        travel_time = data["distance_matrix"][from_node][to_node] / velocity
        return int(travel_time + service_time)
    time_cb_idx = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(time_cb_idx, MAX_WAITING_TIME, MAX_TRAVEL_TIME, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for idx, window in enumerate(data["time_windows"]):
        time_dim.CumulVar(manager.NodeToIndex(idx)).SetRange(window[0], window[1])
    
    # Ép buộc mỗi xe phải ghé qua ít nhất 1 depot thực: sử dụng disjunction với penalty rất lớn
    for depot in data["depots_actual"]:
        depot_index = manager.NodeToIndex(depot)
        routing.AddDisjunction([depot_index], 10000000)
        logger.info("Super Depot: Added disjunction for depot %d", depot)
    
    logger.info("Super Depot: Routing model successfully created.")
    return routing, manager

def solve_super(data, historical_km, lambda_penalty, mu_penalty):
    routing, manager = create_routing_model_super(data)
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = search_strategy
    search_params.log_search = True

    dist_dim = routing.GetDimensionOrDie("Distance")
    min_capacity = min(data["vehicle_capacities"])
    avg_km = sum(historical_km)/len(historical_km) if historical_km else 0
    for v in range(data["num_vehicles"]):
        base_cost = lambda_penalty * historical_km[v] + mu_penalty * (data["vehicle_capacities"][v] - min_capacity)
        balance_penalty = ALPHA_BALANCE * max(0, historical_km[v]-avg_km)
        total_fixed_cost = base_cost + balance_penalty
        routing.SetFixedCostOfVehicle(int(total_fixed_cost), v)
        logger.info("Super Depot: Vehicle %d: historical_km=%d, fixed_cost=%d", v, historical_km[v], int(total_fixed_cost))
    
    solution = routing.SolveWithParameters(search_params)
    if not solution:
        logger.warning("Super Depot: No solution found!")
        return None, None, None, None
    
    daily_distances = []
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route_distance = 0
        while not routing.IsEnd(index):
            route_distance = max(route_distance, solution.Value(dist_dim.CumulVar(index)))
            index = solution.Value(routing.NextVar(index))
        daily_distances.append(route_distance)
        logger.info("Super Depot: Vehicle %d route distance: %d", v, route_distance)
    
    return solution, manager, daily_distances, routing

def print_solution_super(data, manager, routing, solution):
    time_dim = routing.GetDimensionOrDie("Time")
    cap_dim = routing.GetDimensionOrDie("Capacity")
    total_distance = 0
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route_str = f"Super Depot: Route for vehicle {v}:\n"
        route_distance = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival = solution.Value(time_dim.CumulVar(index))
            curr_cap = solution.Value(cap_dim.CumulVar(index))
            next_index = solution.Value(routing.NextVar(index))
            delivered = 0
            if node != data["super_depot"] and node not in data["depots_actual"]:
                delivered = curr_cap - solution.Value(cap_dim.CumulVar(next_index))
            route_str += f"  Node {node} (arrival: {arrival}, cap: {curr_cap}, delivered: {delivered}) -> "
            prev = index
            index = next_index
            route_distance += data["distance_matrix"][manager.IndexToNode(prev)][manager.IndexToNode(index)]
        node = manager.IndexToNode(index)
        arrival = solution.Value(time_dim.CumulVar(index))
        final_cap = solution.Value(cap_dim.CumulVar(index))
        route_str += f"Node {node} (arrival: {arrival}, cap: {final_cap}, delivered: 0)\n"
        route_str += f"  Distance of route: {route_distance}\n"
        total_distance += route_distance
        logger.info(route_str)
    logger.info("Super Depot: Total distance of all routes: %d", total_distance)

# -------------------------------
# Main cho Super Depot approach
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve VRP with 6 depot using Super Depot strategy.")
    parser.add_argument("--output", type=str, help="Output JSON file path", required=False)
    args = parser.parse_args()
    
    Path("data/test").mkdir(parents=True, exist_ok=True)
    TODAY = datetime.now().strftime("%Y-%m-%d")
    distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data_super(request_file=f"data/intermediate/{TODAY}.json")
    historical_km = [0] * num_vehicles
    data = create_data_model_super(distance_matrix, demands, vehicle_capacities, time_windows)
    # Lưu ý: Đảm bảo rằng file distance_matrix của bạn đã bao gồm super depot (ví dụ: node 0) 
    # và config.py có định nghĩa SUPER_DEPOT và depots_actual (ví dụ: SUPER_DEPOT = 0, depots_actual = [1,2,3,4,5,6])
    solution, manager, daily_distances, routing = solve_super(data, historical_km, LAMBDA, MU)
    if solution:
        print_solution_super(data, manager, routing, solution)
    else:
        logger.error("Super Depot: No solution found for today.")
    
    output_filename = args.output if args.output else f"data/test/super_output_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump({"message": "Super Depot solution computed; see logs for details."}, f, indent=4)
    logger.info("Super Depot: Output saved to %s", output_filename)
