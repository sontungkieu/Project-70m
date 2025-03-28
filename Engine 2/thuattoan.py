# # # import json
# # # import random
# # # import logging
# # # import argparse
# # # from datetime import datetime
# # # from ortools.constraint_solver import pywrapcp, routing_enums_pb2
# # # import utilities.generator2depots as generator
# # # import utilities.load_requests as load_requests
# # # from config import *  # Import các hằng số từ config.py
# # # from objects.driver import Driver
# # # from objects.request import Request
# # # from utilities.split_data import split_customers, split_requests
# # # from utilities.update_map import update_map

# # # try:
# # #     NU_PENALTY
# # # except NameError:
# # #     NU_PENALTY = 1

# # # THRESHOLD_KM = 20   # Ngưỡng chênh lệch km giữa 2 depot (20 km)
# # # ALPHA_BALANCE = 2   # Hệ số phạt cho chênh lệch so với trung bình
# # # HUGE_PENALTY = 10000  # Phạt rất nặng để "vô hiệu hóa" các xe của depot chạy quá nhiều

# # # logging.basicConfig(level=logging.INFO)
# # # logger = logging.getLogger(__name__)

# # # search_strategy = [
# # #     routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
# # #     routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
# # #     routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
# # #     routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
# # # ][SEARCH_STRATEGY]

# # # def load_data(distance_file="data/distance.json",
# # #               request_file="data/intermediate/{TODAY}.json",
# # #               vehicle_file="data/vehicle.json",
# # #               real_mode=False):
# # #     with open(vehicle_file, "r", encoding="utf-8") as f:
# # #         vehicle_capacities = [int(u * CAPACITY_SCALE) for u in json.load(f)]
# # #     num_vehicles = len(vehicle_capacities)

# # #     requests_data = load_requests.load_requests(request_file)
# # #     if real_mode:
# # #         divided_mapped_requests, mapping, inverse_mapping = split_requests(requests_data)
# # #         distance_matrix = update_map(divided_mapped_requests, mapping, inverse_mapping)
# # #     else:
# # #         with open(distance_file, "r", encoding="utf-8") as f:
# # #             distance_matrix = [[int(u * DISTANCE_SCALE) for u in v] for v in json.load(f)]

# # #     num_nodes = len(distance_matrix)
# # #     demands = [0] * num_nodes
# # #     time_windows = [(0, 24 * TIME_SCALE)] * num_nodes
# # #     for request in requests_data:
# # #         end_place = request.end_place[0]
# # #         demands[end_place] += int(request.weight * CAPACITY_SCALE)
# # #         time_windows[end_place] = (request.timeframe[0] * TIME_SCALE, request.timeframe[1] * TIME_SCALE)

# # #     logger.info("Đã tải dữ liệu: %s nodes, %s vehicles", num_nodes, num_vehicles)
# # #     return distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles

# # # def create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, depot_vehicle_counts):
# # #     data = {
# # #         "distance_matrix": distance_matrix,
# # #         "demands": demands,
# # #         "vehicle_capacities": vehicle_capacities,
# # #         "num_vehicles": sum(depot_vehicle_counts),
# # #         "depot_vehicle_counts": depot_vehicle_counts,
# # #         "depots": depots,  # Sử dụng danh sách depot từ config.py
# # #         "time_windows": time_windows
# # #     }
# # #     data, node_mapping = split_customers(data)
# # #     logger.debug("Node mapping: %s", node_mapping)
# # #     return data

# # # def create_routing_model(data):
# # #     num_vehicles = data["num_vehicles"]
# # #     num_depot_A = data["depot_vehicle_counts"][0]
# # #     team_A_depots = data["depots"][:3]  # depots 0,1,2 cho team A
# # #     team_B_depots = data["depots"][3:6]  # depots 3,4,5 cho team B

# # #     start_nodes = []
# # #     for v in range(num_vehicles):
# # #         if v < num_depot_A:
# # #             start_nodes.append(team_A_depots[v % len(team_A_depots)])
# # #         else:
# # #             start_nodes.append(team_B_depots[(v - num_depot_A) % len(team_B_depots)])
# # #     end_nodes = start_nodes[:]

# # #     manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), num_vehicles, start_nodes, end_nodes)
# # #     routing = pywrapcp.RoutingModel(manager)

# # #     transit_callback_index = routing.RegisterTransitCallback(
# # #         lambda from_idx, to_idx: data["distance_matrix"][manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]
# # #     )
# # #     routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# # #     routing.AddDimension(transit_callback_index, 0, MAX_TRAVEL_DISTANCE, True, "Distance")
# # #     distance_dimension = routing.GetDimensionOrDie("Distance")
# # #     distance_dimension.SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)

# # #     stops_callback_index = routing.RegisterTransitCallback(lambda from_idx, to_idx: 1)
# # #     routing.AddDimension(stops_callback_index, 0, MAX_ROUTE_SIZE, True, "Stops")

# # #     demand_callback_index = routing.RegisterUnaryTransitCallback(
# # #         lambda from_idx: 0 if manager.IndexToNode(from_idx) in data["depots"]
# # #         else -data["demands"][manager.IndexToNode(from_idx)]
# # #     )
# # #     routing.AddDimensionWithVehicleCapacity(demand_callback_index, 0, data["vehicle_capacities"], False, "Capacity")
# # #     capacity_dimension = routing.GetDimensionOrDie("Capacity")
# # #     for v in range(num_vehicles):
# # #         start = routing.Start(v)
# # #         end = routing.End(v)
# # #         capacity_dimension.CumulVar(start).SetRange(0, data["vehicle_capacities"][v])
# # #         capacity_dimension.CumulVar(end).SetRange(0, 0)
# # #     for i in range(routing.Size()):
# # #         capacity_dimension.CumulVar(i).SetRange(0, max(data["vehicle_capacities"]))

# # #     def time_callback(from_index, to_index):
# # #         from_node = manager.IndexToNode(from_index)
# # #         to_node = manager.IndexToNode(to_index)
# # #         velocity = AVG_VELOCITY
# # #         service_time = 0 if from_node in data["depots"] else 1
# # #         travel_time = data["distance_matrix"][from_node][to_node] / velocity
# # #         return int(travel_time + service_time)

# # #     transit_time_callback_index = routing.RegisterTransitCallback(time_callback)
# # #     routing.AddDimension(transit_time_callback_index, MAX_WAITING_TIME, MAX_TRAVEL_TIME, False, "Time")
# # #     time_dimension = routing.GetDimensionOrDie("Time")
# # #     for idx, window in enumerate(data["time_windows"]):
# # #         index = manager.NodeToIndex(idx)
# # #         time_dimension.CumulVar(index).SetRange(window[0], window[1])

# # #     return routing, manager, capacity_dimension, time_dimension

# # # def solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty):
# # #     search_parameters = pywrapcp.DefaultRoutingSearchParameters()
# # #     search_parameters.first_solution_strategy = search_strategy

# # #     num_depot_A = data["depot_vehicle_counts"][0]
# # #     total_km_A = sum(historical_km[:num_depot_A])
# # #     total_km_B = sum(historical_km[num_depot_A:])
# # #     avg_km = sum(historical_km) / len(historical_km)
# # #     min_capacity = min(data["vehicle_capacities"])

# # #     for v in range(data["num_vehicles"]):
# # #         depot_v = data["depots"][0] if v < num_depot_A else data["depots"][1]
# # #         base_cost = lambda_penalty * historical_km[v] + mu_penalty * (data["vehicle_capacities"][v] - min_capacity)
# # #         balance_penalty = ALPHA_BALANCE * max(0, historical_km[v] - avg_km)
# # #         extra_cost = 0
# # #         if total_km_A - total_km_B > THRESHOLD_KM:
# # #             if v < num_depot_A:
# # #                 extra_cost = HUGE_PENALTY
# # #         elif total_km_B - total_km_A > THRESHOLD_KM:
# # #             if v >= num_depot_A:
# # #                 extra_cost = HUGE_PENALTY

# # #         total_fixed_cost = base_cost + balance_penalty + extra_cost
# # #         routing.SetFixedCostOfVehicle(int(total_fixed_cost), v)

# # #     solution = routing.SolveWithParameters(search_parameters)
# # #     if not solution:
# # #         logger.warning("Không tìm thấy lời giải!")
# # #         return None, None

# # #     daily_distances = []
# # #     distance_dimension = routing.GetDimensionOrDie("Distance")
# # #     for v in range(data["num_vehicles"]):
# # #         index = routing.Start(v)
# # #         route_distance = 0
# # #         while not routing.IsEnd(index):
# # #             route_distance = max(route_distance, solution.Value(distance_dimension.CumulVar(index)))
# # #             index = solution.Value(routing.NextVar(index))
# # #         daily_distances.append(route_distance)
# # #     return solution, daily_distances

# # # def solve_daily_routing(data, historical_km, lambda_penalty, mu_penalty):
# # #     routing, manager, capacity_dimension, time_dimension = create_routing_model(data)
# # #     solution, daily_distances = solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty)
# # #     return solution, manager, daily_distances, routing

