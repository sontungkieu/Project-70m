from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# vehicle capacity phải là số nguyên
# chuyển hết sang đơn vị (0.1m3)
# xe 9.7 m3 thành 97 0.1m3

NUM_OF_VEHICLES = 41              # số xe
NUM_OF_NODES = 30               # số đỉnh của đồ thị
NUM_OF_REQUEST_PER_DAY = 10       #
NUM_OF_DAY_REPETION = 30          #
DISTANCE_SCALE = 1        # scale = 1: đo khoảng cách theo km, scale = 10 do khoảng cách theo 0.1km
CAPACITY_SCALE = 10       # scale = 1: đo hàng theo đơn vị m3, scale = 10: đo hàng theo đơn vị 0.1m3
TIME_SCALE = 1            # scale = 1: đo thời gian theo đơn vị giờ, scale = X: đo thời gian theo đơn vị 1/X giờ
MAX_TRAVEL_DISTANCE = DISTANCE_SCALE * 1000  # quãng đường tối đa xe di chuyển trong 1 turn
AVG_VELOCITY = DISTANCE_SCALE * 45           # đặt vận tốc trung bình xe đi trên đường là 45km/h
MAX_TRAVEL_TIME = TIME_SCALE * 24            # 24 is not able to run
MAX_WAITING_TIME = TIME_SCALE * 3            # xe có thể đến trước, và đợi không quá 5 tiếng 
#tunable parameter
GLOBAL_SPAN_COST_COEFFICIENT = 100
MU = 1 
LAMBDA = 1
SEARCH_STRATEGY = 0

search_strategy = [routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
                   routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
                   routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
                   routing_enums_pb2.FirstSolutionStrategy.SAVINGS,][SEARCH_STRATEGY]

# ------------------------------
# Phần "daily": tạo dữ liệu và mô hình định tuyến cho một ngày giao hàng

def load_data(distance_file='data/distance.csv',request_file = 'data/requests.csv', vehicle_file = 'data/vehicle.csv'):
    global NUM_OF_VEHICLES, NUM_OF_NODES
    import numpy as np
    import pandas as pd

    #load distance matrix
    distance_matrix = np.loadtxt(distance_file, delimiter=',').tolist() #54x54
    distance_matrix = [[int(u*DISTANCE_SCALE) for u in v] for v in distance_matrix]
    NUM_OF_NODES = len(distance_matrix)
    # print(distance_matrix)
    
    #load vehicles list
    vehicle_capacities = [int(u*CAPACITY_SCALE) for u in  np.loadtxt(vehicle_file, delimiter=',').tolist()]
    NUM_OF_VEHICLES = len(vehicle_capacities)

    #load request
    """
    Start Place,End Place,Weight,Gen Day,Gen Timeframe
    [0],[51],1.4,1,"[4, 7]"
    [0],[41],2.16,0,"[0, 2]"
    [1],[36],0.13,1,"[20, 22]"
    [1],[32],1.42,0,"[5, 22]"
    [2],[21],0.79,1,"[3, 10]"
    [3],[10],1.83,2,"[8, 19]"
    [3],[38],0.63,3,"[2, 17]"
    [2],[40],0.98,0,"[1, 21]"
    [2],[9],1.19,0,"[8, 12]"
    [2],[14],1.89,2,"[6, 21]"
    """
    requests_df = pd.read_csv(request_file)
    demands = [0 for i in range(NUM_OF_NODES)]
    time_windows = [(0,24*TIME_SCALE) for i in range(NUM_OF_NODES)]
    for _, row in requests_df.iterrows():
        end_place = int(row['End Place'][1:-1].split(',')[0])
        weight = row['Weight']
        demands[end_place] += int(weight*10)
        time_windows[end_place] = tuple(int(u*TIME_SCALE) for u in row['Gen Timeframe'][1:-1].split(','))
    print(demands)
    return distance_matrix,demands,vehicle_capacities, time_windows
    

