import os
import json
from ortools.sat.python import cp_model

# ============================
# 1. CẤU HÌNH CHUNG & HÀM LOAD DỮ LIỆU
# ============================
NUM_THREADS = 8          # Số luồng chạy CP-SAT
DISTANCE_SCALE = 1
CAPACITY_SCALE = 10
TIME_SCALE = 1
MAX_TRAVEL_DISTANCE = 1000  # Giới hạn quãng đường
ALPHA = 100               # Hệ số phạt chênh lệch tải (cân bằng)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_data():
    distance_file = os.path.join(BASE_DIR, "data", "distance.json")
    request_file = os.path.join(BASE_DIR, "data", "requests.json")
    vehicle_file = os.path.join(BASE_DIR, "data", "vehicle.json")

    with open(distance_file, "r", encoding="utf-8") as f:
        distance_matrix = json.load(f)
    distance_matrix = [[int(u * DISTANCE_SCALE) for u in row] for row in distance_matrix]
    num_nodes = len(distance_matrix)

    with open(vehicle_file, "r", encoding="utf-8") as f:
        vehicle_capacities = json.load(f)
    vehicle_capacities = [int(u * CAPACITY_SCALE) for u in vehicle_capacities]
    num_vehicles = len(vehicle_capacities)

    with open(request_file, "r", encoding="utf-8") as f:
        requests_data = json.load(f)

    demands = [0] * num_nodes
    for req in requests_data:
        end_place = int(req[1][0])
        weight = req[2]
        if end_place >= num_nodes:
            print(f"⚠️ end_place {end_place} >= num_nodes {num_nodes}, bỏ qua đơn hàng này.")
            continue
        demands[end_place] += int(weight * 10)

    return distance_matrix, demands, vehicle_capacities, num_nodes, num_vehicles