# # # def generate_solution_output(data, manager, routing, solution):
# # #     time_dimension = routing.GetDimensionOrDie("Time")
# # #     capacity_dimension = routing.GetDimensionOrDie("Capacity")
# # #     vehicles_output = {}
# # #     for v in range(data["num_vehicles"]):
# # #         index = routing.Start(v)
# # #         route = []
# # #         route_distance = 0
# # #         while not routing.IsEnd(index):
# # #             node = manager.IndexToNode(index)
# # #             arrival = solution.Value(time_dimension.CumulVar(index))
# # #             current_cap = solution.Value(capacity_dimension.CumulVar(index))
# # #             next_index = solution.Value(routing.NextVar(index))
# # #             delivered = 0
# # #             if node not in data["depots"]:
# # #                 delivered = current_cap - solution.Value(capacity_dimension.CumulVar(next_index))
# # #             route.append({
# # #                 "node": node,
# # #                 "arrival_time": arrival,
# # #                 "capacity": current_cap,
# # #                 "delivered": delivered
# # #             })
# # #             route_distance += data["distance_matrix"][node][manager.IndexToNode(next_index)]
# # #             index = next_index
# # #         node = manager.IndexToNode(index)
# # #         arrival = solution.Value(time_dimension.CumulVar(index))
# # #         final_cap = solution.Value(capacity_dimension.CumulVar(index))
# # #         route.append({
# # #             "node": node,
# # #             "arrival_time": arrival,
# # #             "capacity": final_cap,
# # #             "delivered": 0
# # #         })
# # #         vehicles_output[f"vehicle_{v}"] = {
# # #             "list_of_route": route,
# # #             "distance_of_route": route_distance
# # #         }
# # #     return {"vehicles": vehicles_output}

# # # def print_daily_solution(data, manager, routing, solution):
# # #     output_data = generate_solution_output(data, manager, routing, solution)
# # #     for vehicle, info in output_data["vehicles"].items():
# # #         logger.info("Route for %s: %s", vehicle, info["list_of_route"])
# # #         logger.info("Distance: %s", info["distance_of_route"])
# # #     total_distance = sum(info["distance_of_route"] for info in output_data["vehicles"].values())
# # #     logger.info("Total distance of all routes: %s", total_distance)

# # # def multi_day_routing_gen_request(num_days, lambda_penalty, mu_penalty):
# # #     all_outputs = []
# # #     all_outputs.append({"meta": "Multi-day routing output", "dates": DATES})
# # #     historical_km = None
# # #     list_of_seed = []

# # #     for day in DATES:
# # #         logger.info("--- Day %s ---", day)
# # #         seed = random.randint(10, 1000)
# # #         list_of_seed.append(seed)
# # #         generator.gen_requests_and_save(
# # #             NUM_OF_REQUEST_PER_DAY,
# # #             file_sufices=str(day),
# # #             NUM_OF_NODES=NUM_OF_NODES,
# # #             seed=seed,
# # #             depots=depots,  # Sử dụng danh sách depot mới [0,1,2,3,4,5]
# # #             split_index=17,
# # #         )

# # #         (distance_matrix, demands, vehicle_capacities, time_windows,
# # #          num_nodes, num_vehicles) = load_data(request_file=f"data/intermediate/{day}.json")
# # #         if not historical_km:
# # #             historical_km = [0] * num_vehicles
# # #         data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)

# # #         solution, manager, daily_distances, routing = solve_daily_routing(data, historical_km, lambda_penalty, mu_penalty)
# # #         if solution is None:
# # #             logger.error("Không tìm được lời giải cho ngày %s.", day)
# # #             continue
# # #         print_daily_solution(data, manager, routing, solution)
# # #         day_output = generate_solution_output(data, manager, routing, solution)
# # #         day_output["date"] = day
# # #         all_outputs.append(day_output)
# # #         for v in range(data["num_vehicles"]):
# # #             historical_km[v] += daily_distances[v]
# # #         logger.info("Updated historical km: %s", historical_km)

# # #     logger.info("Seeds used: %s", list_of_seed)
# # #     return all_outputs, historical_km

# # # if __name__ == "__main__":
# # #     parser = argparse.ArgumentParser(description="Solve routing problem and output JSON result.")
# # #     parser.add_argument("--output", type=str, help="Path to output JSON file", required=False)
# # #     args = parser.parse_args()

# # #     from pathlib import Path
# # #     Path("data/test").mkdir(parents=True, exist_ok=True)

# # #     if IS_TESTING:
# # #         generator.gen_map(NUM_OF_NODES=NUM_OF_NODES, seed=42)
# # #         generator.gen_list_vehicle(NUM_OF_VEHICLES=NUM_OF_VEHICLES, seed=42)
# # #         all_outputs, historical_km = multi_day_routing_gen_request(num_days=NUM_OF_DAY_REPETION,
# # #                                                                      lambda_penalty=LAMBDA,
# # #                                                                      mu_penalty=MU)
# # #         output_data = all_outputs
# # #     else:
# # #         TODAY = datetime.now().strftime("%Y-%m-%d")
# # #         (distance_matrix, demands, vehicle_capacities, time_windows,
# # #          num_nodes, num_vehicles) = load_data(request_file=f"data/intermediate/{TODAY}.json")
# # #         historical_km = [0] * num_vehicles
# # #         data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
# # #         solution, manager, daily_distances, routing = solve_daily_routing(data, historical_km, LAMBDA, MU)
# # #         if solution:
# # #             print_daily_solution(data, manager, routing, solution)
# # #             output_data = generate_solution_output(data, manager, routing, solution)
# # #         else:
# # #             logger.error("Không tìm được lời giải cho ngày này.")

# # #     if args.output:
# # #         output_filename = args.output
# # #     else:
# # #         current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# # #         output_filename = f"data/test/output_{current_time}.json"

# # #     with open(output_filename, "w", encoding="utf-8") as f:
# # #         json.dump(output_data, f, ensure_ascii=False, indent=4)
# # #     logger.info("Output saved to %s", output_filename)

# # #     import sys
# # #     config["RUNTIME"] = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
# # #     print(config, file=sys.stderr)
# # # import json
# # # import random
# # # import logging
# # # import argparse
# # # from datetime import datetime
# # # from pathlib import Path

# # # from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# # # import utilities.load_requests as load_requests
# # # from config import *  # Chứa IS_TESTING, LAMBDA, MU, ...
# # # from objects.request import Request
# # # from utilities.split_data import split_customers, split_requests
# # # from utilities.update_map import update_map

# # # logging.basicConfig(level=logging.INFO)
# # # logger = logging.getLogger(__name__)

# # # # Các hằng số cho 6 depot balancing
# # # THRESHOLD_KM = 20
# # # ALPHA_BALANCE = 2
# # # HUGE_PENALTY = 10000

# # # search_strategy = [
# # #     routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
# # #     routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
# # #     routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
# # #     routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
# # # ][SEARCH_STRATEGY]


# # # def load_data(distance_file="data/distance.json",
# # #               request_file="data/intermediate/19022025.json",
# # #               vehicle_file="data/vehicle.json",
# # #               real_mode=True):
# # #     """
# # #     Đọc file vehicle.json => vehicle_capacities
# # #     Đọc file request => requests_data (dạng [Request, [start], [end], weight, ...])
# # #     Nếu real_mode=True => gọi update_map(...) để tính distance_matrix thực
# # #     Nếu requests_data rỗng => trả về ([], [], vehicle_capacities, [], 0, len(vehicle_capacities)) để skip
# # #     """

# # #     # 1. Đọc dung tích xe
# # #     with open(vehicle_file, "r", encoding="utf-8") as vf:
# # #         vehicle_capacities = [int(u * CAPACITY_SCALE) for u in json.load(vf)]
# # #     num_vehicles = len(vehicle_capacities)

# # #     # 2. Đọc request
# # #     requests_data = load_requests.load_requests(request_file)
# # #     if not requests_data:
# # #         logger.warning(f"⚠️ Không có request trong file {request_file}. Trả về ma trận rỗng.")
# # #         return [], [], vehicle_capacities, [], 0, num_vehicles

# # #     # 3. Tùy chế độ real_mode => update_map / distance_file
# # #     if real_mode:
# # #         divided_mapped_requests, mapping, inverse_mapping = split_requests(requests_data)
# # #         if not divided_mapped_requests:
# # #             logger.warning(f"⚠️ Sau khi split_requests, vẫn không có request => rỗng. File: {request_file}")
# # #             return [], [], vehicle_capacities, [], 0, num_vehicles
# # #         distance_matrix = update_map(divided_mapped_requests, mapping, inverse_mapping)
# # #     else:
# # #         with open(distance_file, "r", encoding="utf-8") as df:
# # #             dm = json.load(df)
# # #             distance_matrix = [[int(u * DISTANCE_SCALE) for u in row] for row in dm]

# # #     # Kiểm tra distance_matrix
# # #     if not distance_matrix:
# # #         logger.warning(f"⚠️ distance_matrix rỗng => skip. File: {request_file}")
# # #         return [], [], vehicle_capacities, [], 0, num_vehicles

