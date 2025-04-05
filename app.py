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

######################################################################################################################################
# ---------------------------------------------------------------------------
# 2) XÁC THỰC FIREBASE ID TOKEN (nếu cần)
# ---------------------------------------------------------------------------
def verify_firebase_token(req):
    """Xác thực Firebase ID Token từ header Authorization"""
    id_token = req.headers.get("Authorization")
    if not id_token:
        return None
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception:
        return None
# ---------------------------------------------------------------------------
# 3) API: LƯU THÔNG TIN NGƯỜI DÙNG (ví dụ cho profile)
# ---------------------------------------------------------------------------
@app.route("/save-user-info", methods=["POST"])
def save_user_info():
    """Lưu thông tin bổ sung của user vào Firestore."""
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    uid = user["uid"]
    try:
        db.collection("Users").document(uid).set(
            {"additional_info": data.get("additional_info", {})}, merge=True
        )
        return jsonify({"message": "User info saved"}), 200
    except Exception as e:
        app.logger.error(f"Error saving user info: {str(e)}")
        return jsonify({"error": str(e)}), 400
# ---------------------------------------------------------------------------
# 4) API: GỬI THÔNG BÁO FCM
# ---------------------------------------------------------------------------
@app.route("/send_notification", methods=["POST"])
def send_notification():
    """Gửi thông báo FCM đến danh sách tài xế."""
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    driver_ids = data.get("driver_ids", [])
    title = data.get("title", "Notification")
    body = data.get("body", "Hello from system")

    if not driver_ids:
        return jsonify({"error": "Missing driver_ids"}), 400

    tokens = []
    for driver_id in driver_ids:
        driver_doc = db.collection("Users").document(driver_id).get()
        if driver_doc.exists:
            driver_data = driver_doc.to_dict()
            if "fcm_token" in driver_data:
                tokens.append(driver_data["fcm_token"])

    if not tokens:
        return jsonify({"error": "No valid FCM tokens"}), 400

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body), tokens=tokens
    )
    response = messaging.send_multicast(message)
    return (
        jsonify({"message": f"Notification sent to {response.success_count} drivers"}),
        200,
    )
########################################################################################################################################

# ---------------------------------------------------------------------------
# 5) HÀM: LƯU KẾT QUẢ VÀO FIRESTORE và hàm chuyển đổi flatten
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
    finished_at = datetime.now(timezone.utc).isoformat()

    for date_str, vehicles in full_results.items():
        if not vehicles:
            continue

        for vehicle in vehicles:
            vehicle_id = vehicle.get("vehicle_id")
            if vehicle_id is None or vehicle_id == "":
                continue

            vehicle_id_str = str(vehicle_id)
            max_distance = vehicle.get("max_distance")
            safe_date = date_str.replace(".", "_")

            # Rút gọn mỗi route trong danh sách
            raw_routes = vehicle.get("routes", [])
            simplified_routes = []
            for r in raw_routes:
                simplified_route = {
                    "arrival_time": r.get("arrival_time"),
                    "capacity": r.get("capacity"),
                    "delivered": r.get("delivered"),
                    "destination": r.get("destination"),
                    "node": r.get("node"),
                    "request": r.get("request", {}).get("request_id") if r.get("request") else None
                }
                simplified_routes.append(simplified_route)

            doc_id = f"{safe_date}_vehicle_{vehicle_id_str}"
            route_doc = {
                "date": date_str,
                "vehicle_id": vehicle_id_str,
                "route": simplified_routes,
                "total_distance": max_distance,
                "last_update": finished_at
            }

            db.collection("Routes").document(doc_id).set(route_doc, merge=True)

    print("✅ Saved vehicle routes to Firestore (Routes collection, simplified format).")


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
# 6) HÀM: CHẠY PIPELINE (tải Excel → chuyển Excel thành JSON → chạy thuật toán)
# ---------------------------------------------------------------------------
# def run_pipeline(job_id):
#     """
#     Pipeline thực hiện các bước:
    
#       1. Tải file Excel xuống (script Get_data_from_storage.py sẽ đọc file data/excel_info.json)
#       2. Chuyển Excel thành JSON qua read_excel.py.
#       3. Chạy thuật toán OR-Tools qua engine1_lean.py.
#       4. Định dạng lại output, bổ sung execution_time và finished_at.
#       5. Chuyển json thành file excel
#       6. Đẩy file excel lên storage
#       7. Lấy file excel đã sửa bởi nhân viên điều xe
#       8. chuyển file excel sang json
#       9a. accept_accumulated_distance
#       9b. lưu vào firestore
    
#     """
#     # Bước 1: Tải file Excel xuống
#     subprocess.run(["python", "Get_data_from_storage.py"], check=True)

