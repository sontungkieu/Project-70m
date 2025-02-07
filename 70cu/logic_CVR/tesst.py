from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# ------------------------------
# Phần "daily": tạo dữ liệu và mô hình định tuyến cho một ngày giao hàng


def create_daily_data_model():
    """
    Tạo dữ liệu cho một ngày giao hàng với split delivery.
    Ví dụ:
    - 7 node:
         • 0: depot
         • 1: khách hàng 1a (5 đơn vị)
         • 2: khách hàng 1b (3 đơn vị) -> tổng khách hàng 1 = 8 đơn vị (split)
         • 3: khách hàng 2 (1 đơn vị)
         • 4: khách hàng 3 (2 đơn vị)
         • 5: khách hàng 4a (5 đơn vị)
         • 6: khách hàng 4b (1 đơn vị) -> tổng khách hàng 4 = 6 đơn vị (split)
    - Ma trận khoảng cách: khoảng cách giữa các node của cùng khách hàng bằng 0.
    - demand: như mô tả ở trên.
    - vehicle_capacities: ví dụ sử dụng 4 xe với tải trọng như mẫu.
    - time_windows: đặt mẫu cho depot và các khách hàng.
    """
    data = {}
    data['distance_matrix'] = [
        # 0   1   2   3   4   5   6
        [0,  8,  8,  5,  5, 10, 10],  # 0: depot
        [8,  0,  0,  6,  6,  4,  4],   # 1: khách hàng 1a
        [8,  0,  0,  6,  6,  4,  4],   # 2: khách hàng 1b
        [5,  6,  6,  0,  3,  8,  8],   # 3: khách hàng 2
        [5,  6,  6,  3,  0,  8,  8],   # 4: khách hàng 3
        [10, 4,  4,  8,  8,  0,  0],   # 5: khách hàng 4a
        [10, 4,  4,  8,  8,  0,  0],   # 6: khách hàng 4b
    ]
    # demand: depot = 0; khách hàng 1: 5, 3; khách hàng 2: 1; khách hàng 3: 2; khách hàng 4: 5, 1.
    data['demands'] = [0, 5, 5, 2, 2, 5, 5]
    # Ví dụ: 4 xe, với xe 0 có capacity 10 (để phục vụ tổng demand 8 của khách hàng 1, cộng với các xe khác phục vụ các đơn khác).
    data['vehicle_capacities'] = [24, 12, 10, 9]
    data['num_vehicles'] = 4
    data['depot'] = 0
    # Time windows:
    # depot: (0,30), khách hàng 1: (0,20), khách hàng 2: (0,15), khách hàng 3: (0,15), khách hàng 4: (0,30)
    data['time_windows'] = [
        (0, 30),   # depot
        (0, 20),   # khách hàng 1a
        (0, 20),   # khách hàng 1b
        (0, 15),   # khách hàng 2
        (0, 15),   # khách hàng 3
        (0, 30),   # khách hàng 4a
        (0, 30),   # khách hàng 4b
    ]
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
        1000,    # horizon đủ lớn cho bài toán
        True,    # fix_start_cumul_to_zero = True, để bắt đầu từ 0
        "Distance"
    )
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(10)

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
    Giải định tuyến cho ngày hôm đó:
    - historical_km: danh sách số km tích lũy hiện tại của từng xe.
    - lambda_penalty: hệ số điều chỉnh fixed cost theo historical_km.
    Sau khi giải, cập nhật daily distances.
    """
    routing, manager, capacity_dimension, time_dimension = create_daily_routing_model(
        data)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    # Gán fixed cost cho từng xe theo historical_km để ưu tiên xe có số km thấp hơn.
    for v in range(data['num_vehicles']):
        fixed_cost = int(lambda_penalty * historical_km[v])
        routing.SetFixedCostOfVehicle(fixed_cost, v)

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        print("Không tìm thấy lời giải cho ngày này!")
        return None, None, None, None

    # Tính tổng quãng đường của mỗi xe từ dimension "Distance"
    daily_distances = []
    distance_dimension = routing.GetDimensionOrDie("Distance")
    for v in range(data['num_vehicles']):
        end_index = routing.End(v)
        distance = solution.Value(distance_dimension.CumulVar(end_index))
        daily_distances.append(distance)
    return solution, manager, daily_distances, routing


def print_daily_solution(data, manager, routing, solution):
    """
    In kết quả định tuyến của ngày:
    - Cho mỗi xe, in thứ tự các node với:
        • Arrival Time (cumulative 'Time')
        • Capacity (số hàng còn lại trên xe)
        • Delivered: được tính bằng hiệu số giữa load tại node hiện tại và node kế (với depot luôn Delivered = 0).
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
            # Tính số hàng giao tại node này nếu không phải depot:
            # delivered = current capacity - capacity tại node kế
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


def multi_day_routing(num_days, lambda_penalty):
    """
    Giả sử bạn có danh sách historical_km ban đầu cho từng xe (ví dụ với 4 xe).
    Sau mỗi ngày, cập nhật historical_km bằng cách cộng thêm quãng đường của ngày đó.
    Fixed cost của từng xe được tính theo: fixed_cost = lambda_penalty * historical_km.
    Điều này giúp ưu tiên xe có số km tích lũy thấp cho ngày hôm sau.
    """
    # Khởi tạo historical_km cho 4 xe (trong thực tế có thể là 47 xe)
    historical_km = [0 for _ in range(4)]
    for day in range(num_days):
        print(f"\n--- Day {day+1} ---")
        # Trong thực tế, dữ liệu có thể khác mỗi ngày.
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
    # Ví dụ: chạy cho 3 ngày, với lambda_penalty = 10 (điều chỉnh dựa trên dữ liệu thực tế)
    multi_day_routing(num_days=30, lambda_penalty=1000)