# # #     num_nodes = len(distance_matrix)
# # #     if any(len(row) != num_nodes for row in distance_matrix):
# # #         logger.warning(f"⚠️ Ma trận không vuông => skip. File: {request_file}")
# # #         return [], [], vehicle_capacities, [], 0, num_vehicles

# # #     # 4. Tạo demands & time_windows
# # #     demands = [0] * num_nodes
# # #     time_windows = [(0, 24 * TIME_SCALE)] * num_nodes
# # #     for req in requests_data:
# # #         # req.start_place, req.end_place, req.weight, req.timeframe...
# # #         # end_place = req.end_place[0]
# # #         end_place = req.end_place[0]
# # #         # Bảo vệ end_place phải < num_nodes
# # #         if end_place < 0 or end_place >= num_nodes:
# # #             logger.warning(f"⚠️ end_place {end_place} vượt bounds [0..{num_nodes-1}] => bỏ qua.")
# # #             continue
# # #         demands[end_place] += int(req.weight * CAPACITY_SCALE)
# # #         tw = (req.timeframe[0] * TIME_SCALE, req.timeframe[1] * TIME_SCALE)
# # #         time_windows[end_place] = tw

# # #     logger.info(f"Loaded data: {num_nodes} nodes, {num_vehicles} vehicles from {request_file}")
# # #     return distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles


# # # def create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, depot_vehicle_counts):
# # #     """
# # #     Tạo data cho OR-Tools:
# # #       - distance_matrix
# # #       - demands
# # #       - vehicle_capacities
# # #       - num_vehicles = sum(depot_vehicle_counts)
# # #       - depots
# # #       - time_windows
# # #     Rồi split_customers (nếu demand[node] > min_capacity).
# # #     """
# # #     data = {
# # #         "distance_matrix": distance_matrix,
# # #         "demands": demands,
# # #         "vehicle_capacities": vehicle_capacities,
# # #         "num_vehicles": sum(depot_vehicle_counts),
# # #         "depot_vehicle_counts": depot_vehicle_counts,
# # #         "depots": depots,  # config.py
# # #         "time_windows": time_windows
# # #     }
# # #     # Tách node nếu demand lớn hơn min_capacity
# # #     data, node_mapping = split_customers(data)
# # #     return data


# # # def create_routing_model(data):
# # #     """
# # #     Tạo RoutingIndexManager & RoutingModel cho 6-depot:
# # #     - team A: depots[0..2]
# # #     - team B: depots[3..5]
# # #     - Số xe = sum(depot_vehicle_counts).
# # #     """
# # #     num_vehicles = data["num_vehicles"]
# # #     num_depot_A = data["depot_vehicle_counts"][0]
# # #     team_A_depots = data["depots"][:3]
# # #     team_B_depots = data["depots"][3:6]

# # #     start_nodes = []
# # #     for v in range(num_vehicles):
# # #         if v < num_depot_A:
# # #             start_nodes.append(team_A_depots[v % len(team_A_depots)])
# # #         else:
# # #             start_nodes.append(team_B_depots[(v - num_depot_A) % len(team_B_depots)])
# # #     end_nodes = start_nodes[:]

# # #     manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), num_vehicles, start_nodes, end_nodes)
# # #     routing = pywrapcp.RoutingModel(manager)

# # #     # distance callback
# # #     def distance_callback(from_idx, to_idx):
# # #         return data["distance_matrix"][manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]

# # #     dist_cb_idx = routing.RegisterTransitCallback(distance_callback)
# # #     routing.SetArcCostEvaluatorOfAllVehicles(dist_cb_idx)

# # #     # Dimension for Distance
# # #     routing.AddDimension(dist_cb_idx, 0, MAX_TRAVEL_DISTANCE, True, "Distance")
# # #     routing.GetDimensionOrDie("Distance").SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)

# # #     # Dimension for max stops
# # #     stops_cb_idx = routing.RegisterTransitCallback(lambda f, t: 1)
# # #     routing.AddDimension(stops_cb_idx, 0, MAX_ROUTE_SIZE, True, "Stops")

# # #     # demand callback
# # #     def demand_callback(from_index):
# # #         node = manager.IndexToNode(from_index)
# # #         if node in data["depots"]:
# # #             return 0
# # #         return -data["demands"][node]

# # #     demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_callback)
# # #     routing.AddDimensionWithVehicleCapacity(demand_cb_idx, 0, data["vehicle_capacities"], False, "Capacity")
# # #     cap_dim = routing.GetDimensionOrDie("Capacity")
# # #     for v in range(num_vehicles):
# # #         s = routing.Start(v)
# # #         e = routing.End(v)
# # #         cap_dim.CumulVar(s).SetRange(0, data["vehicle_capacities"][v])
# # #         cap_dim.CumulVar(e).SetRange(0, 0)

# # #     # time callback
# # #     def time_callback(from_index, to_index):
# # #         from_node = manager.IndexToNode(from_index)
# # #         to_node = manager.IndexToNode(to_index)
# # #         velocity = AVG_VELOCITY
# # #         service_time = 0 if from_node in data["depots"] else 1
# # #         travel_time = data["distance_matrix"][from_node][to_node] / velocity
# # #         return int(travel_time + service_time)

# # #     time_cb_idx = routing.RegisterTransitCallback(time_callback)
# # #     routing.AddDimension(time_cb_idx, MAX_WAITING_TIME, MAX_TRAVEL_TIME, False, "Time")
# # #     time_dim = routing.GetDimensionOrDie("Time")
# # #     for idx, window in enumerate(data["time_windows"]):
# # #         time_dim.CumulVar(manager.NodeToIndex(idx)).SetRange(window[0], window[1])

# # #     return routing, manager


# # # def solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty):
# # #     """
# # #     Thiết lập fixed_cost cho từng xe dựa trên historical_km.
# # #     Giải model => trả về solution, daily_distances
# # #     """
# # #     search_params = pywrapcp.DefaultRoutingSearchParameters()
# # #     search_params.first_solution_strategy = search_strategy

# # #     dist_dim = routing.GetDimensionOrDie("Distance")
# # #     num_depot_A = data["depot_vehicle_counts"][0]
# # #     avg_km = sum(historical_km) / len(historical_km) if historical_km else 0
# # #     min_capacity = min(data["vehicle_capacities"])

# # #     for v in range(data["num_vehicles"]):
# # #         base_cost = lambda_penalty * historical_km[v] + mu_penalty * (data["vehicle_capacities"][v] - min_capacity)
# # #         balance_penalty = ALPHA_BALANCE * max(0, historical_km[v] - avg_km)
# # #         extra_cost = 0

# # #         # team A / B
# # #         if v < num_depot_A:
# # #             total_km_A = sum(historical_km[:num_depot_A])
# # #             total_km_B = sum(historical_km[num_depot_A:])
# # #             if total_km_A > total_km_B + THRESHOLD_KM:
# # #                 extra_cost = HUGE_PENALTY
# # #         else:
# # #             total_km_A = sum(historical_km[:num_depot_A])
# # #             total_km_B = sum(historical_km[num_depot_A:])
# # #             if total_km_B > total_km_A + THRESHOLD_KM:
# # #                 extra_cost = HUGE_PENALTY

# # #         total_fixed_cost = base_cost + balance_penalty + extra_cost
# # #         routing.SetFixedCostOfVehicle(int(total_fixed_cost), v)

# # #     solution = routing.SolveWithParameters(search_params)
# # #     if not solution:
# # #         logger.warning("No solution found!")
# # #         return None, None

# # #     daily_distances = []
# # #     for v in range(data["num_vehicles"]):
# # #         index = routing.Start(v)
# # #         route_distance = 0
# # #         while not routing.IsEnd(index):
# # #             route_distance = max(route_distance, solution.Value(dist_dim.CumulVar(index)))
# # #             index = solution.Value(routing.NextVar(index))
# # #         daily_distances.append(route_distance)

# # #     return solution, daily_distances


# # # # def multi_day_routing_real(num_days, lambda_penalty, mu_penalty):
# # # #     """
# # # #     Lặp qua các ngày => load_data(real_mode=True) => create_data_model => solve
# # # #     Bỏ qua ngày nếu distance_matrix rỗng
# # # #     Lưu output dưới dạng cũ (vehicles: {...})
# # # #     """
# # # #     historical_km = None
# # # #     all_outputs = [{"vehicles": {}}]  # => outputs[0] = meta

# # # #     for i in range(num_days):
# # # #         day = DATES[i]
# # # #         logger.info(f"--- Real Day {day} ---")

# # # #         distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data(
# # # #             request_file=f"data/intermediate/{day}.json",
# # # #             real_mode=True
# # # #         )

# # # #         # Skip nếu rỗng
# # # #         if not distance_matrix or num_nodes == 0:
# # # #             logger.warning(f"⚠️ Day {day}: distance_matrix rỗng => bỏ qua.")
# # # #             all_outputs.append({"vehicles": {}})
# # # #             continue

# # # #         if not historical_km:
# # # #             historical_km = [0 for _ in range(num_vehicles)]