#     # Bước 2: Chuyển đổi Excel sang JSON
#     subprocess.run(["python", "read_excel.py"], check=True)

#     # Bước 3: Chạy thuật toán OR-Tools và ghi kết quả vào file output_{job_id}.json
#     tstart = perf_counter()
#     output_file = f"data/output_{job_id}.json"
#     with open(output_file, "w", encoding="utf-8") as out_f:
#         process = subprocess.Popen(
#             ["python", "engine1_lean.py"], stdout=out_f
#         )
#         memory_usage = 0
#         while process.poll() is None:
#             try:
#                 info = psutil.Process(process.pid).memory_info()
#                 memory_usage = max(memory_usage, info.rss)
#             except psutil.NoSuchProcess:
#                 break
#         process.wait()
#     run_time = perf_counter() - tstart

#     # Bước 4: Định dạng lại output
#     full_results = read_output(output_file)
#     if full_results is None:
#         raise Exception("Failed to parse output file using read_output.")
#     finished_at = datetime.now(timezone.utc).isoformat()
#     for day_result in full_results:
#         day_result["execution_time"] = f"{run_time:.2f} s"
#         day_result["finished_at"] = finished_at

#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(full_results, f, ensure_ascii=False, indent=2)

#     # Bước 5: Tạo dict vehicles_data từ full_results
#     vehicles_data = {}
#     for day_result in full_results:
#         vehicles = day_result.get("vehicles", {})
#         for drv_id, drv_info in vehicles.items():
#             if drv_id not in vehicles_data:
#                 vehicles_data[drv_id] = {
#                     "distance_of_route": drv_info.get("distance_of_route", 0),
#                     "list_of_route": drv_info.get("list_of_route", []),
#                 }
#             else:
#                 vehicles_data[drv_id]["distance_of_route"] += drv_info.get(
#                     "distance_of_route", 0
#                 )
#                 vehicles_data[drv_id]["list_of_route"].extend(
#                     drv_info.get("list_of_route", [])
#                 )

#     # Bước 6: Lưu kết quả vào Firestore
#     save_to_firestore(job_id, vehicles_data)
#     return run_time, memory_usage
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
    """
    Pipeline thực hiện các bước:
      1. Tải file Excel xuống (script Get_data_from_storage.py sẽ đọc file data/excel_info.json)
      2. Chuyển Excel thành JSON qua read_excel.py.
      3. Chạy thuật toán OR-Tools qua engine1_lean.py.
      4. Định dạng lại output, bổ sung execution_time và finished_at.
      5. Chuyển JSON thành file Excel.
      6. Đẩy file Excel lên Storage.
      
      (Các bước 7,8,9a,9b chưa được thực hiện.)
    """

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

    # --- BẮC 5: Lưu JSON output vào Firestore ---
    # Chuyển full_results (cấu trúc theo ngày) thành danh sách các request tuyến đường
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

    # --- BẮC 6: Chuyển JSON thành file Excel ---
    # Sử dụng hàm read_json_output_file từ post_process để xuất file Excel theo cấu trúc mong muốn
    # File Excel sẽ được lưu vào thư mục "data/output_excel"
    output_excel_dir = "data/output_excel"
    os.makedirs(output_excel_dir, exist_ok=True)
    read_json_output_file(filename=r"D:\Project 70\Project-70m\data\test\2025-02-19_00-00-00.json")

    # --- BẮC 7: Đẩy file Excel lên Firebase Storage ---
    # Lấy danh sách tất cả file Excel vừa được tạo
    excel_files = glob.glob(os.path.join(output_excel_dir, "*.xlsx"))
    # uploaded_urls = []
    for file_path in excel_files:
        # Sử dụng hàm push_excel_to_storage1 đã định nghĩa sẵn (nếu cần, bạn có thể thay bằng push_excel_to_storage2)
        push_excel_to_storage1(file_path)
        # Sau khi upload, lấy blob và tạo signed URL (ví dụ 1 giờ hiệu lực)
        # blob = storage.bucket().blob(f"initexcel/{os.path.basename(file_path)}")
        # url = blob.generate_signed_url(timedelta(hours=1))
        # uploaded_urls.append(url)
    return run_time, memory_usage

