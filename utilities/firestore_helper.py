from typing import List
import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase credentials
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

# Firestore database instance
db = firestore.client()

class Request:
    def __init__(self, request_id:str, start_place:List[int], end_place:List[int], weight: int, date: str, timeframe: List[int], split_id:bool = False):
        self.request_id = request_id
        self.start_place = start_place
        self.end_place = end_place
        self.weight = weight
        self.date = date
        self.timeframe = timeframe
        self.split_id = split_id
        self.delivery_time = -1
        self.delivery_status = 0

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "start_place": self.start_place,
            "end_place": self.end_place,
            "weight": self.weight,
            "date": self.date,
            "timeframe": self.timeframe,
            "split_id": self.split_id,
            "delivery_time": self.delivery_time,
            "delivery_status": self.delivery_status
        }

class Driver:
    def __init__(self, name="Nguyen Van A", cccd="001000000000", vehicle_id="30A-12345", vehicle_load=97, salary=0, route_by_day=None, phone_number="098789JQKA"):
        self.name = name
        self.cccd = cccd
        self.vehicle_id = vehicle_id
        self.route_by_day = route_by_day if route_by_day else {}  # Dictionary lưu danh sách tuyến đường theo ngày
        self.phone_number = phone_number
        self.vehicle_load = vehicle_load
        self.available = True

    def to_dict(self):
        return {
            "name": self.name,
            "cccd": self.cccd,
            "vehicle_id": self.vehicle_id,
            "route_by_day": self.route_by_day,
            "phone_number": self.phone_number,
            "vehicle_load": self.vehicle_load,
            "available": self.available
        }

class Route:
    def __init__(self, driver_id="", vehicle_id=""):
        self.route: List[Request] = []
        self.total_distance: float = 0
        self.driver_id: str = driver_id
        self.vehicle_id: str = vehicle_id

    def to_dict(self):
        return {
            "route": [req.to_dict() for req in self.route],  # Lưu danh sách request
            "total_distance": self.total_distance,
            "driver_id": self.driver_id,
            "vehicle_id": self.vehicle_id
        }
    
#Save data to Firestore
def save_request_to_firestore(request: Request):
    db.collection("requests").document(request.request_id).set(request.to_dict())
    print(f"✅ Request {request.request_id} đã được lưu vào Firestore.")

def save_driver_to_firestore(driver: Driver):
    db.collection("drivers").document(driver.cccd).set(driver.to_dict())
    print(f"✅ Driver {driver.name} đã được lưu vào Firestore.")

def save_route_to_firestore(route: Route, route_id: str):
    db.collection("routes").document(route_id).set(route.to_dict())
    print(f"✅ Route {route_id} đã được lưu vào Firestore.")

"""
# Tạo dữ liệu giả lập
request1 = Request("req_001", [10, 20], [30, 40], 50, "2025-02-20", [8, 18])
driver1 = Driver(name="Nguyen Van B", cccd="002000000001", vehicle_id="51B-54321", vehicle_load=80)
route1 = Route(driver_id="002000000001", vehicle_id="51B-54321")
route1.route.append(request1)

# Lưu vào Firestore
save_request_to_firestore(request1)
save_driver_to_firestore(driver1)
save_route_to_firestore(route1, "route_001")
"""
"""
📂 Firestore Database
   ├── 📂 requests
   │      ├── 📄 req_001 { request_id: "req_001", start_place: [10,20], ... }
   │
   ├── 📂 drivers
   │      ├── 📄 002000000001 { name: "Nguyen Van B", vehicle_id: "51B-54321", ... }
   │
   ├── 📂 routes
   │      ├── 📄 route_001 { driver_id: "002000000001", route: [ ... ] }
"""

#Get data from Firestore
def get_request_from_firestore(request_id: str) -> Request:
    doc = db.collection("requests").document(request_id).get()
    if doc.exists:
        data = doc.to_dict()
        return Request(**data)  # Chuyển dictionary về object Request
    else:
        print(f"⚠ Request {request_id} không tồn tại.")
        return None

def get_driver_from_firestore(driver_id: str) -> Driver:
    doc = db.collection("drivers").document(driver_id).get()
    if doc.exists:
        data = doc.to_dict()
        return Driver(**data)
    else:
        print(f"⚠ Driver {driver_id} không tồn tại.")
        return None

def get_route_from_firestore(route_id: str) -> Route:
    doc = db.collection("routes").document(route_id).get()
    if doc.exists:
        data = doc.to_dict()
        route = Route(driver_id=data["driver_id"], vehicle_id=data["vehicle_id"])
        route.total_distance = data["total_distance"]
        for req_data in data["route"]:
            route.route.append(Request(**req_data))  # Chuyển từng request về object
        return route
    else:
        print(f"⚠ Route {route_id} không tồn tại.")
        return None

"""
# Lấy dữ liệu từ Firestore
retrieved_request = get_request_from_firestore("req_001")
retrieved_driver = get_driver_from_firestore("002000000001")
retrieved_route = get_route_from_firestore("route_001")

# In ra màn hình
print(retrieved_request.__dict__) if retrieved_request else print("Không có request")
print(retrieved_driver.__dict__) if retrieved_driver else print("Không có driver")
print(retrieved_route.__dict__) if retrieved_route else print("Không có route")
"""