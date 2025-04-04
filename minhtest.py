import json
import os
import subprocess
import urllib.parse
from datetime import datetime, timezone, timedelta  
import glob
from time import perf_counter
import firebase_admin
import psutil
from firebase_admin import auth, credentials, firestore, messaging, storage
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from post_process import *

app = Flask(__name__)
# ---------------------------------------------------------------------------
# 1) KHỞI ĐỘNG FIREBASE ADMIN
# ---------------------------------------------------------------------------
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'logistic-project-30dcd.firebasestorage.app'
})
db = firestore.client()
CORS(app) 

def flatten_output_json(full_results):
    """
    Hàm flatten_output_json sẽ duyệt qua toàn bộ kết quả định tuyến (full_results),
    với mỗi ngày (key của full_results) và với mỗi xe, duyệt qua danh sách các tuyến (routes).
    
    Với mỗi tuyến có chứa thông tin request:
      - Gán trường "date" của request bằng ngày hiện tại (key của full_results).
      - Nếu chưa có "original_request_id", gán bằng giá trị của "request_id" từ input.
      - Không thay đổi giá trị "request_id" (giữ nguyên id gốc).
      - Tạo bản ghi flattened với một số trường cơ bản và merge toàn bộ thông tin request.
    
    Trả về danh sách flattened requests.
    """
    flattened_requests = []

    for date_str, vehicles in full_results.items():
        if not vehicles:
            continue  # Bỏ qua nếu không có dữ liệu xe
        
        for vehicle in vehicles:
            vehicle_id = vehicle.get("vehicle_id")
            routes = vehicle.get("routes") or []  # Nếu không có routes thì dùng list rỗng
            for route in routes:
                req_info = route.get("request")
                if not req_info:
                    continue

                # Gán lại ngày cho request theo key của full_results
                req_info["date"] = date_str

                # Nếu chưa có original_request_id, gán bằng giá trị request_id ban đầu
                if not req_info.get("original_request_id"):
                    req_info["original_request_id"] = req_info.get("request_id", "")

                # Lưu ý: Không cập nhật lại request_id để giữ nguyên id gốc từ input

                # Tạo bản ghi flattened gồm một số trường cơ bản và merge toàn bộ thông tin trong req_info
                flattened = {
                    "request_id": req_info.get("request_id", ""),
                    "original_request_id": req_info.get("original_request_id", ""),
                    "staff_id": req_info.get("staff_id"),
                    "vehicle_id": vehicle_id,
                    "arrival_time": route.get("arrival_time"),
                    "capacity": route.get("capacity"),
                    "delivered": route.get("delivered"),
                    "destination": route.get("destination"),
                    "date": date_str,
                }
                # Merge tất cả thông tin từ request (nếu có các trường khác)
                flattened.update(req_info)
                flattened_requests.append(flattened)

    print(f"✅ Flattened {len(flattened_requests)} requests.")
    return flattened_requests

