from datetime import datetime, timedelta

IS_TESTING = False
NUM_OF_VEHICLES = 0  # số xe
NUM_OF_NODES = 50     # số đỉnh của đồ thị
NUM_OF_REQUEST_PER_DAY = 30
NUM_OF_DAY_REPETION = 3
DISTANCE_SCALE = 1
CAPACITY_SCALE = 10
TIME_SCALE = 1
MAX_ROUTE_SIZE = 4
DATES = ["19.02.2025"]

SUPER_DEPOT = 0
ALPHA_BALANCE = 10000000000000
depots_actual = [0, 1, 2, 3, 4, 5]
# scale = 1: đo thời gian theo đơn vị giờ, scale = X: đo thời gian theo đơn vị 1/X giờ
# quãng đường tối đa xe di chuyển trong 1 turn
MAX_TRAVEL_DISTANCE = DISTANCE_SCALE * 1000
AVG_VELOCITY = DISTANCE_SCALE * 45
MAX_TRAVEL_TIME = TIME_SCALE * 24
MAX_WAITING_TIME = TIME_SCALE * 3
MIN_CAPACITY = 24 * CAPACITY_SCALE
MAX_CAPACITY = 57 * CAPACITY_SCALE
GLOBAL_SPAN_COST_COEFFICIENT = 7
MU = 2
LAMBDA = 2
SEARCH_STRATEGY = 0
INFINITY = 999_999_999_999_999_999
RUNTIME = None
DEPOT_VEHICLE_COUNTS = [20, 21]
NU_PENALTY = 10

# Mở rộng danh sách depot thành 6 điểm
depots = [0, 1, 2, 3, 4, 5]

"======================HANDLE EXCEL==========================="
DROP_DOWN_RANGE_DIA_CHI = "Dia_Chi!C1:C1000"
DROP_DOWN_RANGE_TIME = f"CONFIG!AA1:AA{(24 * TIME_SCALE + 1) * 12 * TIME_SCALE}"
DROP_DOWN_RANGE_CHECKBOX = "CONFIG!AB1:AB2"


config = {
    "IS_TESTING": IS_TESTING,
    "NUM_OF_VEHICLES": NUM_OF_VEHICLES,
    "NUM_OF_NODES": NUM_OF_NODES,
    "NUM_OF_REQUEST_PER_DAY": NUM_OF_REQUEST_PER_DAY,
    "NUM_OF_DAY_REPETION": NUM_OF_DAY_REPETION,
    "DISTANCE_SCALE": DISTANCE_SCALE,
    "CAPACITY_SCALE": CAPACITY_SCALE,
    "TIME_SCALE": TIME_SCALE,
    "MAX_ROUTE_SIZE": MAX_ROUTE_SIZE,
    "MAX_TRAVEL_DISTANCE": MAX_TRAVEL_DISTANCE,
    "AVG_VELOCITY": AVG_VELOCITY,
    "MAX_TRAVEL_TIME": MAX_TRAVEL_TIME,
    "MAX_WAITING_TIME": MAX_WAITING_TIME,
    "GLOBAL_SPAN_COST_COEFFICIENT": GLOBAL_SPAN_COST_COEFFICIENT,
    "MU": MU,
    "LAMBDA": LAMBDA,
    "SEARCH_STRATEGY": SEARCH_STRATEGY,
    "RUNTIME": RUNTIME,
    "DEPOT_VEHICLE_COUNTS": DEPOT_VEHICLE_COUNTS,
    "NU_PENALTY": NU_PENALTY,
    "depots": depots
}

now = datetime.now()
TODAY = now.strftime("%d%m%Y")
if IS_TESTING:
    TODAY = "19.02.2025"
TODAY = "27032025"
TODAY_DT = datetime.strptime(TODAY, "%d%m%Y")
DATES = []
for i in range(NUM_OF_DAY_REPETION):
    next_date = TODAY_DT + timedelta(days=i)
    DATES.append(next_date.strftime("%d.%m.%Y"))
config["DATES"] = DATES

"""  #####  DEFAULT DATA  #####  """
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
DEFAULT_DISTANCE_MATRIX = [
    # 0   1    2    3    4    5    6
    [0, 8, 8, 5, 5, 10, 10],  # 0: depot
    [8, 0, 0, 6, 6, 4, 4],  # 1: khách hàng 1a
    [8, 0, 0, 6, 6, 4, 4],  # 2: khách hàng 1b
    [5, 6, 6, 0, 3, 8, 8],  # 3: khách hàng 2
    [5, 6, 6, 3, 0, 8, 8],  # 4: khách hàng 3
    [10, 4, 4, 8, 8, 0, 0],  # 5: khách hàng 4a
    [10, 4, 4, 8, 8, 0, 0],  # 6: khách hàng 4b
]

# Định nghĩa lượng hàng cần giao cho mỗi node:
# - 0: depot không có demand.
# - 1: khách hàng 1a: 5 đơn vị.
# - 2: khách hàng 1b: 3 đơn vị.
# - 3: khách hàng 2: 1 đơn vị.
# - 4: khách hàng 3: 2 đơn vị.
# - 5: khách hàng 4a: 5 đơn vị.
# - 6: khách hàng 4b: 1 đơn vị.
DEFAULT_DEMANDS = [0, 5, 3, 1, 2, 5, 1]
[0, 5, 3, 1, 2, 5, 1]

DEFAULT_VEHICLE_CAPACITIES = [10, 9, 8, 5]  # dung tích của các xe

# Thiết lập khung thời gian cho từng node:
# - Depot có khung thời gian rộng.
# - Các khách hàng có khung thời gian cụ thể:
#     + Khách hàng 1 (node 1 và 2): từ 0 đến 20.
#     + Khách hàng 2 (node 3): từ 0 đến 15.
#     + Khách hàng 3 (node 4): từ 0 đến 15.
#     + Khách hàng 4 (node 5 và 6): từ 10 đến 30.
DEFAULT_TIME_WINDOWS = [
    (0, 24),  # depot
    (0, 16),  # khách hàng 1a
    (0, 16),  # khách hàng 1b
    (0, 12),  # khách hàng 2
    (0, 12),  # khách hàng 3
    (0, 24),  # khách hàng 4a
    (0, 24),  # khách hàng 4b
]


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