# # # #         data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
# # # #         if len(data["distance_matrix"]) == 0:
# # # #             logger.warning(f"⚠️ Day {day}: after create_data_model => no nodes => skip")
# # # #             all_outputs.append({"vehicles": {}})
# # # #             continue

# # # #         routing, manager = create_routing_model(data)
# # # #         solution, daily_distances = solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty)
# # # #         if solution is None:
# # # #             logger.error(f"No solution for day {day}")
# # # #             all_outputs.append({"vehicles": {}})
# # # #             continue

# # # #         # Cập nhật historical_km
# # # #         for v in range(data["num_vehicles"]):
# # # #             historical_km[v] += daily_distances[v]

# # # #         # Tạo output (theo định dạng cũ)
# # # #         distance_dim = routing.GetDimensionOrDie("Distance")
# # # #         time_dim = routing.GetDimensionOrDie("Time")
# # # #         day_output = {"vehicles": {}}

# # # #         for veh in range(data["num_vehicles"]):
# # # #             index = routing.Start(veh)
# # # #             route_list = []
# # # #             route_distance = 0
# # # #             while not routing.IsEnd(index):
# # # #                 node_idx = manager.IndexToNode(index)
# # # #                 arrival_t = solution.Value(time_dim.CumulVar(index))
# # # #                 next_index = solution.Value(routing.NextVar(index))
# # # #                 delivered = 0  # Test script gán
# # # #                 route_list.append({
# # # #                     "node": node_idx,
# # # #                     "arrival_time": arrival_t,
# # # #                     "capacity": 0,  # optional
# # # #                     "delivered": delivered
# # # #                 })

# # # #                 if not routing.IsEnd(next_index):
# # # #                     route_distance = max(route_distance, solution.Value(distance_dim.CumulVar(next_index)))
# # # #                 index = next_index

# # # #             # node cuối
# # # #             node_idx = manager.IndexToNode(index)
# # # #             arrival_t = solution.Value(time_dim.CumulVar(index))
# # # #             route_list.append({
# # # #                 "node": node_idx,
# # # #                 "arrival_time": arrival_t,
# # # #                 "capacity": 0,
# # # #                 "delivered": 0
# # # #             })

# # # #             day_output["vehicles"][veh] = {
# # # #                 "distance_of_route": route_distance,
# # # #                 "list_of_route": route_list
# # # #             }

# # # #         all_outputs.append(day_output)
# # # #         logger.info(f"Updated historical km: {historical_km}")

# # # #     return all_outputs, historical_km
# # # import os
# # # def multi_day_routing_real(num_days, lambda_penalty, mu_penalty):
# # #     historical_km = None
# # #     all_outputs = [{"vehicles": {}}]  # meta

# # #     # Tính ma trận khoảng cách một lần nếu có thể
# # #     cached_distance_matrix = None
# # #     if os.path.exists("data/processed_distance_matrix.pkl"):
# # #         with open("data/processed_distance_matrix.pkl", "rb") as f:
# # #             cached_distance_matrix = pickle.load(f)

# # #     for i in range(num_days):
# # #         day = DATES[i]
# # #         logger.info(f"--- Real Day {day} ---")

# # #         distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data(
# # #             request_file=f"data/intermediate/{day}.json", real_mode=True)
# # #         if not distance_matrix:
# # #             all_outputs.append({"vehicles": {}})
# # #             continue

# # #         if cached_distance_matrix and len(cached_distance_matrix) == num_nodes:
# # #             distance_matrix = cached_distance_matrix

# # #         if not historical_km:
# # #             historical_km = [0] * num_vehicles

# # #         data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
# # #         if not data["distance_matrix"]:
# # #             all_outputs.append({"vehicles": {}})
# # #             continue

# # #         routing, manager = create_routing_model(data)
# # #         solution, daily_distances = solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty)
# # #         if not solution:
# # #             all_outputs.append({"vehicles": {}})
# # #             continue

# # #         for v in range(num_vehicles):
# # #             historical_km[v] += daily_distances[v]

# # #         # Tạo output (giữ nguyên logic của bạn)
# # #         day_output = {"vehicles": {}}
# # #         # ... (thêm logic tạo output như trong code của bạn)
# # #         all_outputs.append(day_output)

# # #     return all_outputs, historical_km

# # # if __name__ == "__main__":
# # #     parser = argparse.ArgumentParser(description="Solve 6-depot VRP multi-day with real data, for existing list-based JSON.")
# # #     parser.add_argument("--output", type=str, help="Path to output JSON file", required=False)
# # #     args = parser.parse_args()

# # #     Path("data/test").mkdir(parents=True, exist_ok=True)

# # #     if not IS_TESTING:
# # #         logger.info("IS_TESTING=True => Dùng code test generator ... (placeholder)")
# # #         all_outputs = [{"vehicles": {}}]
# # #         historical_km = [0]*NUM_OF_VEHICLES
# # #     else:
# # #         all_outputs, historical_km = multi_day_routing_real(num_days=NUM_OF_DAY_REPETION,
# # #                                                             lambda_penalty=LAMBDA,
# # #                                                             mu_penalty=MU)

# # #     current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# # #     if args.output:
# # #         output_filename = args.output
# # #     else:
# # #         output_filename = f"data/test/output_{current_time}.json"

# # #     with open(output_filename, "w", encoding="utf-8") as f:
# # #         json.dump(all_outputs, f, ensure_ascii=False, indent=4)

# # #     logger.info(f"Output saved to {output_filename}")
# # #     logger.info(f"historical_km = {historical_km}")

# # import json
# # import random
# # import logging
# # import argparse
# # from datetime import datetime
# # from pathlib import Path
# # import os
# # import pickle

# # from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# # import utilities.load_requests as load_requests
# # from config import *  # Chứa IS_TESTING, LAMBDA, MU, DEPOT_VEHICLE_COUNTS, depots, DATES, v.v.
# # from objects.request import Request
# # from utilities.split_data import split_customers, split_requests
# # from utilities.update_map import update_map

# # # Cấu hình logging: in ra console và có thể ghi file nếu cần.
# # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# # logger = logging.getLogger(__name__)

# # # Các hằng số cho cân bằng (chỉ dùng cân bằng theo lịch sử km của từng xe)
# # THRESHOLD_KM = 20  # không còn sử dụng do không chia đội nữa
# # ALPHA_BALANCE = 2
# # HUGE_PENALTY = 10000  # không dùng nữa

# # # Chiến lược tìm kiếm của OR-Tools
# # search_strategy = [
# #     routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
# #     routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
# #     routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
# #     routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
# # ][SEARCH_STRATEGY]

# # def load_data(distance_file="data/distance.json",
# #               request_file="data/intermediate/19022025.json",
# #               vehicle_file="data/vehicle.json",
# #               real_mode=True):
# #     """
# #     Load dữ liệu:
# #       - Đọc file vehicle.json -> vehicle_capacities.
# #       - Đọc file request -> requests_data.
# #       - Nếu real_mode=True, tính distance_matrix dựa trên split_requests và update_map.
# #       - Tạo demands và time_windows cho các node.
# #     """
# #     logger.info("Loading vehicle capacities from %s...", vehicle_file)
# #     with open(vehicle_file, "r", encoding="utf-8") as vf:
# #         vehicle_capacities = [int(u * CAPACITY_SCALE) for u in json.load(vf)]
# #     num_vehicles = len(vehicle_capacities)
# #     logger.info("Loaded %d vehicle capacities.", num_vehicles)

# #     logger.info("Loading requests from %s...", request_file)
# #     requests_data = load_requests.load_requests(request_file)
# #     if not requests_data:
# #         logger.warning("No requests found in %s. Returning empty matrix.", request_file)
# #         return [], [], vehicle_capacities, [], 0, num_vehicles
# #     logger.info("Loaded %d request objects.", len(requests_data))

# #     # Tách các request nếu cần
# #     if real_mode:
# #         logger.info("Splitting requests (if necessary)...")
# #         divided_mapped_requests, mapping, inverse_mapping = split_requests(requests_data)
# #         if not divided_mapped_requests:
# #             logger.warning("After splitting, no request remains from file: %s", request_file)
# #             return [], [], vehicle_capacities, [], 0, num_vehicles
# #         logger.info("After splitting, total mapped requests: %d", len(divided_mapped_requests))
# #         logger.info("update_map:orig_nodes: %s", mapping.keys())
# #         distance_matrix = update_map(divided_mapped_requests, mapping, inverse_mapping)
# #     else:
# #         logger.info("Loading distance matrix from %s...", distance_file)
# #         with open(distance_file, "r", encoding="utf-8") as df:
# #             dm = json.load(df)
# #             distance_matrix = [[int(u * DISTANCE_SCALE) for u in row] for row in dm]

# #     if not distance_matrix:
# #         logger.warning("Distance matrix is empty from file: %s", request_file)
# #         return [], [], vehicle_capacities, [], 0, num_vehicles

# #     num_nodes = len(distance_matrix)
# #     if any(len(row) != num_nodes for row in distance_matrix):
# #         logger.warning("Distance matrix is not square in file: %s", request_file)
# #         return [], [], vehicle_capacities, [], 0, num_vehicles