# ---------------------------------------------------------------------------
# 7) API /optimize: CHẠY PIPELINE, GHI excel_url, GỬI THÔNG BÁO FCM & TRẢ KẾT QUẢ
# ---------------------------------------------------------------------------
@app.route("/optimize", methods=["POST", "OPTIONS"])
def optimize():
    # Xử lý preflight request cho CORS
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        return response, 200

    # Nhận và log dữ liệu JSON từ request
    data = request.json or {}
    print("Received JSON:", data)

    excel_url = data.get("excel_url")
    if not excel_url:
        return jsonify({"error": "excel_url is required"}), 400

    # --- Xử lý tên file từ excel_url ---
    # Ví dụ: excel_url có dạng ".../o/requests_xlsx%2FLenh_Dieu_xe.xlsx?alt=media&token=..."
    parsed_url = urllib.parse.urlparse(excel_url)
    encoded_path = parsed_url.path.split("/o/")[
        -1
    ]  # Lấy phần "requests_xlsx%2FLenh_Dieu_xe.xlsx"
    decoded_path = urllib.parse.unquote(
        encoded_path
    )  # Ví dụ: "requests_xlsx/Lenh_Dieu_xe.xlsx"
    actual_file_name = decoded_path.split("/")[-1]
    print("Extracted file name from URL:", actual_file_name)
    # ----------------------------------------------------------------

    # Ghi thông tin excel_url và file_name vào file excel_info.json để Get_data_from_storage.py có thể sử dụng
    os.makedirs("data", exist_ok=True)
    excel_info = {"excel_url": excel_url, "file_name": actual_file_name}
    with open("data/excel_info.json", "w", encoding="utf-8") as info_file:
        json.dump(excel_info, info_file, ensure_ascii=False, indent=2)

    # Lấy job_id từ request hoặc tạo mới dựa trên timestamp
    job_id = data.get("job_id", str(datetime.now(timezone.utc).timestamp()))

    try:
        run_time, memory_usage = run_pipeline(job_id)
    except subprocess.CalledProcessError as e:
        return (
            jsonify({"error": f"Script execution failed: {e.stderr or e.stdout}"}),
            500,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Gửi thông báo FCM tới topic "dispatch_updates"
    try:
        msg = messaging.Message(
            notification=messaging.Notification(
                title="Optimization Completed",
                body=f"Job {job_id} finished in {run_time:.2f}s.",
            ),
            topic="dispatch_updates",
        )
        messaging.send(msg)
    except Exception as e:
        print("FCM error:", str(e))

    return (
        jsonify(
            {
                "job_id": job_id,
                "status": "completed",
                "execution_time": f"{run_time:.2f} s",
                "memory_usage": memory_usage,
            }
        ),
        200,
    )


# ---------------------------------------------------------------------------
# 8) API: CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
# ---------------------------------------------------------------------------
@app.route("/update_delivery_status", methods=["POST"])
def update_delivery_status():
    """API cho tài xế cập nhật trạng thái đơn hàng."""
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    request_id = data.get("request_id")
    new_status = data.get("delivery_status")

    if not request_id or new_status not in [1, 2, 3]:
        return jsonify({"error": "Invalid request"}), 400

    request_ref = db.collection("Requests").document(request_id)
    request_ref.update(
        {
            "delivery_status": new_status,
            "delivery_time": datetime.now(timezone.utc).isoformat(),
        }
    )

    return jsonify({"message": "Delivery status updated"}), 200
# ---------------------------------------------------------------------------
# 9) API: TẠO FILE EXCEL (GỌI HÀM init_excel từ initexcel.py)
# ---------------------------------------------------------------------------
from config import DATES
from initExcel import init_excel

import os

def push_excel_to_storage2(file_path):
    """Đẩy file Excel lên Firebase Storage, vào thư mục 'initexcel'."""
    # Tên file
    file_name = os.path.basename(file_path)

    # Lấy bucket mặc định (đã initialize_app ở trên)
    bucket = storage.bucket()

    # Đường dẫn = initexcel/<tên_file>
    blob = bucket.blob(f"initexcel/{file_name}")

    # Upload file
    blob.upload_from_filename(
        file_path,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    print(f"✅ Đã upload '{file_name}' lên 'initexcel' trong Firebase Storage.")


# @app.route("/create_excel", methods=["POST", "OPTIONS"])
# def create_excel():
#     # Xử lý preflight request cho CORS
#     if request.method == "OPTIONS":
#         response = make_response()
#         response.headers.add("Access-Control-Allow-Origin", "*")
#         response.headers.add(
#             "Access-Control-Allow-Headers", "Content-Type,Authorization"
#         )
#         response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
#         return response, 200

#     data = request.json or {}
#     # Lấy các tham số nếu có: day và is_recreate
    
#     day = data.get("day")  # nếu không cung cấp, init_excel sẽ dùng giá trị mặc định
#     is_recreate = data.get("is_recreate", False)

#     try:
#         # Gọi hàm init_excel để tạo file Excel
#         for i in range(len(DATES)):
#             result_message = init_excel(day=DATES[i], is_recreate= bool(i==0))
#         push_excel_to_storage("data\input\Lenh_Dieu_Xe.xlsx")
#         return jsonify({"message": result_message}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
 # Thêm import datetime nếu chưa có

@app.route("/create_excel", methods=["POST", "OPTIONS"])
def create_excel():
    # Xử lý preflight request cho CORS
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        return response, 200

    data = request.json or {}
    # Lấy các tham số nếu có: day và is_recreate
    day = data.get("day")  # nếu không cung cấp, init_excel sẽ dùng giá trị mặc định
    is_recreate = data.get("is_recreate", False)

    try:
        # Gọi hàm init_excel để tạo file Excel
        for i in range(len(DATES)):
            result_message = init_excel(day=DATES[i], is_recreate= bool(i==0))
        
        # Upload file (giữ nguyên logic cũ)
        push_excel_to_storage2("data\input\Lenh_Dieu_Xe.xlsx")
        
        # Sau khi upload, tạo blob tham chiếu đến file vừa upload
        bucket = storage.bucket()
        blob = bucket.blob("requests_xlsx/Lenh_Dieu_Xe.xlsx")
        
        # Tạo download URL có hiệu lực 1 giờ
        download_url = blob.generate_signed_url(datetime.timedelta(hours=1))
        
        return jsonify({"message": result_message, "download_url": download_url}), 200

    except Exception as e:
        app.logger.error(f"Error creating excel: {str(e)}")
        return jsonify({"error": str(e)}), 500

    


# # ---------------------------------------------------------------------------
# # THÊM ROUTE MẶC ĐỊNH ĐỂ PHỤC VỤ TRUY CẬP
# # ---------------------------------------------------------------------------
@app.route("/")
def index():
    return "API is running", 200
# # import os
# # import datetime
# # import firebase_admin
# # from firebase_admin import storage
# # from flask import request, jsonify, make_response

# # # Ví dụ: file local là "data/input/Lenh_Dieu_xe.xlsx"
# # def push_excel_to_storage(file_name):
# #     """
# #     Đẩy file Excel lên Firebase Storage và trả về download URL.
# #     Tham số file_name nên là phần đường dẫn bên trong thư mục "data", ví dụ "input/Lenh_Dieu_xe.xlsx".
# #     """
# #     # Tạo đường dẫn file local: "data/input/Lenh_Dieu_xe.xlsx"
# #     local_file_path = os.path.join("data", file_name)
    
# #     # Lấy bucket mặc định (đã khởi tạo Firebase Admin)
# #     bucket = firebase_admin.storage.bucket()
    
# #     # Lấy tên file cơ bản để lưu trong Storage, ví dụ "Lenh_Dieu_xe.xlsx"
# #     blob = bucket.blob(f"excel/{os.path.basename(file_name)}")
    
# #     # Upload file lên Firebase Storage
# #     blob.upload_from_filename(
# #         local_file_path,
# #         content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# #     )
# #     print(f"File {file_name} uploaded to Firebase Storage.")
    
# #     # Tạo download URL có hiệu lực 1 giờ
# #     download_url = blob.generate_signed_url(datetime.timedelta(hours=1))
# #     return download_url

# @app.route("/create_excel", methods=["POST", "OPTIONS"])
# def create_excel():
#     # Xử lý preflight request cho CORS
#     if request.method == "OPTIONS":
#         response = make_response()
#         response.headers.add("Access-Control-Allow-Origin", "*")
#         response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
#         response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
#         return response, 200


#     data = request.json or {}
#     day = data.get("day")  # nếu có, dùng để tạo file theo ngày
#     is_recreate = data.get("is_recreate", False)

#     try:
#         # Gọi hàm tạo file Excel
#         if day:
#             result_message = init_excel(day=day, is_recreate=is_recreate)
#         else:
#             for i in range(len(DATES)):
#                 result_message = init_excel(day=DATES[i], is_recreate=(i==0))
        
#         # Upload file lên Firebase Storage và nhận download URL
#         # Lưu ý: Vì file local là "data/input/Lenh_Dieu_xe.xlsx", nên gọi push_excel_to_storage với "input/Lenh_Dieu_xe.xlsx"
#         download_url = push_excel_to_storage("input/Lenh_Dieu_Xe.xlsx")
#         return jsonify({"message": result_message, "download_url": download_url}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route("/robots.txt")
def robots_txt():
    return "", 200, {"Content-Type": "text/plain"}


@app.route("/favicon.ico")
def favicon():
    return "", 200, {"Content-Type": "image/x-icon"}


# ---------------------------------------------------------------------------
# CHẠY APP
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
