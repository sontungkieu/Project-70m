from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from utilities.split_data import split_customers
# vehicle capacity phải là số nguyên
# chuyển hết sang đơn vị (0.1m3)
# xe 9.7 m3 thành 97 0.1m3
from config import *
from objects.driver import Driver
from objects.request import Request
import utilities.load_requests as load_requests

search_strategy = [routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
                   routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
                   routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
                   routing_enums_pb2.FirstSolutionStrategy.SAVINGS,][SEARCH_STRATEGY]

# ------------------------------
# Phần "daily": tạo dữ liệu và mô hình định tuyến cho một ngày giao hàng


def load_data(distance_file='data/distance.json', request_file='data/requests.json', vehicle_file='data/vehicle.json'):
    import json
    global NUM_OF_VEHICLES, NUM_OF_NODES

    # Đọc distance matrix từ JSON
    with open(distance_file, 'r', encoding='utf-8') as f:
        distance_matrix = json.load(f)

    distance_matrix = [[int(u * DISTANCE_SCALE) for u in v]
                       for v in distance_matrix]
    NUM_OF_NODES = len(distance_matrix)

    # Đọc danh sách vehicle từ JSON
    with open(vehicle_file, 'r', encoding='utf-8') as f:
        vehicle_capacities = json.load(f)

    vehicle_capacities = [int(u * CAPACITY_SCALE) for u in vehicle_capacities]
    NUM_OF_VEHICLES = len(vehicle_capacities)

    # Đọc danh sách requests từ JSON
    requests_data = load_requests.load_requests(request_file)
    print(f"requests_data: {requests_data}")
    # exit(0)

    demands = [0 for _ in range(NUM_OF_NODES)]
    time_windows = [(0, 24 * TIME_SCALE) for _ in range(NUM_OF_NODES)]


    for request in requests_data:
        print(f"request: {request}")
        # Truy xuất phần tử đầu tiên trong danh sách
        end_place = request.end_place[0]
        weight = request.weight
        demands[end_place] += int(weight * 10)
        time_windows[end_place] = (request.timeframe[0],request.timeframe[1])

    print(f"demands: {demands}")
    # exit()
    return distance_matrix, demands, vehicle_capacities, time_windows


def create_data_model(*, distance_matrix=None, demands=None, vehicles=None, time_window=None):
    """Tạo dữ liệu cho bài toán giao hàng với split delivery.

    Trong bài toán này:
    - Một khách hàng nếu có nhu cầu vượt quá tải trọng của xe (ở đây là 5 đơn vị)
      sẽ được chia thành nhiều node riêng biệt.
    - Ví dụ:
         • Khách hàng 1 có đơn hàng 8 đơn vị sẽ chia thành 2 node: 1a (5 đơn vị) và 1b (3 đơn vị).
         • Khách hàng 4 có đơn hàng 6 đơn vị sẽ chia thành 2 node: 4a (5 đơn vị) và 4b (1 đơn vị).
    - Các node này đều có cùng vị trí (vì cùng là của khách hàng đó) nên khoảng cách giữa chúng bằng 0.
    """

    global NUM_OF_VEHICLES

    data = {}
    
    data['distance_matrix'] =  DEFAULT_DISTANCE_MATRIX if not distance_matrix else distance_matrix
    
    data['demands'] = DEFAULT_DEMANDS if not demands else demands

    # Với trọng tải của xe là 5 đơn vị, những node với demand <= 5 đảm bảo không vượt quá.
    # Tổng demand của các khách hàng là 5+3+1+2+5+1 = 17, nên sử dụng 4 xe với tải trọng 5 (tổng tải = 20).
    data['vehicle_capacities'] = DEFAULT_VEHICLE_CAPACITIES if not vehicles else vehicles

    data['num_vehicles'] = 4 if not vehicles else len(vehicles)
    NUM_OF_VEHICLES = data['num_vehicles']
    data['depot'] = 0


    data['time_windows'] = DEFAULT_TIME_WINDOWS if time_window == None else time_window

    data, node_mapping = split_customers(data)

    print(f"node_mapping: {node_mapping}")

    return data