# #     # Tạo demands & time_windows
# #     logger.info("Creating demands and time windows for %d nodes...", num_nodes)
# #     demands = [0] * num_nodes
# #     time_windows = [(0, 24 * TIME_SCALE)] * num_nodes
# #     for req in requests_data:
# #         end_place = req.end_place[0]
# #         if end_place < 0 or end_place >= num_nodes:
# #             logger.warning("end_place %d out of bounds [0, %d]. Skipping.", end_place, num_nodes - 1)
# #             continue
# #         demands[end_place] += int(req.weight * CAPACITY_SCALE)
# #         tw = (req.timeframe[0] * TIME_SCALE, req.timeframe[1] * TIME_SCALE)
# #         time_windows[end_place] = tw

# #     logger.info("Loaded data: %d nodes, %d vehicles from %s", num_nodes, num_vehicles, request_file)
# #     return distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles

# # def create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, depot_vehicle_counts):
# #     """
# #     Tạo data model cho OR-Tools.
# #       - Bao gồm: distance_matrix, demands, vehicle_capacities, num_vehicles, depots, time_windows.
# #       - Gọi hàm split_customers nếu demand của khách hàng vượt quá tải nhỏ nhất.
# #     """
# #     logger.info("Creating data model...")
# #     data = {
# #         "distance_matrix": distance_matrix,
# #         "demands": demands,
# #         "vehicle_capacities": vehicle_capacities,
# #         "num_vehicles": sum(depot_vehicle_counts),
# #         "depot_vehicle_counts": depot_vehicle_counts,
# #         "depots": depots,  # từ config.py
# #         "time_windows": time_windows
# #     }
# #     data, node_mapping = split_customers(data)
# #     logger.info("Data model created with %d nodes after splitting.", len(data["demands"]))
# #     return data

# # def create_routing_model(data):
# #     """
# #     Tạo RoutingIndexManager & RoutingModel cho 6 depot.
# #     Không chia đội A/B, mỗi xe được gán start point theo vòng lặp từ depots [0,1,2,3,4,5].
# #     """
# #     num_vehicles = data["num_vehicles"]
# #     logger.info("Creating Routing Model for %d vehicles using depots %s...", num_vehicles, data["depots"])
# #     start_nodes = [data["depots"][v % len(data["depots"])] for v in range(num_vehicles)]
# #     end_nodes = start_nodes[:]  # End nodes giống start nodes
# #     logger.info("Assigned start nodes: %s", start_nodes)

# #     manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), num_vehicles, start_nodes, end_nodes)
# #     routing = pywrapcp.RoutingModel(manager)

# #     # Callback tính khoảng cách giữa 2 node
# #     def distance_callback(from_idx, to_idx):
# #         from_node = manager.IndexToNode(from_idx)
# #         to_node = manager.IndexToNode(to_idx)
# #         return data["distance_matrix"][from_node][to_node]
# #     dist_cb_idx = routing.RegisterTransitCallback(distance_callback)
# #     routing.SetArcCostEvaluatorOfAllVehicles(dist_cb_idx)

# #     # Thêm dimension cho khoảng cách
# #     routing.AddDimension(dist_cb_idx, 0, MAX_TRAVEL_DISTANCE, True, "Distance")
# #     routing.GetDimensionOrDie("Distance").SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)
# #     logger.info("Added Distance dimension.")

# #     # Thêm dimension cho số lượng điểm dừng tối đa
# #     stops_cb_idx = routing.RegisterTransitCallback(lambda f, t: 1)
# #     routing.AddDimension(stops_cb_idx, 0, MAX_ROUTE_SIZE, True, "Stops")
# #     logger.info("Added Stops dimension.")

# #     # Callback demand (không tính depot)
# #     def demand_callback(from_index):
# #         node = manager.IndexToNode(from_index)
# #         return 0 if node in data["depots"] else -data["demands"][node]
# #     demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_callback)
# #     routing.AddDimensionWithVehicleCapacity(demand_cb_idx, 0, data["vehicle_capacities"], False, "Capacity")
# #     cap_dim = routing.GetDimensionOrDie("Capacity")
# #     for v in range(num_vehicles):
# #         s = routing.Start(v)
# #         e = routing.End(v)
# #         cap_dim.CumulVar(s).SetRange(0, data["vehicle_capacities"][v])
# #         cap_dim.CumulVar(e).SetRange(0, 0)
# #     logger.info("Added Capacity dimension.")

# #     # Callback thời gian (time)
# #     def time_callback(from_index, to_index):
# #         from_node = manager.IndexToNode(from_index)
# #         to_node = manager.IndexToNode(to_index)
# #         velocity = AVG_VELOCITY
# #         service_time = 0 if from_node in data["depots"] else 1
# #         travel_time = data["distance_matrix"][from_node][to_node] / velocity
# #         return int(travel_time + service_time)
# #     time_cb_idx = routing.RegisterTransitCallback(time_callback)
# #     routing.AddDimension(time_cb_idx, MAX_WAITING_TIME, MAX_TRAVEL_TIME, False, "Time")
# #     time_dim = routing.GetDimensionOrDie("Time")
# #     for idx, window in enumerate(data["time_windows"]):
# #         time_dim.CumulVar(manager.NodeToIndex(idx)).SetRange(window[0], window[1])
# #     logger.info("Added Time dimension.")

# #     logger.info("Routing model successfully created.")
# #     return routing, manager

# # def solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty):
# #     logger.info("Setting fixed cost for each vehicle based on historical km...")
# #     search_params = pywrapcp.DefaultRoutingSearchParameters()
# #     # Ép cứng sử dụng chiến lược PATH_CHEAPEST_ARC (strategy 0)
# #     search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
# #     # Đặt giới hạn thời gian 60 giây (có thể điều chỉnh lại nếu cần)

# #     # Bật log của solver
# #     search_params.log_search = True

# #     logger.info("Solving routing model using strategy %s...", "PATH_CHEAPEST_ARC")
    
# #     dist_dim = routing.GetDimensionOrDie("Distance")
# #     min_capacity = min(data["vehicle_capacities"])
# #     avg_km = sum(historical_km) / len(historical_km) if historical_km else 0

# #     for v in range(data["num_vehicles"]):
# #         base_cost = lambda_penalty * historical_km[v] + mu_penalty * (data["vehicle_capacities"][v] - min_capacity)
# #         balance_penalty = ALPHA_BALANCE * max(0, historical_km[v] - avg_km)
# #         total_fixed_cost = base_cost + balance_penalty
# #         routing.SetFixedCostOfVehicle(int(total_fixed_cost), v)
# #         logger.info("Vehicle %d: historical_km = %d, fixed_cost = %d", v, historical_km[v], int(total_fixed_cost))

# #     logger.info("Starting solver...")
# #     solution = routing.SolveWithParameters(search_params)
# #     if not solution:
# #         logger.warning("No solution found within the time limit!")
# #         return None, None

# #     daily_distances = []
# #     for v in range(data["num_vehicles"]):
# #         index = routing.Start(v)
# #         route_distance = 0
# #         while not routing.IsEnd(index):
# #             route_distance = max(route_distance, solution.Value(dist_dim.CumulVar(index)))
# #             index = solution.Value(routing.NextVar(index))
# #         daily_distances.append(route_distance)
# #         logger.info("Vehicle %d route distance: %d", v, route_distance)

# #     return solution, daily_distances




# # def multi_day_routing_real(num_days, lambda_penalty, mu_penalty):
# #     """
# #     Xử lý định tuyến đa ngày với dữ liệu thực.
# #     Duyệt qua các ngày trong DATES, cập nhật historical_km và lưu kết quả.
# #     """
# #     logger.info("Starting multi-day routing for %d days...", num_days)
# #     historical_km = None
# #     all_outputs = [{"vehicles": {}}]  # meta

# #     # Nếu có, tải ma trận khoảng cách đã cache để tái sử dụng
# #     cached_distance_matrix = None
# #     cache_file = "data/processed_distance_matrix.pkl"
# #     if os.path.exists(cache_file):
# #         with open(cache_file, "rb") as f:
# #             cached_distance_matrix = pickle.load(f)
# #         logger.info("Loaded cached distance matrix from %s", cache_file)

# #     for i in range(num_days):
# #         day = DATES[i]
# #         logger.info("--- Real Day %s ---", day)

# #         distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data(
# #             request_file=f"data/intermediate/{day}.json", real_mode=True)
# #         if not distance_matrix:
# #             logger.warning("Distance matrix is empty for day %s. Skipping.", day)
# #             all_outputs.append({"vehicles": {}})
# #             continue

# #         if cached_distance_matrix and len(cached_distance_matrix) == num_nodes:
# #             distance_matrix = cached_distance_matrix
# #             logger.info("Using cached distance matrix for day %s.", day)

# #         if not historical_km:
# #             historical_km = [0] * num_vehicles

# #         data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
# #         if not data["distance_matrix"]:
# #             logger.warning("Data model has empty distance matrix for day %s. Skipping.", day)
# #             all_outputs.append({"vehicles": {}})
# #             continue

