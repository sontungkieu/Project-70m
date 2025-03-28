import json
import random
import csv
import math

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

import utilities.generator as generator
import utilities.loader as loader
from config import *
from objects.driver import Driver
from objects.request import Request
from utilities.split_data import split_requests
from utilities.update_map import update_map

# vehicle capacity phải là số nguyên
# chuyển hết sang đơn vị (0.1m3)
# xe 9.7 m3 thành 97 0.1m3

search_strategy = [
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
    routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
][SEARCH_STRATEGY]

# ------------------------------
# Phần "daily": tạo dữ liệu và mô hình định tuyến cho một ngày giao hàng

def load_data_real(
    day: str = DATES[0],
    distance_file="data/distance.json",
    driver_file="data/drivers.json",
):
    request_file=f"data/intermediate/{day}.json"
    global NUM_OF_VEHICLES, NUM_OF_NODES

    # Đọc danh sách vehicle từ JSON
    drivers_list, vehicle_capacities, available_times_s = loader.load_drivers(file_path=driver_file,is_converted_to_dict=True)
    vehicle_capacities = [int(u * CAPACITY_SCALE) for u in vehicle_capacities]
    NUM_OF_VEHICLES = len(vehicle_capacities)
    # print(f"available_times_s: {available_times_s}")

    # Chuyển đổi available_times_s sang đơn vị TIME_SCALE
    available_times_s = [
        [(int(start*TIME_SCALE), int(end*TIME_SCALE)) for start, end in driver_times[day]]
        for driver_times in available_times_s
    ]
    # print(f"available_times_s: {available_times_s}")
    # exit()
    # Đọc danh sách requests từ JSON
    requests_data = loader.load_requests(file_path=request_file)
    print(f"requests_data: len: {len(requests_data)}:  {requests_data}")
    divided_mapped_requests, mapping, inverse_mapping = split_requests(requests_data,)
    print(f"divided_mapped_requests: {divided_mapped_requests}")
    print(f"mapping: {mapping}")
    print(f"inverse_mapping: {inverse_mapping}")
    print(f"requests_data: {requests_data}")
    # exit(0)

    # update map
    distance_matrix = update_map(divided_mapped_requests, mapping, inverse_mapping)
    print(f"distance_matrix: {distance_matrix}")
    # exit()
    NUM_OF_NODES = len(distance_matrix)
    demands = [0 for _ in range(NUM_OF_NODES)]
    time_windows = [(0, 24 * TIME_SCALE) for _ in range(NUM_OF_NODES)]

    # convert requests to demands and time_windows
    for request in divided_mapped_requests:
        # print(f"request: {request}")
        end_place = request.end_place[0]
        weight = request.weight
        demands[end_place] += int(weight)
        time_windows[end_place] = (
            request.timeframe[0],
            request.timeframe[1],
        )

    print(f"demands: {demands}")
    # exit()
    # print(f"load_data_real:distance_matrix: {distance_matrix}")    
    print(f"engine1.py:load_data_real:len(distance_matrix): {len(distance_matrix)}")
    return distance_matrix, demands, vehicle_capacities, time_windows, available_times_s


def create_data_model(
    *, distance_matrix=None, demands=None, vehicles=None, time_window=None, available_times_s=None
):
    """Tạo dữ liệu cho bài toán giao hàng với split delivery.

    Trong bài toán này:
    - Một khách hàng nếu có nhu cầu vượt quá tải trọng của xe (ở đây là 5 đơn vị)
      sẽ được chia thành nhiều node riêng biệt.
    - Ví dụ:
         • Khách hàng 1 có đơn hàng 8 đơn vị sẽ chia thành 2 node: 1a (5 đơn vị) và 1b (3 đơn vị).
         • Khách hàng 4 có đơn hàng 6 đơn vị sẽ chia thành 2 node: 4a (5 đơn vị) và 4b (1 đơn vị).
    - Các node này đều có cùng vị trí (vì cùng là của khách hàng đó) nên khoảng cách giữa chúng bằng 0.
    """
    print(f"engine1.py:create_data_model:len(distance_matrix): {len(distance_matrix)}")

    global NUM_OF_VEHICLES

    data = {}

    data["distance_matrix"] = (
        DEFAULT_DISTANCE_MATRIX if not distance_matrix else distance_matrix
    )
    print(f'engine1.py:create_data_model:len(data["distance_matrix"]): {len(data["distance_matrix"])}')
    # print(f"distance_matrix: {data['distance_matrix']}")


    data["demands"] = DEFAULT_DEMANDS if not demands else demands

    # Với trọng tải của xe là 5 đơn vị, những node với demand <= 5 đảm bảo không vượt quá.
    # Tổng demand của các khách hàng là 5+3+1+2+5+1 = 17, nên sử dụng 4 xe với tải trọng 5 (tổng tải = 20).
    data["vehicle_capacities"] = (
        DEFAULT_VEHICLE_CAPACITIES if not vehicles else vehicles
    )

    data["num_vehicles"] = 4 if not vehicles else len(vehicles)
    NUM_OF_VEHICLES = data["num_vehicles"]
    data["depot"] = 0

    data["time_windows"] = DEFAULT_TIME_WINDOWS if time_window is None else time_window
    data["available_times_s"] = available_times_s  # Thêm thời gian rảnh của tài xế
    print(f"engine1.py:create_data_model:len(distance_matrix)_end: {len(distance_matrix)}")
    print(f'engine1.py:create_data_model:len(data["distance_matrix"])_end: {len(data["distance_matrix"])}')

    # print(f"node_mapping: {node_mapping}")

    return data


