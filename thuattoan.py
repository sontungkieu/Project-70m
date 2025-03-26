import json
import random
import logging
import argparse
from datetime import datetime
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

import utilities.generator2depots as generator
import utilities.load_requests as load_requests
from config import *  # Import các hằng số từ config.py
from objects.driver import Driver
from objects.request import Request
from utilities.split_data import split_customers, split_requests
from utilities.update_map import update_map

# Nếu NU_PENALTY chưa được định nghĩa, ta gán mặc định:
try:
    NU_PENALTY
except NameError:
    NU_PENALTY = 1

# Thêm hằng số mới để điều chỉnh cân bằng km:
THRESHOLD_KM = 20   # Ngưỡng chênh lệch km giữa 2 đội (Team A / Team B)
ALPHA_BALANCE = 2   # Hệ số phạt chênh lệch so với trung bình
HUGE_PENALTY = 10000  # Phạt rất nặng để “vô hiệu hóa” depot/đội đang chạy quá nhiều

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


def load_data(distance_file="data/distance.json",
              request_file="data/intermediate/{TODAY}.json",
              vehicle_file="data/vehicle.json",
              real_mode=False):
    """
    Tải dữ liệu: 
      - distance_matrix
      - demands
      - vehicle_capacities
      - time_windows
    cho một ngày (đọc từ file hoặc cập nhật map nếu real_mode).
    """
    with open(vehicle_file, "r", encoding="utf-8") as f:
        vehicle_capacities = [int(u * CAPACITY_SCALE) for u in json.load(f)]
    num_vehicles = len(vehicle_capacities)

    requests_data = load_requests.load_requests(request_file)
    if real_mode:
        divided_mapped_requests, mapping, inverse_mapping = split_requests(requests_data)
        distance_matrix = update_map(divided_mapped_requests, mapping, inverse_mapping)
    else:
        with open(distance_file, "r", encoding="utf-8") as f:
            distance_matrix = [
                [int(u * DISTANCE_SCALE) for u in v] 
                for v in json.load(f)
            ]

    num_nodes = len(distance_matrix)
    demands = [0] * num_nodes
    time_windows = [(0, 24 * TIME_SCALE)] * num_nodes

    for request in requests_data:
        end_place = request.end_place[0]
        demands[end_place] += int(request.weight * CAPACITY_SCALE)
        time_windows[end_place] = (
            request.timeframe[0] * TIME_SCALE, 
            request.timeframe[1] * TIME_SCALE
        )

    logger.info("Đã tải dữ liệu: %s nodes, %s vehicles", num_nodes, num_vehicles)
    return distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles


def create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, depot_vehicle_counts):
    """
    Tạo data cho nhiều depot. Ta chia thành 2 nhóm depot:
      - team_A_depots = data['depots'][:3]
      - team_B_depots = data['depots'][3:6]
    Số xe chia ra: depot_vehicle_counts[0] xe cho Team A, còn lại cho Team B.
    """
    data = {
        "distance_matrix": distance_matrix,
        "demands": demands,
        "vehicle_capacities": vehicle_capacities,
        "num_vehicles": sum(depot_vehicle_counts),
        "depot_vehicle_counts": depot_vehicle_counts,
        "depots": depots,  # danh sách depot được lấy từ config.py
        "time_windows": time_windows
    }
    # Tách/split node theo demand quá tải nếu cần
    data, node_mapping = split_customers(data)
    logger.debug("Node mapping: %s", node_mapping)
    return data