# #         routing, manager = create_routing_model(data)
# #         solution, daily_distances = solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty)
# #         if not solution:
# #             logger.error("No solution found for day %s", day)
# #             all_outputs.append({"vehicles": {}})
# #             continue

# #         for v in range(num_vehicles):
# #             historical_km[v] += daily_distances[v]
# #         logger.info("Updated historical km: %s", historical_km)

# #         # Tạo output (bạn có thể mở rộng logic xuất chi tiết tuyến đường tại đây)
# #         day_output = {"vehicles": {}}
# #         all_outputs.append(day_output)
# #         logger.info("Finished processing day %s.", day)

# #     return all_outputs, historical_km

# # if __name__ == "__main__":
# #     parser = argparse.ArgumentParser(
# #         description="Giải bài toán VRP 6 depot đa ngày với dữ liệu thực (không chia đội A/B)."
# #     )
# #     parser.add_argument("--output", type=str, help="Đường dẫn đến tệp JSON đầu ra", required=False)
# #     args = parser.parse_args()

# #     Path("data/test").mkdir(parents=True, exist_ok=True)

# #     if not IS_TESTING:
# #         logger.info("IS_TESTING=False => Chạy chế độ thử nghiệm (placeholder)")
# #         all_outputs = [{"vehicles": {}}]
# #         historical_km = [0] * NUM_OF_VEHICLES
# #     else:
# #         all_outputs, historical_km = multi_day_routing_real(
# #             num_days=NUM_OF_DAY_REPETION,
# #             lambda_penalty=LAMBDA,
# #             mu_penalty=MU
# #         )

# #     current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# #     output_filename = args.output if args.output else f"data/test/output_{current_time}.json"

# #     with open(output_filename, "w", encoding="utf-8") as f:
# #         json.dump(all_outputs, f, ensure_ascii=False, indent=4)

# #     logger.info("Output saved to %s", output_filename)
# #     logger.info("Final historical_km = %s", historical_km)
# import sys
# import json
# import random
# import logging
# import argparse
# from datetime import datetime
# from pathlib import Path
# import os
# import pickle

# from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# # Import các hằng số và cấu hình từ file config.py (đảm bảo trong config.py có các biến như: IS_TESTING, LAMBDA, MU, DEPOT_VEHICLE_COUNTS, depots, DATES, DISTANCE_SCALE, CAPACITY_SCALE, TIME_SCALE, AVG_VELOCITY, MAX_TRAVEL_DISTANCE, MAX_ROUTE_SIZE, MAX_WAITING_TIME, MAX_TRAVEL_TIME, ...)
# from config import *
# # Import các hàm xử lý dữ liệu, tách request, cập nhật map
# from utilities.split_data import split_customers, split_requests
# from utilities.update_map import update_map
# import utilities.load_requests as load_requests
# # Nếu cần import generator để test nhiều ngày (nếu bạn dùng chế độ demo)
# import utilities.generator2depots as generator

# # Cấu hình logging để in ra console
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)

# # Sử dụng chiến lược PATH_CHEAPEST_ARC cho OR-Tools
# search_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

# #--------------------------------------------------
# # Hàm load_data: đọc ma trận khoảng cách, tải xe và request từ file.
# # Phiên bản này dùng cho chế độ demo hoặc dữ liệu thật (bạn có thể chuyển đổi qua real_mode nếu cần)
# def load_data(distance_file="data/distance.json",
#               request_file="data/intermediate/{TODAY}.json",
#               vehicle_file="data/vehicle.json",
#               real_mode=True):
#     # Đọc ma trận khoảng cách và scale theo DISTANCE_SCALE
#     logger.info("Loading distance matrix from %s", distance_file)
#     with open(distance_file, "r", encoding="utf-8") as f:
#         distance_matrix = json.load(f)
#     distance_matrix = [[int(u * DISTANCE_SCALE) for u in row] for row in distance_matrix]
#     num_nodes = len(distance_matrix)

#     # Đọc dung tích xe và scale theo CAPACITY_SCALE
#     logger.info("Loading vehicle capacities from %s", vehicle_file)
#     with open(vehicle_file, "r", encoding="utf-8") as f:
#         vehicle_capacities = json.load(f)
#     vehicle_capacities = [int(u * CAPACITY_SCALE) for u in vehicle_capacities]
#     num_vehicles = len(vehicle_capacities)

#     # Đọc danh sách request
#     logger.info("Loading requests from %s", request_file)
#     requests_data = load_requests.load_requests(request_file)
#     if not requests_data:
#         logger.warning("No requests loaded from %s", request_file)
#     # Khởi tạo demands và time windows cho mỗi node
#     demands = [0] * num_nodes
#     time_windows = [(0, 24 * TIME_SCALE) for _ in range(num_nodes)]
#     for req in requests_data:
#         end_place = req.end_place[0]
#         demands[end_place] += int(req.weight * CAPACITY_SCALE)
#         time_windows[end_place] = (req.timeframe[0] * TIME_SCALE, req.timeframe[1] * TIME_SCALE)

#     logger.info("Loaded data: %d nodes, %d vehicles", num_nodes, num_vehicles)
#     return distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles

# #--------------------------------------------------
# # Hàm create_data_model: tạo data model cho OR-Tools,
# # bao gồm ma trận khoảng cách, demands, dung tích xe, số xe, danh sách depot, time windows.
# # Sau đó gọi split_customers để tách các node có demand lớn.
# def create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, depot_vehicle_counts):
#     logger.info("Creating data model...")
#     data = {
#         "distance_matrix": distance_matrix,
#         "demands": demands,
#         "vehicle_capacities": vehicle_capacities,
#         # Số xe = tổng số xe theo từng depot, theo cấu hình DEPOT_VEHICLE_COUNTS (ví dụ: [num_teamA, num_teamB])
#         "num_vehicles": sum(depot_vehicle_counts),
#         "depot_vehicle_counts": depot_vehicle_counts,
#         # Danh sách depot từ config, ví dụ depots = [0, 1, 2, 3, 4, 5]
#         "depots": depots,
#         "time_windows": time_windows
#     }
#     data, node_mapping = split_customers(data)
#     logger.info("Data model created with %d nodes after splitting.", len(data["demands"]))
#     logger.info("Node mapping: %s", node_mapping)
#     return data

# #--------------------------------------------------
# # Hàm create_routing_model: tạo RoutingIndexManager và RoutingModel cho bài toán chia đội A/B.
# # Team A sử dụng depot team_A_depots (ví dụ: depots 0,1,2) và Team B sử dụng team_B_depots (ví dụ: depots 3,4,5).
# def create_routing_model(data):
#     num_vehicles = data["num_vehicles"]
#     depot_vehicle_counts = data["depot_vehicle_counts"]
#     # Giả sử team A có depot từ depots[0:3], team B có depot từ depots[3:6]
#     team_A_depots = depots[:3]
#     team_B_depots = depots[3:6]
#     # Số xe của team A là depot_vehicle_counts[0] (hoặc tổng của team A nếu nhiều giá trị)
#     num_depot_A = depot_vehicle_counts[0]
    
#     # Gán start nodes theo chia đội: xe team A nhận depot từ team_A_depots,
#     # xe team B nhận depot từ team_B_depots.
#     start_nodes = []
#     for v in range(num_vehicles):
#         if v < num_depot_A:
#             start_nodes.append(team_A_depots[v % len(team_A_depots)])
#         else:
#             start_nodes.append(team_B_depots[(v - num_depot_A) % len(team_B_depots)])
#     # Ở đây, ta đặt điểm kết thúc giống điểm xuất phát (có thể điều chỉnh nếu cần khác)
#     end_nodes = start_nodes[:]
    
#     logger.info("Assigned start nodes (Team A/B): %s", start_nodes)
#     manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), num_vehicles, start_nodes, end_nodes)
#     routing = pywrapcp.RoutingModel(manager)
    
#     #-------------------------------
#     # Đăng ký callback tính khoảng cách giữa 2 node.
#     def distance_callback(from_index, to_index):
#         from_node = manager.IndexToNode(from_index)
#         to_node = manager.IndexToNode(to_index)
#         return data["distance_matrix"][from_node][to_node]
#     transit_callback_index = routing.RegisterTransitCallback(distance_callback)
#     routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
#     # Dimension "Distance": theo dõi tổng khoảng cách của mỗi xe.
#     routing.AddDimension(
#         transit_callback_index,
#         0,                      # không cho phép slack
#         MAX_TRAVEL_DISTANCE,    # giới hạn quãng đường tối đa
#         True,                   # bắt buộc fix start cumul = 0
#         "Distance"
#     )
#     distance_dimension = routing.GetDimensionOrDie("Distance")
#     distance_dimension.SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)
#     logger.info("Added Distance dimension.")
    
#     # Dimension "Stops": theo dõi số điểm dừng (sử dụng callback trả về 1 cho mỗi chuyến đi).
#     stops_callback_index = routing.RegisterTransitCallback(lambda from_idx, to_idx: 1)
#     routing.AddDimension(
#         stops_callback_index,
#         0,                  # slack = 0
#         MAX_ROUTE_SIZE,     # số điểm dừng tối đa trên 1 tuyến
#         True,
#         "Stops"
#     )
#     logger.info("Added Stops dimension.")
    