# ---------------------------------------------------------------------------
# Hàm lưu dữ liệu vào Firestore: lưu vào collections "Requests", "Drivers" và "Routes"
# ---------------------------------------------------------------------------
def save_to_firestore(requests_list, full_results):
    from datetime import datetime, timezone
    finished_at = datetime.now(timezone.utc).isoformat()

    # 1. Lưu từng request vào collection "Requests"
    for req in requests_list:
        request_id = req["request_id"]
        db.collection("Requests").document(request_id).set(req, merge=True)

    # 2. Gom request_id theo staff_id và ngày để cập nhật collection "Drivers"
    driver_routes_map = {}  # { staff_id_str -> { date_str -> [request_ids, ...] } }
    for req in requests_list:
        staff_id = req.get("staff_id")
        date_str = req.get("date")
        if staff_id is None or date_str is None:
            continue
        staff_id_str = str(staff_id)
        if staff_id_str not in driver_routes_map:
            driver_routes_map[staff_id_str] = {}
        if date_str not in driver_routes_map[staff_id_str]:
            driver_routes_map[staff_id_str][date_str] = []
        driver_routes_map[staff_id_str][date_str].append(req["request_id"])

    # Cập nhật collection "Drivers"
    for staff_id_str, date_dict in driver_routes_map.items():
        driver_ref = db.collection("Drivers").document(staff_id_str)
        update_data = {
            "available": True,
            "last_update": finished_at
        }
        for date_str, req_ids in date_dict.items():
            safe_date = date_str.replace(".", "_")
            update_data[f"route_by_day.{safe_date}"] = firestore.ArrayUnion(req_ids)
        driver_ref.set(update_data, merge=True)

    # 3. Gom theo (date, vehicle_id) để lưu vào collection "Routes"
    route_data_map = {}  # { (date_str, vehicle_id) -> [request, ...] }
    for req in requests_list:
        date_str = req.get("date")
        vehicle_id = req.get("vehicle_id")
        if date_str is None or vehicle_id is None:
            continue
        key = (date_str, vehicle_id)
        if key not in route_data_map:
            route_data_map[key] = []
        route_data_map[key].append(req)

    for key, reqs in route_data_map.items():
        date_str, vehicle_id = key
        total_distance = None
        vehicles_for_day = full_results.get(date_str, [])
        for v in vehicles_for_day:
            if v.get("vehicle_id") == vehicle_id:
                total_distance = v.get("max_distance")
                break
        safe_date = date_str.replace(".", "_")
        doc_id = f"{safe_date}_vehicle_{vehicle_id}"
        route_doc = {
            "date": date_str,
            "vehicle_id": vehicle_id,
            "route": reqs,
            "total_distance": total_distance,
            "last_update": finished_at
        }
        db.collection("Routes").document(doc_id).set(route_doc, merge=True)

    print("✅ Saved all data to Firestore: Requests, Drivers, and Routes.")


def push_excel_to_storage1(file_path):
    """Đẩy file Excel lên Firebase Storage, vào thư mục 'initexcel'."""
    # Tên file
    file_name = os.path.basename(file_path)

    # Lấy bucket mặc định (đã initialize_app ở trên)
    bucket = storage.bucket()

    # Đường dẫn = initexcel/<tên_file>
    blob = bucket.blob(f"expect_schedule/{file_name}")

    # Upload file
    blob.upload_from_filename(
        file_path,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    print(f"✅ Đã upload '{file_name}' lên 'initexcel' trong Firebase Storage.")

def run_pipeline(job_id):
    # Bước 1: Tải file Excel xuống
    subprocess.run(["python", "Get_data_from_storage.py"], check=True)
    

    # Bước 2: Chuyển đổi Excel sang JSON
    subprocess.run(["python", "read_excel.py"], check=True)

    # Bước 3: Chạy thuật toán OR-Tools và ghi kết quả vào file output_{job_id}.json
    tstart = perf_counter()
    output_file = f"data/output/output_{job_id}.txt"
    with open(output_file, "w", encoding="utf-8") as out_f:
        process = subprocess.Popen(["python", "engine1_lean.py"], stdout=out_f)
        memory_usage = 0
        while process.poll() is None:
            try:
                info = psutil.Process(process.pid).memory_info()
                memory_usage = max(memory_usage, info.rss)
            except psutil.NoSuchProcess:
                break
        process.wait()
    run_time = perf_counter() - tstart

    # Bước 4: Định dạng lại output, bổ sung execution_time và finished_at
    full_results = read_and_save_json_output(output_file)
    if full_results is None:
        raise Exception("Failed to parse output file using read_output.")


    # --- BẮC 5: Lưu JSON output vào Firestore ---
    requests_list = flatten_output_json(full_results)
    print("DEBUG requests_list =", requests_list)
    save_to_firestore(requests_list,full_results)    

    # --- BẮC 6: Chuyển JSON thành file Excel ---
    # output_excel_dir = "data/output_excel"
    # os.makedirs(output_excel_dir, exist_ok=True)
    # read_json_output_file(filename=r"D:\Project 70\Project-70m\data\test\2025-02-19_00-00-00.json")
    return run_time, memory_usage  

if __name__ == "__main__":
    run_pipeline(job_id="test_job_id")