def create_routing_model(data):
    """
    Tạo RoutingIndexManager và RoutingModel cho dữ liệu multiple depots:
      - Ta chia 2 đội (Team A / Team B), mỗi đội có num_depot_A hoặc num_depot_B xe.
      - Mỗi xe trong Team A sẽ lấy 1 depot trong team_A_depots làm start_node và end_node.
      - Tương tự cho Team B.
    """
    num_vehicles = data["num_vehicles"]
    num_depot_A = data["depot_vehicle_counts"][0]

    # Chia danh sách depots (theo config ta có 6 depot => 3 cho A, 3 cho B)
    team_A_depots = data["depots"][:3]
    team_B_depots = data["depots"][3:6]

    # Xác định start_nodes/end_nodes tương ứng từng xe
    start_nodes = []
    for v in range(num_vehicles):
        if v < num_depot_A:
            # Xe thuộc Team A
            start_nodes.append(team_A_depots[v % len(team_A_depots)])
        else:
            # Xe thuộc Team B
            idx_B = v - num_depot_A
            start_nodes.append(team_B_depots[idx_B % len(team_B_depots)])
    # Mặc định ta cho về cùng depot xuất phát
    end_nodes = start_nodes[:]

    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), 
        num_vehicles, 
        start_nodes, 
        end_nodes
    )
    routing = pywrapcp.RoutingModel(manager)

    # Callback tính khoảng cách
    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Dimension cho khoảng cách
    routing.AddDimension(
        transit_callback_index,
        0, 
        MAX_TRAVEL_DISTANCE,  
        True,  
        "Distance"
    )
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)

    # Dimension cho số điểm dừng
    stops_callback_index = routing.RegisterTransitCallback(lambda f, t: 1)
    routing.AddDimension(
        stops_callback_index,
        0,
        MAX_ROUTE_SIZE,
        True,
        "Stops"
    )

    # Dimension cho dung lượng (Capacity)
    def demand_callback(from_idx):
        node = manager.IndexToNode(from_idx)
        if node in data["depots"]:
            return 0
        return -data["demands"][node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        data["vehicle_capacities"],
        False,  # fix_start_cumul_to_zero = False
        "Capacity"
    )
    capacity_dimension = routing.GetDimensionOrDie("Capacity")
    # Ràng buộc capacity ở start/end
    for v in range(num_vehicles):
        start = routing.Start(v)
        end = routing.End(v)
        capacity_dimension.CumulVar(start).SetRange(0, data["vehicle_capacities"][v])
        capacity_dimension.CumulVar(end).SetRange(0, 0)
    for i in range(routing.Size()):
        capacity_dimension.CumulVar(i).SetRange(0, max(data["vehicle_capacities"]))

    # Dimension cho thời gian
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        velocity = AVG_VELOCITY
        service_time = 0 if from_node in data["depots"] else 1
        travel_time = data["distance_matrix"][from_node][to_node] / velocity
        return int(travel_time + service_time)

    transit_time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        transit_time_callback_index,
        MAX_WAITING_TIME,  
        MAX_TRAVEL_TIME,  
        False,             
        "Time"
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    # Gán time windows (nếu node không phải depot thì áp ràng buộc)
    for idx, window in enumerate(data["time_windows"]):
        index = manager.NodeToIndex(idx)
        time_dimension.CumulVar(index).SetRange(window[0], window[1])

    return routing, manager, capacity_dimension, time_dimension


def solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty):
    """
    Giải bài toán định tuyến nhiều depot, áp dụng cơ chế phạt (cost) để cân bằng
    km giữa hai đội (Team A / Team B).
    """
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = search_strategy

    num_depot_A = data["depot_vehicle_counts"][0]
    # historical_km[0 .. num_depot_A-1] => Team A
    # historical_km[num_depot_A .. end] => Team B
    total_km_A = sum(historical_km[:num_depot_A])
    total_km_B = sum(historical_km[num_depot_A:])

    avg_km = sum(historical_km) / len(historical_km) if historical_km else 0
    min_capacity = min(data["vehicle_capacities"])

    for v in range(data["num_vehicles"]):
        # Xe thuộc Team A hay B?
        is_team_A = (v < num_depot_A)

        # Cơ bản: ưu tiên xe có km tích lũy thấp + tải trọng thấp
        base_cost = lambda_penalty * historical_km[v] \
                    + mu_penalty * (data["vehicle_capacities"][v] - min_capacity)

        # Cộng thêm phạt cân bằng: chỉ tính nếu xe vượt quá km trung bình
        balance_penalty = ALPHA_BALANCE * max(0, historical_km[v] - avg_km)

        # Trường hợp chênh lệch tổng km 2 đội cao quá => “vô hiệu hóa” (phạt rất nặng)
        extra_cost = 0
        # Nếu Team A đang cao quá so với Team B
        if (total_km_A - total_km_B) > THRESHOLD_KM and is_team_A:
            extra_cost = HUGE_PENALTY
        # Nếu Team B đang cao quá so với Team A
        elif (total_km_B - total_km_A) > THRESHOLD_KM and not is_team_A:
            extra_cost = HUGE_PENALTY

        total_fixed_cost = base_cost + balance_penalty + extra_cost
        routing.SetFixedCostOfVehicle(int(total_fixed_cost), v)

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        logger.warning("Không tìm thấy lời giải!")
        return None, None

    # Tính quãng đường đi trong ngày cho mỗi xe
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
    """
    Tạo mô hình định tuyến cho 1 ngày và giải.
    Trả về solution + manager + quãng đường mỗi xe + routing object.
    """
    routing, manager, capacity_dimension, time_dimension = create_routing_model(data)
    solution, daily_distances = solve_routing(
        routing, manager, data, historical_km, lambda_penalty, mu_penalty
    )
    return solution, manager, daily_distances, routing


def generate_solution_output(data, manager, routing, solution):
    """
    Tạo JSON output cho lời giải định tuyến:
      - Mỗi xe có driver_id, list_of_route, distance_of_route.
      - Mỗi điểm (không phải depot) kèm order_id, delivered.
    """
    time_dimension = routing.GetDimensionOrDie("Time")
    capacity_dimension = routing.GetDimensionOrDie("Capacity")
    vehicles_output = {}

    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival = solution.Value(time_dimension.CumulVar(index))
            current_cap = solution.Value(capacity_dimension.CumulVar(index))
            next_index = solution.Value(routing.NextVar(index))
            delivered = 0
            extra = {}
            if node not in data["depots"]:
                delivered = current_cap - solution.Value(capacity_dimension.CumulVar(next_index))
                extra["order_id"] = f"order_{node}"

            route.append({
                "node": node,
                "arrival_time": arrival,
                "capacity": current_cap,
                "delivered": delivered,
                **extra
            })
            index = next_index

        # Thêm điểm cuối
        node = manager.IndexToNode(index)
        arrival = solution.Value(time_dimension.CumulVar(index))
        final_cap = solution.Value(capacity_dimension.CumulVar(index))
        route.append({
            "node": node,
            "arrival_time": arrival,
            "capacity": final_cap,
            "delivered": 0
        })

        # Lọc bớt các điểm không giao hàng
        if len(route) > 2:
            filtered_route = [route[0]]
            for r in route[1:-1]:
                if r["node"] not in data["depots"] and r.get("delivered", 0) == 0:
                    continue
                filtered_route.append(r)
            filtered_route.append(route[-1])
        else:
            filtered_route = route

        # Tính lại quãng đường
        route_distance = 0
        for i in range(len(filtered_route) - 1):
            route_distance += data["distance_matrix"][
                filtered_route[i]["node"]
            ][
                filtered_route[i+1]["node"]
            ]

        vehicles_output[f"vehicle_{v}"] = {
            "driver_id": f"driver_{v}",
            "list_of_route": filtered_route,
            "distance_of_route": route_distance
        }

    return {"vehicles": vehicles_output}


def print_daily_solution(data, manager, routing, solution):
    """In lời giải cho một ngày ra console (debug)."""
    output_data = generate_solution_output(data, manager, routing, solution)
    for vehicle, info in output_data["vehicles"].items():
        logger.info("Route for %s: %s", vehicle, info["list_of_route"])
        logger.info("Distance: %s", info["distance_of_route"])
    total_distance = sum(info["distance_of_route"] for info in output_data["vehicles"].values())
    logger.info("Total distance of all routes: %s", total_distance)