#     # Dimension "Capacity": theo dõi tải trọng xe.
#     # Đối với các depot, demand = 0; đối với khách hàng, demand được đưa vào với dấu âm (để mô phỏng việc giảm tải khi giao hàng).
#     def demand_callback(from_index):
#         node = manager.IndexToNode(from_index)
#         return 0 if node in data["depots"] else -data["demands"][node]
#     demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
#     routing.AddDimensionWithVehicleCapacity(
#         demand_callback_index,
#         0,                      # slack = 0
#         data["vehicle_capacities"],  # giới hạn tải trọng theo xe
#         False,                  # không ép bắt đầu cumul từ 0 (có thể điều chỉnh nếu cần)
#         "Capacity"
#     )
#     capacity_dimension = routing.GetDimensionOrDie("Capacity")
#     for v in range(num_vehicles):
#         s = routing.Start(v)
#         e = routing.End(v)
#         capacity_dimension.CumulVar(s).SetRange(0, data["vehicle_capacities"][v])
#         capacity_dimension.CumulVar(e).SetRange(0, 0)
#     logger.info("Added Capacity dimension.")
    
#     # Dimension "Time": theo dõi thời gian di chuyển, bao gồm thời gian dịch vụ tại khách.
#     def time_callback(from_index, to_index):
#         from_node = manager.IndexToNode(from_index)
#         to_node = manager.IndexToNode(to_index)
#         # Đặt tốc độ trung bình và thời gian phục vụ (đối với depot thì service_time = 0)
#         velocity = AVG_VELOCITY
#         service_time = 0 if from_node in data["depots"] else 1
#         travel_time = data["distance_matrix"][from_node][to_node] / velocity
#         return int(travel_time + service_time)
#     time_cb_index = routing.RegisterTransitCallback(time_callback)
#     routing.AddDimension(
#         time_cb_index,
#         MAX_WAITING_TIME,   # cho phép chờ tối đa
#         MAX_TRAVEL_TIME,    # giới hạn thời gian di chuyển tối đa
#         False,
#         "Time"
#     )
#     time_dimension = routing.GetDimensionOrDie("Time")
#     for idx, window in enumerate(data["time_windows"]):
#         index = manager.NodeToIndex(idx)
#         time_dimension.CumulVar(index).SetRange(window[0], window[1])
#     logger.info("Added Time dimension.")
    
#     logger.info("Routing model created successfully with team A/B splitting.")
#     return routing, manager

# #--------------------------------------------------
# # Hàm solve_routing: thiết lập fixed cost dựa trên lịch sử quãng đường và tải trọng, sau đó giải bài toán.
# def solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty):
#     logger.info("Setting fixed cost for each vehicle based on historical km and capacity...")
#     search_params = pywrapcp.DefaultRoutingSearchParameters()
#     search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
#     search_params.log_search = True

#     dist_dim = routing.GetDimensionOrDie("Distance")
#     min_capacity = min(data["vehicle_capacities"])
#     avg_km = sum(historical_km) / len(historical_km) if historical_km else 0

#     # Ví dụ: áp dụng fixed cost khác nhau cho team A và team B
#     num_depot_A = data["depot_vehicle_counts"][0]
#     for v in range(data["num_vehicles"]):
#         # Tính base cost dựa trên lịch sử km và chênh lệch dung tích xe
#         base_cost = lambda_penalty * historical_km[v] + mu_penalty * (data["vehicle_capacities"][v] - min_capacity)
#         # Nếu có cân bằng đội, có thể thêm penalty nếu xe trong team nào chạy quá nhiều
#         if v < num_depot_A:
#             # Team A: có thể thêm penalty nếu tổng km của team A vượt quá ngưỡng so với team B
#             pass  # Ở đây bạn có thể điều chỉnh thêm nếu muốn
#         else:
#             # Team B: tương tự
#             pass
#         total_fixed_cost = base_cost  # + các penalty bổ sung nếu cần
#         routing.SetFixedCostOfVehicle(int(total_fixed_cost), v)
#         logger.info("Vehicle %d: historical_km = %d, fixed_cost = %d", v, historical_km[v], int(total_fixed_cost))

#     logger.info("Starting solver...")
#     solution = routing.SolveWithParameters(search_params)
#     if not solution:
#         logger.warning("No solution found within the time limit!")
#         return None, None

#     daily_distances = []
#     for v in range(data["num_vehicles"]):
#         index = routing.Start(v)
#         route_distance = 0
#         while not routing.IsEnd(index):
#             route_distance = max(route_distance, solution.Value(dist_dim.CumulVar(index)))
#             index = solution.Value(routing.NextVar(index))
#         daily_distances.append(route_distance)
#         logger.info("Vehicle %d route distance: %d", v, route_distance)

#     return solution, daily_distances

# #--------------------------------------------------
# # Hàm in kết quả định tuyến (theo dạng text)
# def print_daily_solution(data, manager, routing, solution):
#     time_dimension = routing.GetDimensionOrDie("Time")
#     capacity_dimension = routing.GetDimensionOrDie("Capacity")
#     total_distance = 0
#     for v in range(data["num_vehicles"]):
#         index = routing.Start(v)
#         route_distance = 0
#         output = f"Route for vehicle {v}:\n"
#         while not routing.IsEnd(index):
#             node = manager.IndexToNode(index)
#             arrival = solution.Value(time_dimension.CumulVar(index))
#             current_cap = solution.Value(capacity_dimension.CumulVar(index))
#             next_index = solution.Value(routing.NextVar(index))
#             delivered = 0
#             if node not in data["depots"]:
#                 delivered = current_cap - solution.Value(capacity_dimension.CumulVar(next_index))
#             output += f"  Node {node} (Arrival: {arrival}, Capacity: {current_cap}, Delivered: {delivered}) ->\n"
#             prev = index
#             index = next_index
#             route_distance += data["distance_matrix"][manager.IndexToNode(prev)][manager.IndexToNode(index)]
#         node = manager.IndexToNode(index)
#         arrival = solution.Value(time_dimension.CumulVar(index))
#         final_cap = solution.Value(capacity_dimension.CumulVar(index))
#         output += f"  Node {node} (Arrival: {arrival}, Capacity: {final_cap}, Delivered: 0)\n"
#         output += f"Distance of the route: {route_distance}\n"
#         print(output)
#         total_distance += route_distance
#     print(f"Total distance of all routes: {total_distance}")

# #--------------------------------------------------
# # Hàm multi_day_routing: chạy định tuyến cho nhiều ngày, cập nhật historical km, và lưu output.
# def multi_day_routing(num_days, lambda_penalty, mu_penalty):
#     logger.info("Starting multi-day routing for %d days...", num_days)
#     historical_km = None
#     all_outputs = [{"meta": "Multi-day routing output", "dates": DATES}]
#     list_of_seed = []
    
#     for day in DATES:
#         logger.info("----- Day %s -----", day)
#         seed = random.randint(10, 1000)
#         list_of_seed.append(seed)
#         # Sinh request và lưu file theo ngày (nếu dùng generator)
#         generator.gen_requests_and_save(NUM_OF_REQUEST_PER_DAY, file_sufices=str(day),
#                                         NUM_OF_NODES=NUM_OF_NODES, seed=seed)
#         # Load dữ liệu cho ngày đó
#         distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data(
#             request_file=f"data/intermediate/{day}.json", real_mode=True)
#         if not historical_km:
#             historical_km = [0] * num_vehicles
#         data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
#         if not data["distance_matrix"]:
#             logger.warning("Data model has empty distance matrix for day %s. Skipping.", day)
#             all_outputs.append({"vehicles": {}})
#             continue
        
#         routing, manager = create_routing_model(data)
#         solution, daily_distances = solve_routing(routing, manager, data, historical_km, lambda_penalty, mu_penalty)
#         if not solution:
#             logger.error("No solution found for day %s", day)
#             all_outputs.append({"vehicles": {}})
#             continue
        
#         print_daily_solution(data, manager, routing, solution)
#         day_output = {"vehicles": {}}  # Bạn có thể mở rộng chi tiết output theo yêu cầu
#         all_outputs.append(day_output)
        
#         for v in range(num_vehicles):
#             historical_km[v] += daily_distances[v]
#         logger.info("Updated historical km: %s", historical_km)
    
#     logger.info("Seeds used: %s", list_of_seed)
#     return all_outputs, historical_km

# #--------------------------------------------------
# # Main: xử lý tham số dòng lệnh và chạy định tuyến đa ngày
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description="Solve multi-depot VRP with team A/B splitting for multiple days using real data."
#     )
#     parser.add_argument("--output", type=str, help="Path to output JSON file", required=False)
#     args = parser.parse_args()

#     Path("data/test").mkdir(parents=True, exist_ok=True)