# ============================
# 2. MÔ HÌNH CP-SAT CHO VRP (MULTI-VEHICLE) + CÂN BẰNG TẢI
# ============================
def solve_vrp_with_balance(distance_matrix, demands, vehicle_capacities, num_nodes, num_vehicles):
    model = cp_model.CpModel()

    N = num_nodes
    V = num_vehicles
    # Big-M cho ràng buộc tải: tổng tất cả demands + 1
    M = sum(demands) + 1

    # ======== Biến quyết định ========
    # x[v,i,j] = 1 nếu xe v đi từ node i -> node j
    x = {}
    for v in range(V):
        for i in range(N):
            for j in range(N):
                if i != j:
                    x[v, i, j] = model.NewBoolVar(f"x[{v},{i},{j}]")

    # load[v,i] = tải của xe v tại node i
    load = {}
    for v in range(V):
        for i in range(N):
            load[v, i] = model.NewIntVar(0, vehicle_capacities[v], f"load[{v},{i}]")

    # loadOfVehicle[v] = tổng lượng hàng xe v đã chở
    # (bằng tổng demands của các node mà xe v đi qua)
    loadOfVehicle = []
    for v in range(V):
        max_demand_sum = sum(demands)  # Xe v có thể chở tối đa = tổng demand
        loadOfVehicle_v = model.NewIntVar(0, max_demand_sum, f"loadOfVehicle[{v}]")
        loadOfVehicle.append(loadOfVehicle_v)

    # maxLoad, minLoad để cân bằng tải
    maxLoad = model.NewIntVar(0, sum(demands), "maxLoad")
    minLoad = model.NewIntVar(0, sum(demands), "minLoad")

    # ======== Ràng buộc cơ bản ========
    # 2.1 Mỗi node (trừ depot = 0) phục vụ đúng 1 lần
    for j in range(1, N):
        model.Add(sum(x[v,i,j] for v in range(V) for i in range(N) if i != j) == 1)

    # 2.2 Mỗi xe xuất phát từ depot (node 0) tối đa 1 lần
    for v in range(V):
        model.Add(sum(x[v, 0, j] for j in range(1, N)) <= 1)

    # 2.3 Ràng buộc luồng (flow):
    #     Tại mỗi node i>0 của xe v, số cung đi ra = số cung đi vào
    for v in range(V):
        for i in range(1, N):
            model.Add(
                sum(x[v, i, j] for j in range(N) if j != i) ==
                sum(x[v, k, i] for k in range(N) if k != i)
            )

    # 2.4 Ràng buộc tải: load[v,j] = load[v,i] + demands[j] nếu x[v,i,j] = 1
    for v in range(V):
        # depot ban đầu load = 0
        model.Add(load[v, 0] == 0)
        for i in range(N):
            for j in range(1, N):
                if i != j:
                    model.Add(load[v, j] >= load[v, i] + demands[j] - M*(1 - x[v, i, j]))
                    model.Add(load[v, j] <= load[v, i] + demands[j] + M*(1 - x[v, i, j]))
                    # load[v, j] <= capacity[v]
                    model.Add(load[v, j] <= vehicle_capacities[v])

    # 2.5 Khống chế tổng quãng đường < MAX_TRAVEL_DISTANCE
    total_distance_expr = []
    for v in range(V):
        for i in range(N):
            for j in range(N):
                if i != j:
                    total_distance_expr.append(distance_matrix[i][j] * x[v, i, j])
    total_dist = model.Add(sum(total_distance_expr) <= MAX_TRAVEL_DISTANCE)

    # ======== Tính loadOfVehicle[v] ========
    # loadOfVehicle[v] = sum( demands[j] * sum_{i} x[v,i,j] )
    for v in range(V):
        expr_load_v = []
        for i in range(N):
            for j in range(N):
                if i != j:
                    expr_load_v.append(demands[j] * x[v, i, j])
        model.Add(loadOfVehicle[v] == sum(expr_load_v))

    # ======== Cân bằng tải: maxLoad - minLoad, ràng buộc maxLoad >= loadOfVehicle[v], minLoad <= loadOfVehicle[v]
    for v in range(V):
        model.Add(loadOfVehicle[v] <= maxLoad)
        model.Add(loadOfVehicle[v] >= minLoad)

    # ======== Hàm mục tiêu: Minimize (tổng quãng đường + ALPHA * (maxLoad - minLoad))
    total_distance = sum(distance_matrix[i][j] * x[v, i, j] for v in range(V) for i in range(N) for j in range(N) if i != j)
    model.Minimize(total_distance + ALPHA * (maxLoad - minLoad))

    # ============================
    # 2.6 Giải mô hình CP-SAT
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = NUM_THREADS  # đa luồng
    solver.parameters.max_time_in_seconds = 60.0        # giới hạn thời gian

    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("✅ Tìm thấy lời giải khả thi (hoặc tối ưu).")
        print(f"➡ Total distance = {solver.Value(total_distance)}")
        print(f"➡ maxLoad = {solver.Value(maxLoad)}, minLoad = {solver.Value(minLoad)}")
        print(f"➡ Chênh lệch tải = {solver.Value(maxLoad) - solver.Value(minLoad)}")

        # In tuyến đường cho từng xe
        for v in range(num_vehicles):
            print(f"\n🚛 Xe {v}:")
            # Tìm node xuất phát:
            start_found = False
            for j in range(1, N):
                if solver.Value(x[v, 0, j]) == 1:
                    start_found = True
                    break
            if not start_found:
                print("  Không xuất phát (xe không dùng)")
                continue

            # Xây dựng route
            route = [0]
            current = 0
            while True:
                next_node = None
                for j in range(N):
                    if j != current and solver.Value(x[v, current, j]) == 1:
                        next_node = j
                        break
                if next_node is None:
                    break
                route.append(next_node)
                current = next_node

            print("  Route:", route)
            # Tải xe
            print(f"  Total load of vehicle {v}:", solver.Value(loadOfVehicle[v]))

    else:
        print("❌ Không tìm thấy lời giải (trong giới hạn thời gian).")

# ============================
# 3. CHẠY CHƯƠNG TRÌNH
# ============================
if __name__ == "__main__":
    distance_matrix, demands, vehicle_capacities, num_nodes, num_vehicles = load_data()
    solve_vrp_with_balance(distance_matrix, demands, vehicle_capacities, num_nodes, num_vehicles)