def create_daily_routing_model(data):
    """
    Tạo RoutingIndexManager và RoutingModel cho dữ liệu của một ngày.
    Thiết lập các callback và dimensions cho Distance, Capacity và Time.
    """
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'],
                                           data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    # Callback khoảng cách
    def distance_callback(from_index, to_index):
        return data['distance_matrix'][manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Dimension "Distance" để tính tổng quãng đường và tối ưu giảm maximum route distance.
    routing.AddDimension(
        transit_callback_index,
        0,       # không cho phép slack
        MAX_TRAVEL_DISTANCE,    # horizon đủ lớn cho bài toán
        True,    # fix_start_cumul_to_zero = True, để bắt đầu từ 0
        "Distance"
    )
    distance_dimension = routing.GetDimensionOrDie("Distance")

    distance_dimension.SetGlobalSpanCostCoefficient(GLOBAL_SPAN_COST_COEFFICIENT)

    def stops_callback(from_index, to_index):
        return 1
    stops_callback_index = routing.RegisterTransitCallback(stops_callback)
    routing.AddDimension(
        stops_callback_index,
        0,       # không có slack
        MAX_ROUTE_SIZE,       # tối đa 5 node (bao gồm depot và node kết thúc)
        True,    # bắt đầu từ 0
        "Stops"
    )
    stops_dimension = routing.GetDimensionOrDie("Stops")

    # Callback demand cho "Capacity"
    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        return 0 if node == data['depot'] else -data['demands'][node]
    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # slack = 0
        data['vehicle_capacities'],
        # fix_start_cumul_to_zero = False (xe load được tự chọn phù hợp)
        False,
        'Capacity'
    )
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    for v in range(data['num_vehicles']):
        start = routing.Start(v)
        end = routing.End(v)
        capacity_dimension.CumulVar(start).SetRange(
            0, data['vehicle_capacities'][v])
        capacity_dimension.CumulVar(end).SetRange(0, 0)
    for i in range(routing.Size()):
        capacity_dimension.CumulVar(i).SetRange(
            0, max(data['vehicle_capacities']))

    # Callback "Time" – sử dụng khoảng cách chia theo vận tốc và service time.
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        velocity = AVG_VELOCITY
        service_time = 0 if from_node == data['depot'] else 1
        travel_time = data['distance_matrix'][from_node][to_node] / velocity
        return int(travel_time + service_time)
    transit_time_callback_index = routing.RegisterTransitCallback(
        time_callback)

    routing.AddDimension(
        transit_time_callback_index,
        MAX_WAITING_TIME,
        MAX_TRAVEL_TIME,
        False,   # fix_start_cumul_to_zero = True
        'Time'
    )
    time_dimension = routing.GetDimensionOrDie('Time')
    for idx, window in enumerate(data['time_windows']):
        index = manager.NodeToIndex(idx)
        time_dimension.CumulVar(index).SetRange(window[0], window[1])
    return routing, manager, capacity_dimension, time_dimension


def solve_daily_routing(data, historical_km, lambda_penalty, mu_penalty):
    """
    Giải định tuyến cho ngày hôm đó:
    - historical_km: danh sách số km tích lũy hiện tại của từng xe.
    - lambda_penalty: hệ số điều chỉnh fixed cost theo historical_km.
    - mu_penalty: hệ số điều chỉnh fixed cost theo chênh lệch tải trọng.
    Sau khi giải, trả về daily_distances của từng xe.
    """
    def tinh_trung_binh_co_ban(danh_sach_so):
        """Tính trung bình cộng sử dụng sum() và len()."""
        if not danh_sach_so:
            return None
        return sum(danh_sach_so) / len(danh_sach_so)

    routing, manager, capacity_dimension, time_dimension = create_daily_routing_model(
        data)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = search_strategy

    # Tính min_capacity để điều chỉnh fixed cost theo tải trọng.
    min_capacity = min(data['vehicle_capacities'])
    avg_capacity = tinh_trung_binh_co_ban(data['vehicle_capacities'])
    # Gán fixed cost cho từng xe theo historical_km và tải trọng.
    # print(data['num_vehicles'],"#"*10,historical_km)
    for v in range(data['num_vehicles']):
        fixed_cost = int(lambda_penalty * historical_km[v] + mu_penalty * (
            data['vehicle_capacities'][v] - 0))
        routing.SetFixedCostOfVehicle(fixed_cost, v)

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        print("Không tìm thấy lời giải cho ngày này!")
        return None, None, None, None

    # Tính tổng quãng đường của mỗi xe từ dimension "Distance"
    daily_distances = []
    distance_dimension = routing.GetDimensionOrDie("Distance")
    for v in range(data['num_vehicles']):
        # Bắt đầu từ depot
        index = routing.Start(v)
        max_distance = 0
        # Duyệt qua toàn bộ các node trên lộ trình của xe
        while not routing.IsEnd(index):
            current_distance = solution.Value(
                distance_dimension.CumulVar(index))
            max_distance = max(max_distance, current_distance)
            index = solution.Value(routing.NextVar(index))
        # Sau khi duyệt hết lộ trình, max_distance là khoảng cách xa nhất từ depot
        daily_distances.append(max_distance)

    return solution, manager, daily_distances, routing


