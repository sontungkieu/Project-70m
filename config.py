from datetime import datetime, timedelta

IS_TESTING = True
NUM_OF_VEHICLES = 41  # số xe
NUM_OF_NODES = 50     # số đỉnh của đồ thị
NUM_OF_REQUEST_PER_DAY = 30
NUM_OF_DAY_REPETION = 30
DISTANCE_SCALE = 1
CAPACITY_SCALE = 10
TIME_SCALE = 1
MAX_ROUTE_SIZE = 4
MAX_TRAVEL_DISTANCE = DISTANCE_SCALE * 1000
AVG_VELOCITY = DISTANCE_SCALE * 45
MAX_TRAVEL_TIME = TIME_SCALE * 24
MAX_WAITING_TIME = TIME_SCALE * 3
MIN_CAPACITY = 9.7 * CAPACITY_SCALE
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
    TODAY = "19022025"
TODAY_DT = datetime.strptime(TODAY, "%d%m%Y")
DATES = []
for i in range(NUM_OF_DAY_REPETION):
    next_date = TODAY_DT + timedelta(days=i)
    DATES.append(next_date.strftime("%d.%m.%Y"))
config["DATES"] = DATES