def create_data_model(*,distance_matrix=None,demands = None, vehicles = None, time_window = None):
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
    ] if not distance_matrix  else distance_matrix
    # Định nghĩa lượng hàng cần giao cho mỗi node:
    # - 0: depot không có demand.
    # - 1: khách hàng 1a: 5 đơn vị.
    # - 2: khách hàng 1b: 3 đơn vị.
    # - 3: khách hàng 2: 1 đơn vị.
    # - 4: khách hàng 3: 2 đơn vị.
    # - 5: khách hàng 4a: 5 đơn vị.
    # - 6: khách hàng 4b: 1 đơn vị.
    data['demands'] = [0, 5, 3, 1, 2, 5, 1] if not demands  else demands

    # Với trọng tải của xe là 5 đơn vị, những node với demand <= 5 đảm bảo không vượt quá.
    # Tổng demand của các khách hàng là 5+3+1+2+5+1 = 17, nên sử dụng 4 xe với tải trọng 5 (tổng tải = 20).
    data['vehicle_capacities'] = [10, 9, 8, 5] if not vehicles else vehicles
    data['num_vehicles'] = 4 if not vehicles else len(vehicles)
    NUM_OF_VEHICLES = data['num_vehicles']
    data['depot'] = 0

    # Thiết lập khung thời gian cho từng node:
    # - Depot có khung thời gian rộng.
    # - Các khách hàng có khung thời gian cụ thể:
    #     + Khách hàng 1 (node 1 và 2): từ 0 đến 20.
    #     + Khách hàng 2 (node 3): từ 0 đến 15.
    #     + Khách hàng 3 (node 4): từ 0 đến 15.
    #     + Khách hàng 4 (node 5 và 6): từ 10 đến 30.
    t_TIME_SCALE = TIME_SCALE/30*24
    data['time_windows'] = [
        (0, 30*t_TIME_SCALE),    # depot
        (0, 20*t_TIME_SCALE),    # khách hàng 1a
        (0, 20*t_TIME_SCALE),    # khách hàng 1b
        (0, 15*t_TIME_SCALE),    # khách hàng 2
        (0, 15*t_TIME_SCALE),    # khách hàng 3
        (0, 30*t_TIME_SCALE),   # khách hàng 4a
        (0, 30*t_TIME_SCALE),   # khách hàng 4b
    ] if time_window == None else time_window
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
        import gen_requests
        import random
        seed = random.randint(10,1000)
        list_of_seed.append(seed)
        gen_requests.gen_requests_and_save(NUM_OF_REQUEST_PER_DAY,file_sufices=str(day),NUM_OF_NODES=NUM_OF_NODES,seed=seed)
        distance_matrix,demands,vehicle_capacities, time_windows = load_data(request_file=f"data/requests{day}.csv")
        if not historical_km:
            historical_km = [0 for _ in range(NUM_OF_VEHICLES)]
        # Trong thực tế, dữ liệu đơn hàng có thể khác mỗi ngày.
        # data = create_daily_data_model()
        data = create_data_model(distance_matrix=distance_matrix,demands=demands,vehicles=vehicle_capacities, time_window=time_windows)
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

# config = {'NUM_OF_VEHICLES': NUM_OF_VEHICLES,              # số xe
# 'NUM_OF_NODES': NUM_OF_NODES,                # số đỉnh của đồ thị
# 'NUM_OF_REQUEST_PER_DAY': NUM_OF_REQUEST_PER_DAY,        #
# 'NUM_OF_DAY_REPETION': NUM_OF_DAY_REPETION,          #
# 'DISTANCE_SCALE': DISTANCE_SCALE,        # scale = 1: đo khoảng cách theo km, scale = 10 do khoảng cách theo 0.1km
# 'CAPACITY_SCALE': CAPACITY_SCALE,       # scale = 1: đo hàng theo đơn vị m3, scale = 10: đo hàng theo đơn vị 0.1m3
# 'TIME_SCALE':TIME_SCALE,            # scale = 1: đo thời gian theo đơn vị giờ, scale = X: đo thời gian theo đơn vị 1/X giờ
# MAX_TRAVEL_DISTANCE  # quãng đường tối đa xe di chuyển trong 1 turn
# AVG_VELOCITY = DISTANCE_SCALE * 45           # đặt vận tốc trung bình xe đi trên đường là 45km/h
# MAX_TRAVEL_TIME = TIME_SCALE * 24            # 24 is not able to run
# MAX_WAITING_TIME = TIME_SCALE * 3            # xe có thể đến trước, và đợi không quá 5 tiếng 
# #tunable parameter
# GLOBAL_SPAN_COST_COEFFICIENT = 100
# MU = 1 
# LAMBDA = 1
# SEARCH_STRATEGY = 0}

