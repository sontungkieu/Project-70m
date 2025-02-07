from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# ------------------------------
# Phần "daily" – dữ liệu đơn hàng và mô hình định tuyến của một ngày
# (Mẫu này dựa trên code bạn cung cấp với split delivery, nhiều depot,…)


def create_daily_data_model():
    """
    Tạo dữ liệu cho một ngày giao hàng.
    Trong ví dụ này, ta sử dụng dữ liệu mẫu với 7 node như trong code bạn đưa ra.
    (Trong thực tế, bạn có thể load đơn hàng của ngày hôm đó, tiền xử lý tách đơn nếu cần, 
     phân loại theo depot,...)
    """
    data = {}
    # 7 node: 0: depot, 1-2: khách hàng 1 (split), 3: khách hàng 2, 4: khách hàng 3, 5-6: khách hàng 4 (split)
    data['distance_matrix'] = [
        # 0   1   2   3   4   5   6
        [0,  8,  8,  5,  5, 10, 10],  # 0: depot
        [8,  0,  0,  6,  6,  4,  4],  # 1: khách hàng 1a
        [8,  0,  0,  6,  6,  4,  4],  # 2: khách hàng 1b
        [5,  6,  6,  0,  3,  8,  8],  # 3: khách hàng 2
        [5,  6,  6,  3,  0,  8,  8],  # 4: khách hàng 3
        [10, 4,  4,  8,  8,  0,  0],  # 5: khách hàng 4a
        [10, 4,  4,  8,  8,  0,  0],  # 6: khách hàng 4b
    ]
    # demand: 0 cho depot, split orders như sau:
    # khách hàng 1: 8 đơn vị → node1:5, node2:3; khách hàng 2: 1 đơn vị; khách hàng 3: 2 đơn vị; khách hàng 4: 6 đơn vị → node5:5, node6:1.
    data['demands'] = [0, 5, 3, 1, 2, 5, 1]

    # Giả sử hôm nay có 4 xe với tải trọng như mẫu (ở đây xe không nhất thiết phải full load nếu tổng demand của các node giao là nhỏ hơn)
    data['vehicle_capacities'] = [10, 5, 5, 5]
    data['num_vehicles'] = 4
    data['depot'] = 0

    # Time windows: đặt mẫu theo yêu cầu (ở đây đơn giản)
    data['time_windows'] = [
        (0, 30),    # depot
        (0, 20),    # khách hàng 1a
        (0, 20),    # khách hàng 1b
        (0, 15),    # khách hàng 2
        (0, 15),    # khách hàng 3
        (0, 30),    # khách hàng 4a
        (0, 30),    # khách hàng 4b
    ]
    return data