#     if IS_TESTING:
#         # Sinh map và danh sách xe để test
#         generator.gen_map(NUM_OF_NODES=NUM_OF_NODES, seed=42)
#         generator.gen_list_vehicle(NUM_OF_VEHICLES=NUM_OF_VEHICLES, seed=42)
#         all_outputs, historical_km = multi_day_routing(
#             num_days=NUM_OF_DAY_REPETION,
#             lambda_penalty=LAMBDA,
#             mu_penalty=MU
#         )
#         output_data = all_outputs
#     else:
#         TODAY = datetime.now().strftime("%Y-%m-%d")
#         distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data(
#             request_file=f"data/intermediate/{TODAY}.json"
#         )
#         historical_km = [0] * num_vehicles
#         data = create_data_model(distance_matrix, demands, vehicle_capacities, time_windows, DEPOT_VEHICLE_COUNTS)
#         routing, manager = create_routing_model(data)
#         solution, daily_distances = solve_routing(routing, manager, data, historical_km, LAMBDA, MU)
#         if solution:
#             print_daily_solution(data, manager, routing, solution)
#             # Có thể tạo output theo định dạng mong muốn
#             output_data = {}
#         else:
#             logger.error("No solution found for today.")
    
#     current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     output_filename = args.output if args.output else f"data/test/output_{current_time}.json"
#     with open(output_filename, "w", encoding="utf-8") as f:
#         json.dump(output_data, f, ensure_ascii=False, indent=4)
#     logger.info("Output saved to %s", output_filename)
#     logger.info("Final historical_km = %s", historical_km)
#!/usr/bin/env python3
import sys
import json
import random
import logging
import argparse
from datetime import datetime
from pathlib import Path
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import utilities.load_requests as load_requests
from config import *  # Cấu hình: IS_TESTING, LAMBDA, MU, DEPOT_VEHICLE_COUNTS, depots, DATES, CAPACITY_SCALE, DISTANCE_SCALE, TIME_SCALE, AVG_VELOCITY, MAX_TRAVEL_DISTANCE, MAX_ROUTE_SIZE, MAX_WAITING_TIME, MAX_TRAVEL_TIME
from objects.request import Request
from utilities.split_data import split_customers, split_requests
from utilities.update_map import update_map

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Chiến lược tìm kiếm: sử dụng PATH_CHEAPEST_ARC
search_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

def load_data_team(distance_file="data/distance.json",
                   request_file="data/intermediate/{TODAY}.json",
                   vehicle_file="data/vehicle.json",
                   real_mode=True):
    # Load ma trận khoảng cách
    with open(distance_file, "r", encoding="utf-8") as f:
        distance_matrix = json.load(f)
    distance_matrix = [[int(u * DISTANCE_SCALE) for u in row] for row in distance_matrix]
    num_nodes = len(distance_matrix)
    
    # Load dung tích xe
    with open(vehicle_file, "r", encoding="utf-8") as f:
        vehicle_capacities = json.load(f)
    vehicle_capacities = [int(u * CAPACITY_SCALE) for u in vehicle_capacities]
    num_vehicles = len(vehicle_capacities)
    
    # Load requests và tạo demands, time_windows
    requests_data = load_requests.load_requests(request_file)
    print(requests_data)
    demands = [0] * num_nodes
    time_windows = [(0, 24 * TIME_SCALE) for _ in range(num_nodes)]
    for req in requests_data:
        end_place = req.end_place[0]
        demands[end_place] += int(req.weight * CAPACITY_SCALE)
        time_windows[end_place] = (req.timeframe[0] * TIME_SCALE, req.timeframe[1] * TIME_SCALE)
    
        
    logger.info("Team A/B: Loaded data: %d nodes, %d vehicles", num_nodes, num_vehicles)
    return distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles
distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data_team(distance_file="data/distance.json",
                   request_file="data/intermediate/19022025.json",
                   vehicle_file="data/vehicle.json",
                   real_mode=True)
print('distance_matrix is', distance_matrix)
print('demands is', demands)
print('num nodes is', num_nodes)
print('num_vehicle is', num_vehicles)
def create_data_model_team(distance_matrix, demands, vehicle_capacities, time_windows):
    data = {
        "distance_matrix": distance_matrix,
        "demands": demands,
        "vehicle_capacities": vehicle_capacities,
        "num_vehicles": sum(DEPOT_VEHICLE_COUNTS),  # tổng số xe theo cấu hình chia đội
        "depot_vehicle_counts": DEPOT_VEHICLE_COUNTS,
        "depots": depots,  # ví dụ: [0,1,2,3,4,5]
        "time_windows": time_windows
    }
    data, node_mapping = split_customers(data)
    logger.info("Team A/B: Data model created with %d nodes after splitting.", len(data["demands"]))
    return data

def create_routing_model_team(data):
    """
    Xây dựng Routing Model theo phương án Team A/B.
    - Team A: sử dụng các depot từ depots[0:3]
    - Team B: sử dụng các depot từ depots[3:6]
    """
    num_vehicles = data["num_vehicles"]
    num_depot_A = data["depot_vehicle_counts"][0]
    team_A_depots = depots[:3]   # [0, 1, 2]
    team_B_depots = depots[3:]   # [3, 4, 5]
    
    start_nodes = []
    for v in range(num_vehicles):
        if v < num_depot_A:
            start_nodes.append(team_A_depots[v % len(team_A_depots)])
        else:
            start_nodes.append(team_B_depots[(v - num_depot_A) % len(team_B_depots)])
    end_nodes = start_nodes[:]  # điểm kết thúc giống điểm bắt đầu
    
    logger.info("Team A/B: Assigned start nodes: %s", start_nodes)
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), num_vehicles, start_nodes, end_nodes)
    routing = pywrapcp.RoutingModel(manager)
    
    # Callback khoảng cách
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]
    transit_cb_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)
    
    # Dimension "Distance"
    routing.AddDimension(transit_cb_idx, 0, MAX_TRAVEL_DISTANCE, True, "Distance")
    routing.GetDimensionOrDie("Distance").SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)
    
    # Dimension "Stops" (số điểm dừng)
    stops_cb_idx = routing.RegisterTransitCallback(lambda f, t: 1)
    routing.AddDimension(stops_cb_idx, 0, MAX_ROUTE_SIZE, True, "Stops")
    
    # Dimension "Capacity"
    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        return 0 if node in depots else -data["demands"][node]
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
        service_time = 0 if from_node in depots else 1
        travel_time = data["distance_matrix"][from_node][to_node] / velocity
        return int(travel_time + service_time)
    time_cb_idx = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(time_cb_idx, MAX_WAITING_TIME, MAX_TRAVEL_TIME, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for idx, window in enumerate(data["time_windows"]):
        time_dim.CumulVar(manager.NodeToIndex(idx)).SetRange(window[0], window[1])
    
    logger.info("Team A/B: Routing model successfully created.")
    return routing, manager

def solve_team(data, historical_km, lambda_penalty, mu_penalty):
    routing, manager = create_routing_model_team(data)
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
        logger.info("Team A/B: Vehicle %d: historical_km=%d, fixed_cost=%d", v, historical_km[v], int(total_fixed_cost))
    
    solution = routing.SolveWithParameters(search_params)
    if not solution:
        logger.warning("Team A/B: No solution found!")
        return None, None, None, None
    
    daily_distances = []
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route_distance = 0
        while not routing.IsEnd(index):
            route_distance = max(route_distance, solution.Value(dist_dim.CumulVar(index)))
            index = solution.Value(routing.NextVar(index))
        daily_distances.append(route_distance)
        logger.info("Team A/B: Vehicle %d route distance: %d", v, route_distance)
    
    return solution, manager, daily_distances, routing

def print_solution_team(data, manager, routing, solution):
    time_dim = routing.GetDimensionOrDie("Time")
    cap_dim = routing.GetDimensionOrDie("Capacity")
    total_distance = 0
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route_str = f"Team A/B: Route for vehicle {v}:\n"
        route_distance = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival = solution.Value(time_dim.CumulVar(index))
            curr_cap = solution.Value(cap_dim.CumulVar(index))
            next_index = solution.Value(routing.NextVar(index))
            delivered = 0
            if node not in depots:
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
    logger.info("Team A/B: Total distance of all routes: %d", total_distance)

# -------------------------------
# Main cho Team A/B approach
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve VRP with 6 depot using Team A/B strategy.")
    parser.add_argument("--output", type=str, help="Output JSON file path", required=False)
    args = parser.parse_args()
    
    # Giả sử dùng file test
    Path("data/test").mkdir(parents=True, exist_ok=True)
    TODAY = datetime.now().strftime("%Y-%m-%d")
    distance_matrix, demands, vehicle_capacities, time_windows, num_nodes, num_vehicles = load_data_team(request_file=f"data/intermediate/{TODAY}.json")
    historical_km = [0] * num_vehicles  # Khởi tạo lịch sử quãng đường cho mỗi xe
    data = create_data_model_team(distance_matrix, demands, vehicle_capacities, time_windows)
    solution, manager, daily_distances, routing = solve_team(data, historical_km, LAMBDA, MU)
    if solution:
        print_solution_team(data, manager, routing, solution)
    else:
        logger.error("Team A/B: No solution found for today.")
    
    output_filename = args.output if args.output else f"data/test/team_output_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump({"message": "Team A/B solution computed; see logs for details."}, f, indent=4)
    logger.info("Team A/B: Output saved to %s", output_filename)