def print_daily_solution(data, manager, routing, solution):
    """
    In kết quả định tuyến của ngày:
    - Cho mỗi xe, in thứ tự các node với:
        • Arrival Time (cumulative 'Time')
        • Capacity (số hàng còn lại trên xe)
        • Delivered: được tính là (capacity tại node hiện tại - capacity tại node kế) nếu node không phải depot; với depot Delivered = 0.
    - In tổng khoảng cách của từng xe.

    Ví dụ mẫu:
      Route for vehicle 0:
       Node 0 (Arrival Time: 0, Capacity: 10, Delivered: 0) -> Node 1 (Arrival Time: 4, Capacity: 10, Delivered: 5) -> Node 5 (Arrival Time: 6, Capacity: 5, Delivered: 5) -> Node 0 (Arrival Time: 11, Capacity: 0, Delivered: 0)
       Distance of the route: 19
    """
    time_dimension = routing.GetDimensionOrDie('Time')
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    total_distance = 0
    for v in range(data['num_vehicles']):
        index = routing.Start(v)
        route_distance = 0
        output = f"Route for vehicle {v}:\n"
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival = solution.Value(time_dimension.CumulVar(index))
            current_cap = solution.Value(capacity_dimension.CumulVar(index))
            next_index = solution.Value(routing.NextVar(index))
            delivered = 0
            if node != data['depot']:
                delivered = current_cap - \
                    solution.Value(capacity_dimension.CumulVar(next_index))
            output += f" Node {node} (Arrival Time: {arrival}, Capacity: {current_cap}, Delivered: {delivered}) ->"
            prev = index
            index = next_index
            route_distance += data['distance_matrix'][manager.IndexToNode(
                prev)][manager.IndexToNode(index)]
        node = manager.IndexToNode(index)
        arrival = solution.Value(time_dimension.CumulVar(index))
        final_cap = solution.Value(capacity_dimension.CumulVar(index))
        output += f" Node {node} (Arrival Time: {arrival}, Capacity: {final_cap}, Delivered: 0)\n"
        output += f"Distance of the route: {route_distance}\n"
        print(output)
        total_distance += route_distance
    print(f"Total distance of all routes: {total_distance}")

# ------------------------------
# Phần "multi-day": lặp qua nhiều ngày với cập nhật historical_km và ưu tiên theo fixed cost


def multi_day_routing(num_days, lambda_penalty, mu_penalty):
    """
    Giả sử bạn có danh sách historical_km ban đầu cho từng xe (ví dụ với 4 xe).
    Sau mỗi ngày, cập nhật historical_km bằng cách cộng thêm quãng đường của ngày đó.
    Fixed cost của từng xe được tính theo: 
         fixed_cost = lambda_penalty * historical_km + mu_penalty * (vehicle_capacities - min_capacity)
    Điều này giúp ưu tiên xe có số km tích lũy thấp và có tải trọng nhỏ hơn.
    """
    # Khởi tạo historical_km cho 4 xe (trong thực tế có thể là 47 xe)
    historical_km = None
    for day in range(num_days):
        print(f"\n--- Day {day+1} ---")
        # Trong thực tế, dữ liệu đơn hàng có thể khác mỗi ngày.
        # data = create_daily_data_model()
        data = create_data_model()
        if not historical_km:
            historical_km = [0 for _ in range(NUM_OF_VEHICLES)]
        solution, manager, daily_distances, routing = solve_daily_routing(
            data, historical_km, lambda_penalty, mu_penalty)
        if solution is None:
            print("Không tìm được lời giải cho ngày này.")
            continue
        print_daily_solution(data, manager, routing, solution)
        # Cập nhật historical_km cho từng xe
        for v in range(data['num_vehicles']):
            historical_km[v] += daily_distances[v]
        print("Updated historical km:", historical_km)