def create_daily_routing_model(data):
    # Tạo RoutingIndexManager và RoutingModel cho dữ liệu ngày hôm đó
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'],
                                           data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    # Callback khoảng cách
    def distance_callback(from_index, to_index):
        return data['distance_matrix'][manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Dimension "Distance" để tính tổng quãng đường và dùng để tối ưu giảm maximum route distance.
    routing.AddDimension(
        transit_callback_index,
        0, 1000, True, "Distance"
    )
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(10000)

    # Callback demand cho "Capacity": trả về 0 cho depot, -demand cho khách hàng.
    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        return 0 if node == data['depot'] else -data['demands'][node]
    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        data['vehicle_capacities'],
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

    # Callback "Time" – sử dụng khoảng cách (chia theo vận tốc) và service time (ví dụ: 1 đơn vị với khách hàng, 0 với depot)
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        velocity = 2
        service_time = 0 if from_node == data['depot'] else 1
        travel_time = data['distance_matrix'][from_node][to_node] / velocity
        return int(travel_time + service_time)
    transit_time_callback_index = routing.RegisterTransitCallback(
        time_callback)
    waiting_time = 5
    horizon = 30
    routing.AddDimension(
        transit_time_callback_index,
        waiting_time,
        horizon,
        True,   # fix_start_cumul_to_zero = True
        'Time'
    )
    time_dimension = routing.GetDimensionOrDie('Time')
    for idx, window in enumerate(data['time_windows']):
        index = manager.NodeToIndex(idx)
        time_dimension.CumulVar(index).SetRange(window[0], window[1])
    return routing, manager, capacity_dimension, time_dimension


def solve_daily_routing(data, historical_km, lambda_penalty):
    """
    Giải định tuyến cho ngày hôm đó với dữ liệu data, và cập nhật ưu tiên theo historical_km.
    historical_km là danh sách số km tích lũy hiện tại của mỗi xe.
    lambda_penalty là hệ số để tính fixed cost của xe.
    """
    routing, manager, capacity_dimension, time_dimension = create_daily_routing_model(
        data)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    # Gán fixed cost cho từng xe dựa trên historical_km (điều chỉnh để ưu tiên xe ít km hơn)
    for v in range(data['num_vehicles']):
        fixed_cost = int(lambda_penalty * historical_km[v])
        routing.SetFixedCostOfVehicle(fixed_cost, v)

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        print("Không tìm thấy lời giải cho ngày này!")
        return None, None, None, None

    # Tính tổng quãng đường của mỗi xe (từ dimension Distance) để cập nhật historical_km
    daily_distances = []
    for v in range(data['num_vehicles']):
        end_index = routing.End(v)
        distance = solution.Value(
            routing.GetDimensionOrDie("Distance").CumulVar(end_index))
        daily_distances.append(distance)
    return solution, manager, daily_distances, routing


def print_daily_solution(data, manager, routing, solution):
    """In kết quả của ngày (định tuyến, thời gian, capacity, …)"""
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
            cap = solution.Value(capacity_dimension.CumulVar(index))
            output += f" Node {node} (Arrival: {arrival}, Capacity: {cap}) ->"
            previous = index
            index = solution.Value(routing.NextVar(index))
            route_distance += data['distance_matrix'][manager.IndexToNode(
                previous)][manager.IndexToNode(index)]
        node = manager.IndexToNode(index)
        arrival = solution.Value(time_dimension.CumulVar(index))
        cap = solution.Value(capacity_dimension.CumulVar(index))
        output += f" Node {node} (Arrival: {arrival}, Capacity: {cap})\n"
        output += f"Distance of the route: {route_distance}\n"
        print(output)
        total_distance += route_distance
    print(f"Total distance of all routes: {total_distance}")

# ------------------------------
# Phần "multi-day": vòng lặp qua nhiều ngày


def multi_day_routing(num_days, lambda_penalty):
    """
    Giả sử bạn có danh sách historical_km ban đầu cho từng xe (ví dụ, 47 xe),
    ở đây dùng số nhỏ cho ví dụ (với 4 xe) – trong thực tế, danh sách này sẽ có kích thước = số xe.
    Sau mỗi ngày, ta cập nhật historical_km bằng cách cộng thêm quãng đường của ngày đó.
    """
    # Ví dụ khởi tạo historical_km cho 4 xe (bạn có thể mở rộng cho 47 xe)
    historical_km = [0 for _ in range(4)]
    # Giả sử mỗi ngày đơn hàng là như mẫu từ create_daily_data_model()
    for day in range(num_days):
        print(f"\n--- Day {day+1} ---")
        # Trong thực tế, load dữ liệu đơn hàng của ngày đó
        data = create_daily_data_model()
        solution, manager, daily_distances, routing = solve_daily_routing(
            data, historical_km, lambda_penalty)
        if solution is None:
            print("Không tìm được lời giải cho ngày này.")
            continue
        print_daily_solution(data, manager, routing, solution)
        # Cập nhật historical_km cho từng xe
        for v in range(data['num_vehicles']):
            historical_km[v] += daily_distances[v]
        print("Updated historical km:", historical_km)


if __name__ == '__main__':
    # Sử dụng lambda_penalty = 10 (điều chỉnh dựa trên dữ liệu thực tế) và giải lịch cho 3 ngày
    multi_day_routing(num_days=3, lambda_penalty=10)
