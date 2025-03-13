from objects.driver import Driver

driver_list = []
vehicle_list = []

# def to_json():
#     driver_list_json = []
#     vehicle_list_json = []
#     for driver in driver_list:
#         driver_list_json.append({
#             "name": driver.name,
#             "cccd": driver.cccd,
#             "vehicle_id": driver.vehicle_id,
#             "salary": driver.salary,
#             "route_by_day": driver.route_by_day,
#             "phone_number": driver.phone_number
#         })
#     for vehicle in vehicle_list:
#         vehicle_list_json.append({
#             "vehicle_id": vehicle.vehicle_id,
#             "driver_cccd": vehicle.driver_cccd,
#             "load": vehicle.load,
#             "accumulated_distance": vehicle.accumulated_distance,
#             "route_by_day": vehicle.route_by_day
#         })
#     res = {
#         "drivers": driver_list_json,
#         "vehicles": vehicle_list_json
#     }
#     # Dump result to data.json
#     import json
#     with open("data/driver_vehicle.json", "w", encoding="utf-8") as file:
#         json.dump(res, file, separators=(",", ":"), ensure_ascii=False)
#     return res

# def read_json():
#     import json
#     global driver_list
#     global vehicle_list
#     with open("data/driver_vehicle.json", "r") as file:
#         data = json.load(file)
#         driver_list = []
#         vehicle_list = []
#         for driver in data["drivers"]:
#             new_driver = Driver(driver["name"], driver["cccd"], driver["vehicle_id"], driver["salary"], driver["route_by_day"],driver["phone_number"])
#             driver_list.append(new_driver)
#         for vehicle in data["vehicles"]:
#             new_vehicle = Vehicle(vehicle["vehicle_id"], vehicle["driver_cccd"], vehicle["load"], vehicle["accumulated_distance"],driver["route_by_day"])
#             vehicle_list.append(new_vehicle)

# def add_driver(driver:Driver):
#     read_json()
#     driver_list.append(driver)
#     driver_list.sort(key = lambda driver:driver.cccd)
#     to_json()

# def add_vehicle(vehicle:Vehicle):
#     read_json()
#     vehicle_list.append(vehicle)
#     vehicle_list.sort(key = lambda vehicle:vehicle.comparable_id())
#     to_json()

# def attach2way(driver_cccd,vehicle_id):
#     read_json()
#     for i in range(len(driver_list)):
#         if driver_list[i].cccd == driver_cccd:
#             driver_list[i].vehicle_id = vehicle_id
#     for i in range(len(vehicle_list)):
#         if vehicle_list[i].vehicle_id == vehicle_id:
#             vehicle_list[i].driver_cccd = driver_cccd
#     to_json()

# def detach2way(driver_cccd,vehicle_id):
#     read_json()
#     for i in range(len(driver_list)):
#         if driver_list[i].cccd == driver_cccd:
#             driver_list[i].vehicle_id = ""
#     for i in range(len(vehicle_list)):
#         if vehicle_list[i].vehicle_id == vehicle_id:
#             vehicle_list[i].driver_cccd = ""
#     to_json()
# #tài xế nghỉ ốm

# def nghi_om(driver_cccd):
#     read_json()
#     driver_id = -1
#     for i in range(len(driver_list)):
#         if driver_list[i].cccd == driver_cccd:
#             driver_id = i
#             break
#     else:
#         to_json()
#         return
#     for i in range(len(vehicle_list)):
#         if driver_list[driver_id].cccd == vehicle_list[i].driver_cccd:
#             vehicle_list[i].driver_cccd = ""
#     to_json()
# def rev_nghi_om(driver_cccd):
#     read_json()
#     driver_id = -1
#     for i in range(len(driver_list)):
#         if driver_list[i].cccd == driver_cccd:
#             driver_id = i
#             break
#     else:
#         to_json()
#         return
#     vehicle_id = driver_list[driver_id].vehicle_id
#     for i in range(len(vehicle_list)):
#         if vehicle_id == vehicle_list[i].vehicle_id:
#             vehicle_list[i].driver_cccd = driver_list[driver_id].cccd
#     to_json()
