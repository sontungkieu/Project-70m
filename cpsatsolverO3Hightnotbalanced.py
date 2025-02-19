import os
import json
from ortools.sat.python import cp_model

# ============================
# 1. CẤU HÌNH CHUNG & HÀM LOAD DỮ LIỆU
# ============================
NUM_OF_VEHICLES = 4    # Số xe (bạn có thể điều chỉnh)
NUM_OF_NODES = 30      # Số node (sẽ được cập nhật từ dữ liệu)
DISTANCE_SCALE = 1
CAPACITY_SCALE = 10
TIME_SCALE = 1
MAX_TRAVEL_DISTANCE = DISTANCE_SCALE * 1000
AVG_VELOCITY = DISTANCE_SCALE * 45
MAX_TRAVEL_TIME = TIME_SCALE * 24
MAX_WAITING_TIME = TIME_SCALE * 3
NUM_THREADS = 8        # Sử dụng đa luồng

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_data():
    global NUM_OF_NODES, NUM_OF_VEHICLES
    distance_file = os.path.join(BASE_DIR, "data", "distance.json")
    request_file = os.path.join(BASE_DIR, "data", "requests.json")
    vehicle_file = os.path.join(BASE_DIR, "data", "vehicle.json")

    with open(distance_file, "r", encoding="utf-8") as f:
        distance_matrix = json.load(f)
    # Quy đổi đơn vị nếu cần
    distance_matrix = [[int(u * DISTANCE_SCALE) for u in row] for row in distance_matrix]
    NUM_OF_NODES = len(distance_matrix)

    with open(vehicle_file, "r", encoding="utf-8") as f:
        vehicle_capacities = json.load(f)
    vehicle_capacities = [int(u * CAPACITY_SCALE) for u in vehicle_capacities]
    NUM_OF_VEHICLES = len(vehicle_capacities)

    with open(request_file, "r", encoding="utf-8") as f:
        requests_data = json.load(f)

    demands = [0] * NUM_OF_NODES
    time_windows = [(0, 24 * TIME_SCALE)] * NUM_OF_NODES

    for request in requests_data:
        end_place = int(request[1][0])
        weight = request[2]
        if end_place >= NUM_OF_NODES:
            print(f"⚠️ Warning: end_place {end_place} exceeds NUM_OF_NODES ({NUM_OF_NODES}). Skipping request.")
            continue
        demands[end_place] += int(weight * 10)
        time_windows[end_place] = tuple(int(u * TIME_SCALE) for u in request[-1])

    return distance_matrix, demands, vehicle_capacities, time_windows

