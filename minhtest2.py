import json
import os
import subprocess
from datetime import datetime, timezone
from time import perf_counter
import psutil

import firebase_admin
from firebase_admin import credentials, firestore, storage
from flask import Flask
from flask_cors import CORS

# Hàm hỗ trợ đọc output file thành full_results
from post_process import read_and_save_json_output

# ---------------------------------------------------------------------------
# KHỞI TẠO FIREBASE ADMIN
# ---------------------------------------------------------------------------
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'logistic-project-30dcd.firebasestorage.app'
})
db = firestore.client()

app = Flask(__name__)
CORS(app)


# ---------------------------------------------------------------------------
# 1) Hàm FLATTEN dữ liệu -> Requests
# ---------------------------------------------------------------------------
def flatten_output_json(full_results):
    """
    Duyệt qua full_results theo từng ngày, mỗi vehicle, và từng route:
      - Tạo list request, gắn date, vehicle_id, arrival_time, delivered...
      - Lưu ý: original_request_id = request_id nếu chưa có.
    """
    flattened_requests = []
    for date_str, vehicles in full_results.items():
        if not vehicles:
            continue
        for vehicle in vehicles:
            vehicle_id = vehicle.get("vehicle_id")
            routes = vehicle.get("routes") or []
            for route in routes:
                req_info = route.get("request")
                if not req_info:
                    continue

                # Gán date và original_request_id
                req_info["date"] = date_str
                if not req_info.get("original_request_id"):
                    req_info["original_request_id"] = req_info.get("request_id", "")

                # Tạo bản ghi flattened
                flattened = {
                    "request_id": req_info.get("request_id", ""),
                    "original_request_id": req_info.get("original_request_id", ""),
                    "vehicle_id": vehicle_id,
                    "arrival_time": route.get("arrival_time"),
                    "capacity": route.get("capacity"),
                    "delivered": route.get("delivered"),
                    "destination": route.get("destination"),
                    "date": date_str,
                    "status": "scheduled"  # Mặc định, cập nhật sau nếu cần
                }
                # Gộp thêm các field còn lại trong req_info
                flattened.update(req_info)

                flattened_requests.append(flattened)

    print(f"✅ Flattened {len(flattened_requests)} requests.")
    return flattened_requests


# ---------------------------------------------------------------------------
# 2) Lưu danh sách request vào collection "Requests"
# ---------------------------------------------------------------------------
def save_requests_to_firestore(requests_list):
    """
    Lưu từng request vào Firestore collection "Requests".
    Document ID = request_id.
    """
    for req in requests_list:
        request_id = req["request_id"]
        db.collection("Requests").document(request_id).set(req, merge=True)

    print("✅ Saved all requests to Firestore (Requests collection).")


# ---------------------------------------------------------------------------
# 3) Lưu route của mỗi vehicle (theo ngày) vào collection "Routes"
# ---------------------------------------------------------------------------
def save_routes_to_firestore(full_results):
    """
    Duyệt full_results theo từng ngày -> từng vehicle:
      - Tạo doc_id = "{safe_date}_vehicle_{vehicle_id}" trong collection "Routes"
      - Lưu nguyên danh sách route (vehicle_routes) + total_distance
    """
    finished_at = datetime.now(timezone.utc).isoformat()

    for date_str, vehicles in full_results.items():
        if not vehicles:
            continue
        for vehicle in vehicles:
            vehicle_id = vehicle.get("vehicle_id")
            vehicle_routes = vehicle.get("routes", [])
            max_distance = vehicle.get("max_distance")

            safe_date = date_str.replace(".", "_")
            doc_id = f"{safe_date}_vehicle_{vehicle_id}"

            route_doc = {
                "date": date_str,
                "vehicle_id": vehicle_id,
                "route": vehicle_routes,
                "total_distance": max_distance,
                "last_update": finished_at
            }
            db.collection("Routes").document(doc_id).set(route_doc, merge=True)

    print("✅ Saved vehicle routes to Firestore (Routes collection).")


# ---------------------------------------------------------------------------
# 4) Lưu tóm tắt/dữ liệu vào collection "Vehicles"
#    + Subcollection "init" (hoặc "history") để lưu chi tiết route theo ngày
# ---------------------------------------------------------------------------
def save_vehicles_to_firestore(full_results):
    finished_at = datetime.now(timezone.utc).isoformat()
    for date_str, vehicles in full_results.items():
        if not vehicles:
            continue
        for vehicle in vehicles:
            vehicle_id = vehicle.get("vehicle_id")
            # Cho phép vehicle_id bằng 0, chỉ bỏ qua nếu là None hoặc chuỗi rỗng.
            if vehicle_id is None or vehicle_id == "":
                continue
            vehicle_id_str = str(vehicle_id)
            vehicle_routes = vehicle.get("routes", [])
            max_distance = vehicle.get("max_distance", 0)
            # Tạo một bản ghi lịch sử giao hàng cho xe đó
            history_record = {
                "vehicle_id": vehicle_id_str,
                "date": date_str,
                "route": vehicle_routes,
                "total_distance": max_distance,
                "last_update": finished_at
            }
            safe_date = date_str.replace(".", "_")
            # Lưu vào subcollection "history" của document vehicle_id
            db.collection("Vehicles").document(vehicle_id_str).collection("history")\
              .document(safe_date).set(history_record, merge=True)
            # Cập nhật thông tin tóm tắt vào document Vehicles (các trường mới nhất)
            db.collection("Vehicles").document(vehicle_id_str).set({
                "vehicle_id": vehicle_id_str,
                "last_update": finished_at,
                "last_date": date_str,
                "last_distance": max_distance
            }, merge=True)
    print("✅ Saved delivery history to Firestore (Vehicles collection with subcollection history).")


# ---------------------------------------------------------------------------
# 5) Hàm run_pipeline: thực hiện toàn bộ quy trình
# ---------------------------------------------------------------------------
def run_pipeline(job_id):
    """
    Pipeline gồm:
      1. Tải file Excel
      2. Chuyển Excel -> JSON
      3. Chạy OR-Tools (engine1_lean.py)
      4. Đọc output -> full_results
      5. Flatten -> Lưu Requests
      6. Lưu Routes
      7. Lưu Vehicles (top-level + subcollection "init")
    """
    # Bước 1: Tải file Excel từ Storage
    subprocess.run(["python", "Get_data_from_storage.py"], check=True)

    # Bước 2: Chuyển đổi Excel sang JSON
    subprocess.run(["python", "read_excel.py"], check=True)

    # Bước 3: Chạy thuật toán OR-Tools
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

    # Bước 4: Đọc file output -> full_results (dict)
    full_results = read_and_save_json_output(output_file)
    if full_results is None:
        raise Exception("Failed to parse output file using read_and_save_json_output.")

    # Bước 5: Lưu Requests (flatten)
    flattened_requests = flatten_output_json(full_results)
    save_requests_to_firestore(flattened_requests)

    # Bước 6: Lưu Routes (nguyên cấu trúc)
    save_routes_to_firestore(full_results)

    # Bước 7: Lưu Vehicles (tóm tắt + subcollection init)
    save_vehicles_to_firestore(full_results)

    print(f"✅ Pipeline completed in {run_time:.2f} seconds, max memory usage: {memory_usage} bytes.")
    return run_time, memory_usage


# ---------------------------------------------------------------------------
# Chạy pipeline khi file được thực thi trực tiếp
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    job_id = "test_job_id"
    run_pipeline(job_id)
