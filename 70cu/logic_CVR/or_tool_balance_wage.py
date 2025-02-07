from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def create_data_model():
    """Tạo dữ liệu cho bài toán giao hàng với split delivery.

    Trong bài toán này:
    - Một khách hàng nếu có nhu cầu vượt quá tải trọng của xe (ở đây là 5 đơn vị)
      sẽ được chia thành nhiều node riêng biệt.
    - Ví dụ:
         • Khách hàng 1 có đơn hàng 8 đơn vị sẽ chia thành 2 node: 1a (5 đơn vị) và 1b (3 đơn vị).
         • Khách hàng 4 có đơn hàng 6 đơn vị sẽ chia thành 2 node: 4a (5 đơn vị) và 4b (1 đơn vị).
    - Các node này đều có cùng vị trí (vì cùng là của khách hàng đó) nên khoảng cách giữa chúng bằng 0.
    """
    data = {}
    # Định nghĩa 7 node:
    # 0: depot
    # 1: khách hàng 1a (5 đơn vị)
    # 2: khách hàng 1b (3 đơn vị) -> tổng của khách hàng 1 là 8 đơn vị, vượt tải nên cần split.
    # 3: khách hàng 2 (1 đơn vị)
    # 4: khách hàng 3 (2 đơn vị)
    # 5: khách hàng 4a (5 đơn vị)
    # 6: khách hàng 4b (1 đơn vị) -> tổng của khách hàng 4 là 6 đơn vị, vượt tải nên cần split.

    # Ma trận khoảng cách được định nghĩa sao cho:
    # - Các khoảng cách từ depot đến các khách hàng được lấy làm ví dụ.
    # - Khoảng cách giữa các node của cùng một khách hàng (1a, 1b và 4a, 4b) bằng 0.
    data['distance_matrix'] = [
        # 0   1    2    3    4    5    6
        [0,  8,   8,   5,   5,  10,  10],  # 0: depot
        [8,  0,   0,   6,   6,   4,   4],  # 1: khách hàng 1a
        [8,  0,   0,   6,   6,   4,   4],  # 2: khách hàng 1b
        [5,  6,   6,   0,   3,   8,   8],  # 3: khách hàng 2
        [5,  6,   6,   3,   0,   8,   8],  # 4: khách hàng 3
        [10,  4,   4,   8,   8,   0,   0],  # 5: khách hàng 4a
        [10,  4,   4,   8,   8,   0,   0],  # 6: khách hàng 4b
    ]
    # Định nghĩa lượng hàng cần giao cho mỗi node:
    # - 0: depot không có demand.
    # - 1: khách hàng 1a: 5 đơn vị.
    # - 2: khách hàng 1b: 3 đơn vị.
    # - 3: khách hàng 2: 1 đơn vị.
    # - 4: khách hàng 3: 2 đơn vị.
    # - 5: khách hàng 4a: 5 đơn vị.
    # - 6: khách hàng 4b: 1 đơn vị.
    data['demands'] = [0, 5, 3, 1, 2, 5, 1]

    # Với trọng tải của xe là 5 đơn vị, những node với demand <= 5 đảm bảo không vượt quá.
    # Tổng demand của các khách hàng là 5+3+1+2+5+1 = 17, nên sử dụng 4 xe với tải trọng 5 (tổng tải = 20).
    data['vehicle_capacities'] = [10, 5, 5, 5]
    data['num_vehicles'] = 4
    data['depot'] = 0

    # Thiết lập khung thời gian cho từng node:
    # - Depot có khung thời gian rộng.
    # - Các khách hàng có khung thời gian cụ thể:
    #     + Khách hàng 1 (node 1 và 2): từ 0 đến 20.
    #     + Khách hàng 2 (node 3): từ 0 đến 15.
    #     + Khách hàng 3 (node 4): từ 0 đến 15.
    #     + Khách hàng 4 (node 5 và 6): từ 10 đến 30.
    data['time_windows'] = [
        (0, 30),    # depot
        (0, 20),    # khách hàng 1a
        (0, 20),    # khách hàng 1b
        (0, 15),    # khách hàng 2
        (0, 15),    # khách hàng 3
        (0, 30),   # khách hàng 4a
        (0, 30),   # khách hàng 4b
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

    # --- Thêm dimension "Distance" để cân bằng quãng đường giữa các xe ---
    # Dimension này tích lũy quãng đường đi qua của mỗi xe dựa trên distance_callback.
    # Sau đó, sử dụng SetGlobalSpanCostCoefficient để thêm chi phí cho sự chênh lệch quãng đường giữa các xe.
    routing.AddDimension(
        transit_callback_index,
        0,      # Không cho phép slack (không có khoảng cách dư thừa)
        1000,  # Giới hạn tối đa của quãng đường có thể đi (có thể tùy chỉnh)
        True,   # Bắt đầu từ 0
        "Distance"
    )
    distance_dimension = routing.GetDimensionOrDie("Distance")
    # Hệ số này sẽ thêm chi phí vào hàm mục tiêu tương ứng với hiệu số giữa xe có quãng đường lớn nhất và nhỏ nhất.
    distance_dimension.SetGlobalSpanCostCoefficient(10000)
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
        # return int(travel_time + service_time)
        return int(travel_time)
    transit_time_callback_index = routing.RegisterTransitCallback(
        time_callback)
    waiting_time = 5   # Cho phép xe chờ nếu đến sớm
    horizon = 20      # Tổng thời gian tối đa của mỗi xe
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