config = {
    'NUM_OF_VEHICLES': NUM_OF_VEHICLES,              # số xe
    'NUM_OF_NODES': NUM_OF_NODES,                    # số đỉnh của đồ thị
    'NUM_OF_REQUEST_PER_DAY': NUM_OF_REQUEST_PER_DAY, # số yêu cầu mỗi ngày
    'NUM_OF_DAY_REPETION': NUM_OF_DAY_REPETION,      # số lần lặp lại trong ngày
    'DISTANCE_SCALE': DISTANCE_SCALE,                # scale = 1: đo khoảng cách theo km, scale = 10 do khoảng cách theo 0.1km
    'CAPACITY_SCALE': CAPACITY_SCALE,                # scale = 1: đo hàng theo đơn vị m3, scale = 10: đo hàng theo đơn vị 0.1m3
    'TIME_SCALE': TIME_SCALE,                        # scale = 1: đo thời gian theo đơn vị giờ, scale = X: đo thời gian theo đơn vị 1/X giờ
    'MAX_TRAVEL_DISTANCE': MAX_TRAVEL_DISTANCE,      # quãng đường tối đa xe di chuyển trong 1 turn
    'AVG_VELOCITY': AVG_VELOCITY,                    # đặt vận tốc trung bình xe đi trên đường là 45km/h
    'MAX_TRAVEL_TIME': MAX_TRAVEL_TIME,              # thời gian di chuyển tối đa
    'MAX_WAITING_TIME': MAX_WAITING_TIME,            # xe có thể đến trước, và đợi không quá 5 tiếng
    'GLOBAL_SPAN_COST_COEFFICIENT': GLOBAL_SPAN_COST_COEFFICIENT, # hệ số chi phí toàn cầu
    'MU': MU,                                        # hệ số MU
    'LAMBDA': LAMBDA,                                # hệ số LAMBDA
    'SEARCH_STRATEGY': SEARCH_STRATEGY               # chiến lược tìm kiếm
}

if __name__=='__main__':
    import gen_map
    import gen_vehicle
    #gen map
    gen_map.gen_map(NUM_OF_NODES=NUM_OF_NODES,seed=42)
    #gen vehicle
    gen_vehicle.gen_list_vehicle(NUM_OF_VEHICLES=NUM_OF_VEHICLES,seed=42)

    # Ví dụ: chạy cho 30 ngày, với lambda_penalty = 1000 và mu_penalty = 50 (điều chỉnh dựa trên dữ liệu thực tế)
    # multi_day_routing(num_days=2, lambda_penalty=1, mu_penalty=1)
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=1)#[1638, 1577, 1567, 2201, 2136]       
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=2)#[1559, 1568, 1615, 2231, 2118]
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=3)#[1528, 1561, 1548, 2194, 2126]
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=5)#[1528, 1561, 1548, 2194, 2126]      
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=10)#[1428, 1457, 1452, 2314, 2224]       
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=20)#[1465, 1460, 1448, 2284, 2372]       
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=30)#[1466, 1459, 1491, 2245, 2336]       
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=0.01)#[1671, 1566, 1574, 2209, 2136]      
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=1, mu_penalty=0.0001)#[1522, 1543, 1530, 2292, 2197]       
    # multi_day_routing_gen_request(num_days=30, lambda_penalty=0.1, mu_penalty=1)#[1615, 1577, 1685, 2115, 2046]        
    multi_day_routing_gen_request(num_days=NUM_OF_DAY_REPETION, lambda_penalty=LAMBDA, mu_penalty=MU)#[1638, 1577, 1567, 2201, 2136] 
    import sys

    print(config, file=sys.stderr)      
      

