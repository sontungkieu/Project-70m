def split_customers(data):
    """
    Tiền xử lý: Nếu demand của một khách hàng (node > 0) vượt quá tải trọng nhỏ nhất,
    tách khách hàng đó thành nhiều sub-node sao cho mỗi sub-node có demand <= min_capacity.

    Hàm này sẽ cập nhật trực tiếp data (original_data) hiện có, thay đổi các trường:
      - 'demands'
      - 'distance_matrix'
      - 'time_windows'
    và trả về data cùng với mapping: danh sách mapping từ chỉ số của new node sang chỉ số khách hàng gốc.
    """
    NUM_OF_NODES = len(data['demands'])
    #  2. Áp dụng Floyd-Warshall để đảm bảo không vi phạm bất đẳng thức tam giác
    matrix = data['distance_matrix']
    for k in range(NUM_OF_NODES):
        for i in range(NUM_OF_NODES):
            for j in range(NUM_OF_NODES):
                # Nếu đi qua nút k giúp rút ngắn khoảng cách từ i đến j thì cập nhật
                if matrix[i][k] + matrix[k][j] < matrix[i][j]:
                    matrix[i][j] = matrix[i][k] + matrix[k][j]
    # Tạo danh sách mới để lưu các demand sau khi tách và mapping của các node.
    data['distance_matrix'] = matrix
    new_demands = []
    node_mapping = []  # mapping: new node index -> original customer index

    # Đầu tiên, thêm depot (node 0)
    new_demands.append(data['demands'][0])
    node_mapping.append(0)

    # Xác định tải trọng nhỏ nhất
    min_capacity = min(data['vehicle_capacities'])

    # Duyệt qua các khách hàng (node 1..n)
    for i in range(1, len(data['demands'])):
        demand = data['demands'][i]
        if demand <= min_capacity:
            new_demands.append(demand)
            node_mapping.append(i)
        else:
            # Tách: số phần = ceil(demand / min_capacity)
            parts = (demand + min_capacity - 1) // min_capacity
            for _ in range(parts - 1):
                new_demands.append(min_capacity)
                node_mapping.append(i)
            remainder = demand - min_capacity * (parts - 1)
            new_demands.append(remainder)
            node_mapping.append(i)

    # Cập nhật 'demands'
    data['demands'] = new_demands

    # Xây dựng distance_matrix mới:
    n_new = len(new_demands)
    new_distance_matrix = [[0 for _ in range(n_new)] for _ in range(n_new)]
    for i in range(n_new):
        for j in range(n_new):
            orig_i = node_mapping[i]
            orig_j = node_mapping[j]
            if orig_i == orig_j and i != j:
                new_distance_matrix[i][j] = 0
            else:
                new_distance_matrix[i][j] = data['distance_matrix'][orig_i][orig_j]
    data['distance_matrix'] = new_distance_matrix

    # Xây dựng time_windows mới theo mapping (đối với depot và khách hàng gốc)
    new_time_windows = []
    for i in range(n_new):
        orig = node_mapping[i]
        new_time_windows.append(data['time_windows'][orig])
    data['time_windows'] = new_time_windows

    # Lưu ý: Các thông số khác như 'vehicle_capacities' và 'num_vehicles' không thay đổi.
    return data, node_mapping

from typing import List
from objects.request import Request
try:
    from ..config import MIN_CAPACITY
except:
    from config import MIN_CAPACITY
    
def split_requests(requests:List[Request]):
    #maping, inverse_mapping
    new_node = 1
    mapping = {0:[0]}
    inverse_mapping = {0:0}
    new_requests = []
    for request in requests:
        while request.weight > MIN_CAPACITY:
            new_request = Request(request.start_place,request.end_place, MIN_CAPACITY, request.date, request.timeframe, split_id=1)
            new_requests.append(new_request)
            request.weight -= MIN_CAPACITY
        new_requests.append(request)
    mapped_requests = []
    for request in new_requests:
        if request.end_place[0] not in mapping:
            mapping[request.end_place[0]] = [new_node]
        else:
            mapping[request.end_place[0]].append(new_node)
        inverse_mapping[new_node] = request.end_place[0]
        request.end_place[0] = new_node
        new_node += 1
        mapped_requests.append(request)
    return mapped_requests, mapping, inverse_mapping