# ============================
# 2. MÔ HÌNH CP-SAT CHO VRP (Multi-Vehicle)
# ============================
def solve_vrp_cp_sat(distance_matrix, demands, vehicle_capacities):
    model = cp_model.CpModel()

    N = NUM_OF_NODES   # số node (bao gồm depot là node 0)
    V = NUM_OF_VEHICLES

    # Tính M (big-M cho ràng buộc tải trọng), có thể dùng tổng demand
    M = sum(demands) + 1

    # Biến quyết định: x[v,i,j] = 1 nếu xe v di chuyển từ i đến j, 0 nếu không.
    x = {}
    for v in range(V):
        for i in range(N):
            for j in range(N):
                if i != j:
                    x[v, i, j] = model.NewBoolVar(f"x[{v},{i},{j}]")

    # Biến tải trọng: load[v,i] là lượng hàng trên xe v khi đến node i.
    load = {}
    for v in range(V):
        for i in range(N):
            # Giá trị tải có thể từ 0 đến capacity của xe v.
            load[v, i] = model.NewIntVar(0, vehicle_capacities[v], f"load[{v},{i}]")

    # ============================
    # 2.1 Ràng buộc: Mỗi khách hàng (node 1..N-1) được phục vụ đúng 1 lần.
    for j in range(1, N):
        model.Add(sum(x[v, i, j] for v in range(V) for i in range(N) if i != j) == 1)

    # ============================
    # 2.2 Ràng buộc: Luồng xe (flow conservation) cho từng xe.
    # Từ depot (node 0), xe có thể xuất phát (xuất phát = 1) và phải về depot.
    for v in range(V):
        # Xe v khởi hành từ depot.
        model.Add(sum(x[v, 0, j] for j in range(1, N)) <= 1)
        # Luồng tại depot: số xe xuất phát = số xe kết thúc = 0 (chúng ta không bắt buộc phải quay về depot trong mô hình này)
        # Với các node khác (khách hàng):
        for i in range(1, N):
            model.Add(sum(x[v, i, j] for j in range(N) if i != j) ==
                      sum(x[v, j, i] for j in range(N) if i != j))

    # ============================
    # 2.3 Ràng buộc tải trọng và loại bỏ các chu trình phụ (sub-tours)
    # Nếu xe v di chuyển từ i đến j, thì tải tại j = tải tại i + demand của j.
    for v in range(V):
        # Tại depot, tải ban đầu = 0.
        model.Add(load[v, 0] == 0)
        for i in range(N):
            for j in range(1, N):  # Chỉ áp dụng cho khách hàng
                if i != j:
                    # Nếu x[v,i,j] = 1 => load[v,j] == load[v,i] + demands[j]
                    # Sử dụng trick của big-M:
                    model.Add(load[v, j] >= load[v, i] + demands[j] - M * (1 - x[v, i, j]))
                    model.Add(load[v, j] <= load[v, i] + demands[j] + M * (1 - x[v, i, j]))
                    # Ngoài ra, đảm bảo load không giảm.
                    model.Add(load[v, j] >= demands[j]).OnlyEnforceIf(x[v, i, j])

    # ============================
    # 2.4 Ràng buộc: Tải trọng không vượt quá khả năng của xe.
    for v in range(V):
        for i in range(N):
            model.Add(load[v, i] <= vehicle_capacities[v])

    # ============================
    # 2.5 Ràng buộc: Tổng quãng đường di chuyển của tất cả các xe không vượt quá MAX_TRAVEL_DISTANCE.
    total_distance = sum(distance_matrix[i][j] * x[v, i, j]
                         for v in range(V) for i in range(N) for j in range(N) if i != j)
    model.Add(total_distance <= MAX_TRAVEL_DISTANCE)

    # ============================
    # 2.6 Hàm mục tiêu: Tối ưu hóa tổng quãng đường.
    model.Minimize(total_distance)

    # ============================
    # 2.7 Cấu hình solver với đa luồng
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = NUM_THREADS
    solver.parameters.max_time_in_seconds = 60.0  # Giới hạn thời gian, có thể điều chỉnh

    # ============================
    # 2.8 Giải bài toán
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("✅ Tìm thấy lời giải!")
        # In lời giải cho từng xe:
        for v in range(V):
            print(f"\n🚛 Xe {v} route:")
            route = [0]
            current = 0
            while True:
                next_node = None
                for j in range(N):
                    if current != j and solver.Value(x[v, current, j]) == 1:
                        next_node = j
                        break
                if next_node is None:
                    break
                route.append(next_node)
                current = next_node
                if current == 0:
                    break
            if len(route) == 1:
                print("  Không có tuyến.")
            else:
                # In thêm tải và khoảng cách
                load_values = [solver.Value(load[v, i]) for i in route]
                print("  Route: ", route)
                print("  Load at nodes: ", load_values)
        print("\n📏 Tổng quãng đường:", solver.Value(total_distance), "km")
    else:
        print("❌ Không tìm thấy lời giải tối ưu!")
    return solver, model

# ============================
# 3. CHẠY CHƯƠNG TRÌNH
# ============================
if __name__ == "__main__":
    distance_matrix, demands, vehicle_capacities, time_windows = load_data()
    solve_vrp_cp_sat(distance_matrix, demands, vehicle_capacities)