def multi_day_routing_gen_request(num_days, lambda_penalty, mu_penalty):
    """
    Định tuyến nhiều ngày. Mỗi ngày sẽ:
      - Sinh yêu cầu (generator).
      - Giải và in/kết quả.
      - Cập nhật km tích lũy (historical_km).
    """
    all_outputs = []
    all_outputs.append({"meta": "Multi-day routing output", "dates": DATES})
    historical_km = None
    list_of_seed = []

    for day in DATES:
        logger.info("--- Day %s ---", day)
        seed = random.randint(10, 1000)
        list_of_seed.append(seed)

        # Sinh yêu cầu cho ngày day (2 depot):
        generator.gen_requests_and_save(
            NUM_OF_REQUEST_PER_DAY,
            file_sufices=str(day),
            NUM_OF_NODES=NUM_OF_NODES,
            seed=seed,
            depots=depots,  # truyền list depot
            split_index=17,
        )

        (distance_matrix, demands, vehicle_capacities, time_windows,
         num_nodes, num_vehicles) = load_data(request_file=f"data/intermediate/{day}.json")

        if not historical_km:
            historical_km = [0] * num_vehicles

        data = create_data_model(
            distance_matrix, 
            demands, 
            vehicle_capacities, 
            time_windows, 
            DEPOT_VEHICLE_COUNTS
        )

        solution, manager, daily_distances, routing = solve_daily_routing(
            data, 
            historical_km, 
            lambda_penalty, 
            mu_penalty
        )
        if solution is None:
            logger.error("Không tìm được lời giải cho ngày %s.", day)
            continue

        print_daily_solution(data, manager, routing, solution)
        day_output = generate_solution_output(data, manager, routing, solution)
        day_output["date"] = day
        all_outputs.append(day_output)

        # Cập nhật historical km
        for v in range(data["num_vehicles"]):
            historical_km[v] += daily_distances[v]
        logger.info("Updated historical km: %s", historical_km)

    logger.info("Seeds used: %s", list_of_seed)
    return all_outputs, historical_km


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve routing problem and output JSON result.")
    parser.add_argument("--output", type=str, help="Path to output JSON file", required=False)
    args = parser.parse_args()

    from pathlib import Path
    Path("data/test").mkdir(parents=True, exist_ok=True)

    if IS_TESTING:
        # Sinh map và danh sách xe
        generator.gen_map(NUM_OF_NODES=NUM_OF_NODES, seed=42)
        generator.gen_list_vehicle(NUM_OF_VEHICLES=NUM_OF_VEHICLES, seed=42)

        # Chạy nhiều ngày
        all_outputs, historical_km = multi_day_routing_gen_request(
            num_days=NUM_OF_DAY_REPETION,
            lambda_penalty=LAMBDA,
            mu_penalty=MU
        )
        output_data = all_outputs
    else:
        # Trường hợp chạy 1 ngày thật (real_mode)
        TODAY = datetime.now().strftime("%Y-%m-%d")
        (distance_matrix, demands, vehicle_capacities, time_windows,
         num_nodes, num_vehicles) = load_data(request_file=f"data/intermediate/{TODAY}.json",
                                              real_mode=True)
        historical_km = [0] * num_vehicles

        data = create_data_model(
            distance_matrix,
            demands,
            vehicle_capacities,
            time_windows,
            DEPOT_VEHICLE_COUNTS
        )
        solution, manager, daily_distances, routing = solve_daily_routing(data, historical_km, LAMBDA, MU)
        if solution:
            print_daily_solution(data, manager, routing, solution)
            output_data = generate_solution_output(data, manager, routing, solution)
        else:
            logger.error("Không tìm được lời giải cho ngày này.")
            output_data = {}

    # Ghi kết quả ra file JSON
    if args.output:
        output_filename = args.output
    else:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"data/test/output_{current_time}.json"

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    logger.info("Output saved to %s", output_filename)

    import sys
    config["RUNTIME"] = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    print(config, file=sys.stderr)
