from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def create_data_model():
    """Tạo dữ liệu cho bài toán giao hàng.

    - Node 0 (depot) là nguồn: xe chỉ load đúng số hàng cần giao (tổng demand của các khách hàng xe đi qua).
    - Các khách hàng có demand > 0.
    - vehicle_capacities: giới hạn tối đa của xe.
    - time_windows: các khung thời gian cho từng điểm.
    """
    data = {}
    data['distance_matrix'] = [
        [0, 9, 3, 6, 7],
        [9, 0, 6, 4, 3],
        [3, 6, 0, 5, 8],
        [6, 4, 5, 0, 7],
        [7, 3, 8, 7, 0],
    ]
    # Ở depot (node 0): demand = 0; các khách hàng: số hàng cần giao.
    data['demands'] = [0, 1, 1, 2, 4]
    # Mỗi xe có capacity tối đa (xe chỉ load đúng tổng demand của các khách hàng xe đi qua).
    data['vehicle_capacities'] = [5, 5]
    data['num_vehicles'] = 2
    data['depot'] = 0
    # Time windows theo yêu cầu:
    # depot: (0,15), khách hàng 1: (2,9), khách hàng 2: (3,5), khách hàng 3: (1,5), khách hàng 4: (7,11)
    data['time_windows'] = [
        (0, 15),    # depot
        (0, 9),     # khách hàng 1
        (0, 5),     # khách hàng 2
        (0, 5),     # khách hàng 3
        (0, 11),    # khách hàng 4
    ]
    return data


def main():
    data = create_data_model()

    # Quản lý index của các điểm.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'],
                                           data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    # --- Callback tính khoảng cách giữa các điểm ---
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # --- Callback demand cho dimension "Capacity" ---
    # Trả về 0 cho depot, và -demand cho khách hàng.
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return 0 if from_node == data['depot'] else -data['demands'][from_node]
    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)

    # Thêm dimension "Capacity"
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # Không cho phép slack
        data['vehicle_capacities'],
        False,  # fix_start_cumul_to_zero = False để solver tự chọn load phù hợp tại depot
        'Capacity'
    )
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    for vehicle_id in range(data['num_vehicles']):
        start_index = routing.Start(vehicle_id)
        end_index = routing.End(vehicle_id)
        # Tại depot, load được chọn trong khoảng [0, capacity].
        capacity_dimension.CumulVar(start_index).SetRange(
            0, data['vehicle_capacities'][vehicle_id])
        # Tại điểm kết thúc, buộc load về 0.
        capacity_dimension.CumulVar(end_index).SetRange(0, 0)
    for i in range(routing.Size()):
        capacity_dimension.CumulVar(i).SetRange(
            0, max(data['vehicle_capacities']))

    # --- Callback tính "Time" với velocity và service time ---
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        velocity = 2
        # Service time: 0 với depot, 1 với khách hàng.
        service_time = 0 if from_node == data['depot'] else 1
        travel_time = data['distance_matrix'][from_node][to_node] / velocity
        return int(travel_time + service_time)
    transit_time_callback_index = routing.RegisterTransitCallback(
        time_callback)
    waiting_time = 5   # Cho phép xe chờ nếu đến sớm
    horizon = 30       # Tổng thời gian tối đa của mỗi xe
    # fix_start_cumul_to_zero=True để bắt đầu từ 0 và tích lũy thời gian thực.
    routing.AddDimension(
        transit_time_callback_index,
        waiting_time,
        horizon,
        True,  # fix_start_cumul_to_zero = True
        'Time'
    )
    time_dimension = routing.GetDimensionOrDie('Time')
    for location_idx, time_window in enumerate(data['time_windows']):
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        print_solution(data, manager, routing, solution)
    else:
        print("Không tìm thấy lời giải!")


def print_solution(data, manager, routing, solution):
    """In kết quả cho mỗi xe:
       - Thứ tự các điểm trên tuyến.
       - Arrival Time (cumulative 'Time') của từng điểm.
       - Capacity (số hàng còn lại trên xe) tại mỗi điểm.
       - Delivered: với khách hàng, tính là hiệu số giữa giá trị capacity tại node hiện tại và node kế, bằng demand của node đó.
       - Tổng khoảng cách của tuyến.
    """
    time_dimension = routing.GetDimensionOrDie('Time')
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    total_distance = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_distance = 0
        plan_output = f"Route for vehicle {vehicle_id}:\n"
        # Duyệt qua các node trên tuyến
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival_time = solution.Value(time_dimension.CumulVar(index))
            current_capacity = solution.Value(
                capacity_dimension.CumulVar(index))
            # Nếu node không phải depot, tính số hàng giao tại node này theo:
            # delivered = capacity(current node) - capacity(next node)
            next_index = solution.Value(routing.NextVar(index))
            delivered = 0
            if node != data['depot']:
                delivered = current_capacity - \
                    solution.Value(capacity_dimension.CumulVar(next_index))
            plan_output += f" Node {node} (Arrival Time: {arrival_time}, Capacity: {current_capacity}, Delivered: {delivered}) ->"
            from_node = manager.IndexToNode(index)
            index = next_index
            to_node = manager.IndexToNode(index)
            route_distance += data['distance_matrix'][from_node][to_node]
        # In node cuối (depot kết thúc)
        node = manager.IndexToNode(index)
        arrival_time = solution.Value(time_dimension.CumulVar(index))
        final_capacity = solution.Value(capacity_dimension.CumulVar(index))
        plan_output += f" Node {node} (Arrival Time: {arrival_time}, Capacity: {final_capacity}, Delivered: 0)\n"
        plan_output += f"Distance of the route: {route_distance}\n"
        print(plan_output)
        total_distance += route_distance
    print(f"Total distance of all routes: {total_distance}")


if __name__ == '__main__':
    main()