def multi_day_routing_gen_request(num_days, lambda_penalty, mu_penalty):
    """
    Giả sử bạn có danh sách historical_km ban đầu cho từng xe (ví dụ với 4 xe).
    Sau mỗi ngày, cập nhật historical_km bằng cách cộng thêm quãng đường của ngày đó.
    Fixed cost của từng xe được tính theo: 
         fixed_cost = lambda_penalty * historical_km + mu_penalty * (vehicle_capacities - min_capacity)
    Điều này giúp ưu tiên xe có số km tích lũy thấp và có tải trọng nhỏ hơn.
    """
    # Khởi tạo historical_km cho 4 xe (trong thực tế có thể là 47 xe)
    historical_km = None
    list_of_seed = []
    for day in range(num_days):
        print(f"\n--- Day {day+1} ---")

        import utilities.generator as generator
        import random
        seed = random.randint(10, 1000)
        list_of_seed.append(seed)
        generator.gen_requests_and_save(NUM_OF_REQUEST_PER_DAY, file_sufices=str(
            day), NUM_OF_NODES=NUM_OF_NODES, seed=seed)
        distance_matrix, demands, vehicle_capacities, time_windows = load_data(
            request_file=f"data/requests{day}.json")
        if not historical_km:
            historical_km = [0 for _ in range(NUM_OF_VEHICLES)]
        # Trong thực tế, dữ liệu đơn hàng có thể khác mỗi ngày.
        # data = create_daily_data_model()
        data = create_data_model(distance_matrix=distance_matrix, demands=demands,
                                 vehicles=vehicle_capacities, time_window=time_windows)
        solution, manager, daily_distances, routing = solve_daily_routing(
            data, historical_km, lambda_penalty, mu_penalty)
        if solution is None:
            print("Không tìm được lời giải cho ngày này.")
            continue
        print_daily_solution(data, manager, routing, solution)
        # Cập nhật historical_km cho từng xe
        for v in range(data['num_vehicles']):
            historical_km[v] += daily_distances[v]
        print("Updated historical km:", historical_km)
    print(list_of_seed)
    return historical_km

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
    for day in range(num_days):
        print(f"\n--- Day {day+1} ---")
        # Cập nhật số se available tại mỗi ngày
        import utilities.update_list_vehicle as update_list_vehicle
        # Load request từ file
        import utilities.load_requests as load_requests
        # Tạo bản đồ từ request
        import utilities.update_map as update_map


        # Trong thực tế, dữ liệu đơn hàng có thể khác mỗi ngày.
        data = create_data_model()
        if not historical_km:
            historical_km = [0 for _ in range(NUM_OF_VEHICLES)]
        solution, manager, daily_distances, routing = solve_daily_routing(
            data, historical_km, lambda_penalty, mu_penalty)
        if solution is None:
            print("Không tìm được lời giải cho ngày này.")
            continue
        print_daily_solution(data, manager, routing, solution)
        # Cập nhật historical_km cho từng xe
        for v in range(data['num_vehicles']):
            historical_km[v] += daily_distances[v]
        print("Updated historical km:", historical_km)

    return historical_km

if __name__ == '__main__':
    # test = False
    # multi_day_routing_real_ready_to_deploy(
    #     num_days=NUM_OF_DAY_REPETION, lambda_penalty=LAMBDA, mu_penalty=MU)
    # test = true
    "#####################################################################"
    import utilities.generator as generator
    # gen map
    generator.gen_map(NUM_OF_NODES=NUM_OF_NODES, seed=42)
    # gen vehicle
    generator.gen_list_vehicle(NUM_OF_VEHICLES=NUM_OF_VEHICLES, seed=42)


    historical_km = multi_day_routing_gen_request(
        num_days=NUM_OF_DAY_REPETION, lambda_penalty=LAMBDA, mu_penalty=MU)  # [1638, 1577, 1567, 2201, 2136]
    print(
        f"max km: {max(historical_km)}, mim km: {min(historical_km)}, sum km: {sum(historical_km)}")
    import sys
    # ffile = open("trollC=.txt","a")
    # print(config, file=ffile)
    print(config, file=sys.stderr)