def create_daily_routing_model(data):
    print(f'engine1.py:create_daily_routing_model:len(data["distance_matrix"]): {len(data["distance_matrix"])}')

    print(f"create_daily_routing_model:")
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)

    # Callback khoảng cách
    import sys

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]
        try:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data["distance_matrix"][from_node][to_node]
        except Exception as e:
            print(f"🔥 Lỗi tại distance_callback với from_index = {from_index}, to_index = {to_index}")
            print(f"manager.Size() = {manager.GetNumberOfNodes()}, routing.Size() = {routing.Size()}")
            print(f"Lỗi chi tiết: {e}")
            sys.exit(1)


    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Dimension "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,
        MAX_TRAVEL_DISTANCE,
        True,
        "Distance",
    )
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)

    # Dimension "Stops"
    # Callback cho "Stops" (chỉ tính số điểm dừng, mỗi lần đi qua là 1 điểm)
    # def stops_callback(from_index):
    #     return 1  # Mỗi node là 1 điểm dừng

    # stops_callback_index = routing.RegisterUnaryTransitCallback(stops_callback)

    # routing.AddDimension(
    #     stops_callback_index,
    #     0,
    #     MAX_ROUTE_SIZE,
    #     True,
    #     "Stops",
    # )


    # Callback demand cho "Capacity"
    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        return 0 if node == data["depot"] else -data["demands"][node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        data["vehicle_capacities"],
        False,
        "Capacity",
    )
    capacity_dimension = routing.GetDimensionOrDie("Capacity")
    for v in range(data["num_vehicles"]):
        start = routing.Start(v)
        end = routing.End(v)
        capacity_dimension.CumulVar(start).SetRange(0, data["vehicle_capacities"][v])
        capacity_dimension.CumulVar(end).SetRange(0, 0)
    for i in range(routing.Size()):
        capacity_dimension.CumulVar(i).SetRange(0, max(data["vehicle_capacities"]))

    # Callback "Time"
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        velocity = AVG_VELOCITY
        service_time = (0 if from_node == data["depot"] else 1) * TIME_SCALE
        travel_time = data["distance_matrix"][from_node][to_node] / velocity * TIME_SCALE
        return int(travel_time + service_time)

    transit_time_callback_index = routing.RegisterTransitCallback(time_callback)

    routing.AddDimension(
        transit_time_callback_index,
        MAX_WAITING_TIME,
        MAX_TRAVEL_TIME,
        False,
        "Time",
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    # # Áp dụng time windows cho các node (khách hàng)
    # for idx, window in enumerate(data["time_windows"]):
    #     index = manager.NodeToIndex(idx)
    #     time_dimension.CumulVar(index).SetRange(window[0], window[1])

    # Áp dụng thời gian rảnh của tài xế cho mỗi xe (chọn khoảng đầu tiên)
    # for vehicle_id in range(data["num_vehicles"]):
    #     start_index = routing.Start(vehicle_id)
    #     end_index = routing.End(vehicle_id)
    #     available_times = data["available_times_s"][vehicle_id]  # Danh sách khoảng rảnh
    #     # Chọn khoảng thời gian rảnh đầu tiên (hoặc logic chọn khác)
    #     start_time, end_time = available_times[0]  # Chỉ lấy khoảng đầu tiên
    #     time_dimension.CumulVar(start_index).SetRange(start_time, end_time)
    #     time_dimension.CumulVar(end_index).SetRange(start_time, end_time)
    
    print(f'engine1.py:create_daily_routing_model:len(data["distance_matrix"]_end): {len(data["distance_matrix"])}')

    return routing, manager, capacity_dimension, time_dimension

def solve_daily_routing(data, historical_km, lambda_penalty, mu_penalty):
    """
    Giải định tuyến cho ngày hôm đó:
    - historical_km: danh sách số km tích lũy hiện tại của từng xe.
    - lambda_penalty: hệ số điều chỉnh fixed cost theo historical_km.
    - mu_penalty: hệ số điều chỉnh fixed cost theo chênh lệch tải trọng.
    Sau khi giải, trả về daily_distances của từng xe.
    """
    # print(f"solve_daily_routing:data: {data}")
    print(f'solve_daily_routing:len(data["distance_matrix"]): {len(data["distance_matrix"])}')

    def tinh_trung_binh_co_ban(danh_sach_so):
        """Tính trung bình cộng sử dụng sum() và len()."""
        print(f"tinh_trung_binh_co_ban:")
        if not danh_sach_so:
            return None
        return sum(danh_sach_so) / len(danh_sach_so)

    (
        routing,
        manager,
        capacity_dimension,
        time_dimension,
    ) = create_daily_routing_model(data)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = search_strategy
    search_parameters.log_search = True

    # Tính min_capacity để điều chỉnh fixed cost theo tải trọng.
    min_capacity = min(data["vehicle_capacities"])
    avg_capacity = tinh_trung_binh_co_ban(data["vehicle_capacities"])
    # Gán fixed cost cho từng xe theo historical_km và tải trọng.
    # print(data['num_vehicles'],"#"*10,historical_km)
    for v in range(data["num_vehicles"]):
        fixed_cost = int(
            lambda_penalty * historical_km[v]
            + mu_penalty * (data["vehicle_capacities"][v] - 0)
        )
        routing.SetFixedCostOfVehicle(fixed_cost, v)
    print(f"routing.Solve:")
    solution = routing.SolveWithParameters(search_parameters)
    print(f"finish")
    if not solution:
        print("Không tìm thấy lời giải cho ngày này!")
        return None, None, None, None

    # Tính tổng quãng đường của mỗi xe từ dimension "Distance"
    daily_distances = []
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route_distance = 0
        while not routing.IsEnd(index):
            from_node = manager.IndexToNode(index)
            next_index = solution.Value(routing.NextVar(index))
            if next_index>=20: 
                print(f"next_index:{next_index}")
                exit()
            to_node = manager.IndexToNode(next_index)
            route_distance = math.ceil(max(route_distance,data["distance_matrix"][from_node][to_node],data["distance_matrix"][to_node][from_node],data["distance_matrix"][0][to_node]))
            index = next_index
        daily_distances.append(route_distance)

    return solution, manager, daily_distances, routing


def print_daily_solution(data, manager, routing, solution):
    """
    In kết quả định tuyến của ngày:
    - Chỉ in những route có tổng khoảng cách > 0
    - Cho mỗi xe, in thứ tự các node với:
        • Arrival Time (cumulative 'Time')
        • Capacity (số hàng còn lại trên xe)
        • Delivered: được tính là (capacity tại node hiện tại - capacity tại node kế) nếu node không phải depot; với depot Delivered = 0.
    - In tổng khoảng cách của từng xe.
    """
    time_dimension = routing.GetDimensionOrDie("Time")
    capacity_dimension = routing.GetDimensionOrDie("Capacity")
    total_distance = 0
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        route_distance = 0
        output = f"Route for vehicle {v}:\n"
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival = solution.Value(time_dimension.CumulVar(index))
            current_cap = solution.Value(capacity_dimension.CumulVar(index))
            next_index = solution.Value(routing.NextVar(index))
            if next_index>=20: 
                print(f"next_index:{next_index}")
                exit()
            delivered = 0
            if node != data["depot"]:
                delivered = current_cap - solution.Value(
                    capacity_dimension.CumulVar(next_index)
                )
            output += f" Node {node} (Arrival Time: {arrival}, Capacity: {current_cap}, Delivered: {delivered}) ->"
            prev = index
            index = next_index
            route_distance += float(data["distance_matrix"][manager.IndexToNode(prev)][
                manager.IndexToNode(index)
            ])
        node = manager.IndexToNode(index)
        arrival = solution.Value(time_dimension.CumulVar(index))
        final_cap = solution.Value(capacity_dimension.CumulVar(index))
        output += f" Node {node} (Arrival Time: {arrival}, Capacity: {final_cap}, Delivered: 0)\n"
        output += f"Distance of the route: {route_distance}\n"
        
        if route_distance > 0:
            print(output)
            total_distance += route_distance
    print(f"Total distance of all routes: {total_distance}")


# ------------------------------
# Phần "multi-day": lặp qua nhiều ngày với cập nhật historical_km và ưu tiên theo fixed cost

def multi_day_routing_real_ready_to_deploy(num_days, lambda_penalty, mu_penalty):
    """
    Giả sử bạn có danh sách historical_km ban đầu cho từng xe (ví dụ với 4 xe).
    Sau mỗi ngày, cập nhật historical_km bằng cách cộng thêm quãng đường của ngày đó.
    Fixed cost của từng xe được tính theo:
         fixed_cost = lambda_penalty * historical_km + mu_penalty * (vehicle_capacities - min_capacity)
    Điều này giúp ưu tiên xe có số km tích lũy thấp và có tải trọng nhỏ hơn.
    """
    # Khởi tạo historical_km cho NUM_OF_VEHICLE xe (trong thực tế có thể là 47 xe)
    historical_km = None
    list_of_seed = []
    historical_km_by_day = []
    for day in DATES:
        print(f"\n--- Day {day} ---")
        seed = random.randint(10, 1000)
        list_of_seed.append(seed)
        distance_matrix, demands, vehicle_capacities, time_windows, available_times_s = load_data_real(
            day=day
        )
        if not historical_km:
            historical_km = [0 for _ in range(NUM_OF_VEHICLES)]
        data = create_data_model(
            distance_matrix=distance_matrix,
            demands=demands,
            vehicles=vehicle_capacities,
            time_window=time_windows,
            available_times_s=available_times_s,
        )
        print(f'engine1.py:multi_day_routing_real_ready_to_deploy:len(data["distance_matrix"]): {len(data["distance_matrix"])}')

        solution, manager, daily_distances, routing = solve_daily_routing(
            data, historical_km, lambda_penalty, mu_penalty
        )
        if solution is None:
            print("Không tìm được lời giải cho ngày này.")
            continue
        print_daily_solution(data, manager, routing, solution)
        # Cập nhật historical_km cho từng xe
        historical_km_by_day.append(daily_distances)
        for v in range(data["num_vehicles"]):
            historical_km[v] += daily_distances[v]
        print("Updated historical km:", historical_km)
    print(list_of_seed)
    return historical_km,historical_km_by_day



if __name__ == "__main__":
    if IS_TESTING:
        # gen map
        generator.gen_map(NUM_OF_NODES=NUM_OF_NODES, seed=42)
        # gen vehicle
        generator.gen_list_vehicle(NUM_OF_VEHICLES=NUM_OF_VEHICLES, seed=42)

        # run main algorithm
        historical_km,historical_km_by_day = multi_day_routing_gen_request(
            num_days=NUM_OF_DAY_REPETION, lambda_penalty=LAMBDA, mu_penalty=MU
        )  # [1638, 1577, 1567, 2201, 2136]
    else:
        # run main algorithm
        historical_km,historical_km_by_day = multi_day_routing_real_ready_to_deploy(
            num_days=NUM_OF_DAY_REPETION, lambda_penalty=LAMBDA, mu_penalty=MU
        )
    "#####################################################################"
    with open("data/accummulated_distance.csv", 'w', newline='') as file:
        writer = csv.writer(file)
        # Optionally, add a header row (uncomment if needed)
        # writer.writerow(["Entity1_km", "Entity2_km"])
        # Write all rows of the 2D list
        writer.writerows(historical_km_by_day)

    print(
        f"max km: {max(historical_km)}, mim km: {min(historical_km)}, sum km: {sum(historical_km)}"
    )
    import sys

    # ffile = open("trollC=.txt","a")
    # print(config, file=ffile)
    from datetime import datetime, timedelta

    config["RUNTIME"] = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    print(config, file=sys.stderr)
