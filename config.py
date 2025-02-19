NUM_OF_VEHICLES = 41                   # số xe
NUM_OF_NODES = 30               # số đỉnh của đồ thị
NUM_OF_REQUEST_PER_DAY = 30        #
NUM_OF_DAY_REPETION = 30            #
# scale = 1: đo khoảng cách theo km, scale = 10 do khoảng cách theo 0.1km
DISTANCE_SCALE = 1
# scale = 1: đo hàng theo đơn vị m3, scale = 10: đo hàng theo đơn vị 0.1m3
CAPACITY_SCALE = 10
# scale = 1: đo thời gian theo đơn vị giờ, scale = X: đo thời gian theo đơn vị 1/X giờ
TIME_SCALE = 1
# quãng đường tối đa xe di chuyển trong 1 turn
MAX_TRAVEL_DISTANCE = DISTANCE_SCALE * 1000
# đặt vận tốc trung bình xe đi trên đường là 45km/h
AVG_VELOCITY = DISTANCE_SCALE * 45
MAX_TRAVEL_TIME = TIME_SCALE * 24            # 24 is not able to run
# xe có thể đến trước, và đợi không quá 5 tiếng
MAX_WAITING_TIME = TIME_SCALE * 3
# tunable parameter
GLOBAL_SPAN_COST_COEFFICIENT = 10
MU = 2.5
LAMBDA = 1
# 0: PATH_CHEAPEST_ARC, 1: AUTOMATIC, 2: GLOBAL_CHEAPEST_ARC, 3: SAVINGS
SEARCH_STRATEGY = 2    # chọn chiến lược tìm kiếm



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