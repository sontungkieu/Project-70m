# from flask import Flask, request, jsonify
# import firebase_admin
# from firebase_admin import credentials, firestore, messaging, auth
# from datetime import datetime, timezone
# import json
# import os
# import subprocess
# import psutil
# from time import perf_counter

# # Import hàm read_output từ file read_output.py để định dạng lại output
# from utilities.read_output import read_output
# # Import hàm chạy thuật toán từ test_bo_doi_cong_nghiep.py (giả sử hàm này được dùng trong pipeline)
# # Nếu hàm run_test_bo_doi_cong_nghiep được sử dụng trong pipeline, bạn có thể import nó
# # from test_bo_doi_cong_nghiep import run_test_bo_doi_cong_nghiep

# app = Flask(__name__)

# # ---------------------------------------------------------------------------
# # 1) KHỞI ĐỘNG FIREBASE ADMIN
# # ---------------------------------------------------------------------------
# cred = credentials.Certificate("firebase-key.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# # ---------------------------------------------------------------------------
# # 2) XÁC THỰC FIREBASE ID TOKEN (nếu cần)
# # ---------------------------------------------------------------------------
# def verify_firebase_token(req):
#     """Xác thực Firebase ID Token từ header Authorization"""
#     id_token = req.headers.get("Authorization")
#     if not id_token:
#         return None
#     try:
#         decoded_token = auth.verify_id_token(id_token)
#         return decoded_token
#     except Exception:
#         return None

# # ---------------------------------------------------------------------------
# # 3) API: LƯU THÔNG TIN NGƯỜI DÙNG (ví dụ cho profile)
# # ---------------------------------------------------------------------------
# @app.route('/save-user-info', methods=['POST'])
# def save_user_info():
#     """Lưu thông tin bổ sung của user vào Firestore."""
#     user = verify_firebase_token(request)
#     if not user:
#         return jsonify({"error": "Unauthorized"}), 401

#     data = request.json
#     uid = user["uid"]
#     try:
#         db.collection("Users").document(uid).set({
#             "additional_info": data.get("additional_info", {})
#         }, merge=True)
#         return jsonify({"message": "User info saved"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# # ---------------------------------------------------------------------------
# # 4) API: GỬI THÔNG BÁO FCM
# # ---------------------------------------------------------------------------
# @app.route('/send_notification', methods=['POST'])
# def send_notification():
#     """Gửi thông báo FCM đến danh sách tài xế."""
#     user = verify_firebase_token(request)
#     if not user:
#         return jsonify({"error": "Unauthorized"}), 401

#     data = request.json or {}
#     driver_ids = data.get('driver_ids', [])
#     title = data.get('title', "Notification")
#     body = data.get('body', "Hello from system")

#     if not driver_ids:
#         return jsonify({"error": "Missing driver_ids"}), 400

#     tokens = []
#     for driver_id in driver_ids:
#         driver_doc = db.collection("Users").document(driver_id).get()
#         if driver_doc.exists:
#             driver_data = driver_doc.to_dict()
#             if "fcm_token" in driver_data:
#                 tokens.append(driver_data["fcm_token"])

#     if not tokens:
#         return jsonify({"error": "No valid FCM tokens"}), 400

#     message = messaging.MulticastMessage(
#         notification=messaging.Notification(title=title, body=body),
#         tokens=tokens
#     )
#     response = messaging.send_multicast(message)
#     return jsonify({"message": f"Notification sent to {response.success_count} drivers"}), 200

# # ---------------------------------------------------------------------------
# # 5) HÀM: LƯU KẾT QUẢ VÀO FIRESTORE
# # ---------------------------------------------------------------------------
# def save_to_firestore(job_id, vehicles_data):
#     """
#     Lưu kết quả tối ưu hóa vào Firestore với collection "Routes" và cập nhật thông tin "Drivers".
#     Mỗi document trong "Routes" có ID: vehicle_id_job_id, chứa vehicle_id, distance_of_route,
#     list_of_route và finished_at.
#     """
#     for vehicle_id, driver_data in vehicles_data.items():
#         route_doc_id = f"{vehicle_id}_{job_id}"
#         db.collection("Routes").document(route_doc_id).set({
#             "vehicle_id": vehicle_id,
#             "distance_of_route": driver_data.get("distance_of_route", 0),
#             "list_of_route": driver_data.get("list_of_route", []),
#             "finished_at": datetime.now(timezone.utc).isoformat()
#         })
#         driver_ref = db.collection("Drivers").document(str(vehicle_id))
#         driver_ref.set({
#             "route_by_day": {job_id: driver_data.get("list_of_route", [])}
#         }, merge=True)
#         driver_ref.update({
#             "available": True,
#             "last_update": datetime.now(timezone.utc).isoformat()
#         })

# # ---------------------------------------------------------------------------
# # 6) HÀM: CHẠY PIPELINE (tải Excel → chuyển Excel thành JSON → chạy thuật toán)
# # ---------------------------------------------------------------------------
# def run_pipeline(job_id):
#     """
#     Pipeline thực hiện các bước:
#       1. Đọc excel_url từ file (đã được ghi bởi /optimize) và tải file Excel xuống thư mục data/input/.
#          (Script Get_data_from_storage.py sẽ đọc file data/excel_url.txt)
#       2. Chuyển Excel thành JSON qua read_excel.py.
#       3. Chạy thuật toán OR-Tools qua test_bo_doi_cong_nghiep.py, ghi kết quả vào file output_{job_id}.json.
#       4. Sử dụng read_output để định dạng lại kết quả, bổ sung execution_time và finished_at.
#       5. Tạo dict vehicles_data từ full_results và lưu vào Firestore.
#     """
#     # Bước 1: Gọi script Get_data_from_storage.py (script này sẽ tự đọc file data/excel_url.txt)
#     subprocess.run(['python', 'Get_data_from_storage.py'], check=True)

#     # Bước 2: Chuyển đổi Excel sang JSON (script read_excel.py sẽ xử lý file data/input/input.xlsx)
#     subprocess.run(['python', 'read_excel.py'], check=True)

#     # Bước 3: Chạy thuật toán OR-Tools và ghi kết quả vào file output_{job_id}.json
#     tstart = perf_counter()
#     output_file = f"data/output_{job_id}.json"
#     with open(output_file, 'w', encoding='utf-8') as out_f:
#         process = subprocess.Popen(['python', 'test_bo_doi_cong_nghiep.py'],
#                                      stdout=out_f)
#         memory_usage = 0
#         while process.poll() is None:
#             try:
#                 info = psutil.Process(process.pid).memory_info()
#                 memory_usage = max(memory_usage, info.rss)
#             except psutil.NoSuchProcess:
#                 break
#         process.wait()
#     run_time = perf_counter() - tstart

#     # Bước 4: Định dạng lại output bằng hàm read_output (từ file read_output.py)
#     full_results = read_output(output_file)
#     if full_results is None:
#         raise Exception("Failed to parse output file using read_output.")
#     finished_at = datetime.now(timezone.utc).isoformat()
#     for day_result in full_results:
#         day_result["execution_time"] = f"{run_time:.2f} s"
#         day_result["finished_at"] = finished_at

#     # (Nếu cần: ghi lại file output đã định dạng)
#     with open(output_file, 'w', encoding='utf-8') as f:
#         json.dump(full_results, f, ensure_ascii=False, indent=2)

#     # Bước 5: Tạo dict vehicles_data từ full_results
#     vehicles_data = {}
#     for day_result in full_results:
#         vehicles = day_result.get("vehicles", {})
#         for drv_id, drv_info in vehicles.items():
#             if drv_id not in vehicles_data:
#                 vehicles_data[drv_id] = {
#                     "distance_of_route": drv_info.get("distance_of_route", 0),
#                     "list_of_route": drv_info.get("list_of_route", [])
#                 }
#             else:
#                 vehicles_data[drv_id]["distance_of_route"] += drv_info.get("distance_of_route", 0)
#                 vehicles_data[drv_id]["list_of_route"].extend(drv_info.get("list_of_route", []))

#     # Bước 6: Lưu kết quả vào Firestore
#     save_to_firestore(job_id, vehicles_data)
#     return run_time, memory_usage

# # ---------------------------------------------------------------------------
# # 7) API /optimize: CHẠY PIPELINE, GHI excel_url & GỬI THÔNG BÁO FCM & TRẢ KẾT QUẢ
# # ---------------------------------------------------------------------------
# @app.route('/optimize', methods=['POST'])
# def optimize():
#     """
#     Endpoint /optimize:
#       - Nhận trường "excel_url" từ request và ghi vào file data/excel_url.txt
#       - Chạy pipeline: tải file Excel, chuyển đổi, chạy thuật toán, định dạng kết quả,
#         lưu kết quả vào Firestore
#       - Gửi thông báo FCM đến topic "dispatch_updates"
#       - Trả về kết quả chạy pipeline
#     """
#     data = request.json or {}
#     excel_url = data.get("excel_url")
#     if not excel_url:
#         return jsonify({"error": "excel_url is required"}), 400

#     # Ghi excel_url vào file để script Get_data_from_storage.py có thể đọc
#     os.makedirs("data", exist_ok=True)
#     with open('data/excel_url.txt', 'w', encoding='utf-8') as f:
#         f.write(excel_url)

#     # Sử dụng job_id được cung cấp hoặc tạo mới dựa trên timestamp
#     job_id = data.get("job_id", str(datetime.now(timezone.utc).timestamp()))

#     try:
#         run_time, memory_usage = run_pipeline(job_id)
#     except subprocess.CalledProcessError as e:
#         return jsonify({"error": f"Script execution failed: {e.stderr or e.stdout}"}), 500
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#     # Gửi thông báo FCM tới topic "dispatch_updates"
#     try:
#         msg = messaging.Message(
#             notification=messaging.Notification(
#                 title="Optimization Completed",
#                 body=f"Job {job_id} finished in {run_time:.2f}s."
#             ),
#             topic="dispatch_updates"
#         )
#         messaging.send(msg)
#     except Exception as e:
#         print("FCM error:", str(e))

#     return jsonify({
#         "job_id": job_id,
#         "status": "completed",
#         "execution_time": f"{run_time:.2f} s",
#         "memory_usage": memory_usage
#     }), 200

# # ---------------------------------------------------------------------------
# # 8) API: CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
# # ---------------------------------------------------------------------------
# @app.route('/update_delivery_status', methods=['POST'])
# def update_delivery_status():
#     """API cho tài xế cập nhật trạng thái đơn hàng."""
#     user = verify_firebase_token(request)
#     if not user:
#         return jsonify({"error": "Unauthorized"}), 401

#     data = request.json or {}
#     request_id = data.get("request_id")
#     new_status = data.get("delivery_status")

#     if not request_id or new_status not in [1, 2, 3]:
#         return jsonify({"error": "Invalid request"}), 400

#     request_ref = db.collection("Requests").document(request_id)
#     request_ref.update({
#         "delivery_status": new_status,
#         "delivery_time": datetime.now(timezone.utc).isoformat()
#     })

#     return jsonify({"message": "Delivery status updated"}), 200

# # ---------------------------------------------------------------------------
# # CHẠY APP
# # ---------------------------------------------------------------------------
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8080)
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, messaging, auth
from datetime import datetime, timezone
import json
import os
import subprocess
import psutil
from time import perf_counter
from flask_cors import CORS

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os, json, subprocess, psutil
from time import perf_counter
from datetime import datetime, timezone
# Các import liên quan tới firebase và firestore, FCM, v.v.
from firebase_admin import messaging
import urllib.parse

# Import hàm read_output từ file read_output.py để định dạng lại output
from utilities.read_output import read_output

app = Flask(__name__)

# ---------------------------------------------------------------------------
# 1) KHỞI ĐỘNG FIREBASE ADMIN
# ---------------------------------------------------------------------------
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
CORS(app)  # Cho phép CORS cho tất cả các domain

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
@app.route('/save-user-info', methods=['POST'])
def save_user_info():
    """Lưu thông tin bổ sung của user vào Firestore."""
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    uid = user["uid"]
    try:
        db.collection("Users").document(uid).set({
            "additional_info": data.get("additional_info", {})
        }, merge=True)
        return jsonify({"message": "User info saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------------------------------------------------------------------------
# 4) API: GỬI THÔNG BÁO FCM
# ---------------------------------------------------------------------------
@app.route('/send_notification', methods=['POST'])
def send_notification():
    """Gửi thông báo FCM đến danh sách tài xế."""
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    driver_ids = data.get('driver_ids', [])
    title = data.get('title', "Notification")
    body = data.get('body', "Hello from system")

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
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens
    )
    response = messaging.send_multicast(message)
    return jsonify({"message": f"Notification sent to {response.success_count} drivers"}), 200

# 5) HÀM: LƯU KẾT QUẢ VÀO FIRESTORE
# ---------------------------------------------------------------------------
def save_to_firestore(job_id, vehicles_data):
    """
    Lưu kết quả tối ưu hóa vào Firestore với collection "Routes" và cập nhật thông tin "Drivers".
    """
    for vehicle_id, driver_data in vehicles_data.items():
        route_doc_id = f"{vehicle_id}_{job_id}"
        db.collection("Routes").document(route_doc_id).set({
            "vehicle_id": vehicle_id,
            "distance_of_route": driver_data.get("distance_of_route", 0),
            "list_of_route": driver_data.get("list_of_route", []),
            "finished_at": datetime.now(timezone.utc).isoformat()
        })
        driver_ref = db.collection("Drivers").document(str(vehicle_id))
        driver_ref.set({
            "route_by_day": {job_id: driver_data.get("list_of_route", [])}
        }, merge=True)
        driver_ref.update({
            "available": True,
            "last_update": datetime.now(timezone.utc).isoformat()
        })

# ---------------------------------------------------------------------------
# 6) HÀM: CHẠY PIPELINE (tải Excel → chuyển Excel thành JSON → chạy thuật toán)
# ---------------------------------------------------------------------------
def run_pipeline(job_id):
    """
    Pipeline thực hiện các bước:
      1. Tải file Excel xuống (script Get_data_from_storage.py sẽ đọc file data/excel_info.json)
      2. Chuyển Excel thành JSON qua read_excel.py.
      3. Chạy thuật toán OR-Tools qua test_bo_doi_cong_nghiep.py.
      4. Định dạng lại output, bổ sung execution_time và finished_at.
      5. Tạo dict vehicles_data từ full_results và lưu vào Firestore.
    """
    # Bước 1: Tải file Excel xuống
    subprocess.run(['python', 'Get_data_from_storage.py'], check=True)

    # Bước 2: Chuyển đổi Excel sang JSON
    subprocess.run(['python', 'read_excel.py'], check=True)

    # Bước 3: Chạy thuật toán OR-Tools và ghi kết quả vào file output_{job_id}.json
    tstart = perf_counter()
    output_file = f"data/output_{job_id}.json"
    with open(output_file, 'w', encoding='utf-8') as out_f:
        process = subprocess.Popen(['python', 'test_bo_doi_cong_nghiep.py'], stdout=out_f)
        memory_usage = 0
        while process.poll() is None:
            try:
                info = psutil.Process(process.pid).memory_info()
                memory_usage = max(memory_usage, info.rss)
            except psutil.NoSuchProcess:
                break
        process.wait()
    run_time = perf_counter() - tstart

    # Bước 4: Định dạng lại output
    full_results = read_output(output_file)
    if full_results is None:
        raise Exception("Failed to parse output file using read_output.")
    finished_at = datetime.now(timezone.utc).isoformat()
    for day_result in full_results:
        day_result["execution_time"] = f"{run_time:.2f} s"
        day_result["finished_at"] = finished_at

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, ensure_ascii=False, indent=2)

    # Bước 5: Tạo dict vehicles_data từ full_results
    vehicles_data = {}
    for day_result in full_results:
        vehicles = day_result.get("vehicles", {})
        for drv_id, drv_info in vehicles.items():
            if drv_id not in vehicles_data:
                vehicles_data[drv_id] = {
                    "distance_of_route": drv_info.get("distance_of_route", 0),
                    "list_of_route": drv_info.get("list_of_route", [])
                }
            else:
                vehicles_data[drv_id]["distance_of_route"] += drv_info.get("distance_of_route", 0)
                vehicles_data[drv_id]["list_of_route"].extend(drv_info.get("list_of_route", []))

    # Bước 6: Lưu kết quả vào Firestore
    save_to_firestore(job_id, vehicles_data)
    return run_time, memory_usage

# ---------------------------------------------------------------------------
# 7) API /optimize: CHẠY PIPELINE, GHI excel_url, GỬI THÔNG BÁO FCM & TRẢ KẾT QUẢ
# ---------------------------------------------------------------------------
@app.route('/optimize', methods=['POST', 'OPTIONS'])
def optimize():
    # Xử lý preflight request cho CORS
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
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
    encoded_path = parsed_url.path.split('/o/')[-1]  # Lấy phần "requests_xlsx%2FLenh_Dieu_xe.xlsx"
    decoded_path = urllib.parse.unquote(encoded_path)  # Ví dụ: "requests_xlsx/Lenh_Dieu_xe.xlsx"
    actual_file_name = decoded_path.split('/')[-1]
    print("Extracted file name from URL:", actual_file_name)
    # ----------------------------------------------------------------

    # Ghi thông tin excel_url và file_name vào file excel_info.json để Get_data_from_storage.py có thể sử dụng
    os.makedirs("data", exist_ok=True)
    excel_info = {"excel_url": excel_url, "file_name": actual_file_name}
    with open('data/excel_info.json', 'w', encoding='utf-8') as info_file:
        json.dump(excel_info, info_file, ensure_ascii=False, indent=2)

    # Lấy job_id từ request hoặc tạo mới dựa trên timestamp
    job_id = data.get("job_id", str(datetime.now(timezone.utc).timestamp()))

    try:
        run_time, memory_usage = run_pipeline(job_id)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Script execution failed: {e.stderr or e.stdout}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Gửi thông báo FCM tới topic "dispatch_updates"
    try:
        msg = messaging.Message(
            notification=messaging.Notification(
                title="Optimization Completed",
                body=f"Job {job_id} finished in {run_time:.2f}s."
            ),
            topic="dispatch_updates"
        )
        messaging.send(msg)
    except Exception as e:
        print("FCM error:", str(e))

    return jsonify({
        "job_id": job_id,
        "status": "completed",
        "execution_time": f"{run_time:.2f} s",
        "memory_usage": memory_usage
    }), 200
# ---------------------------------------------------------------------------
# 8) API: CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
# ---------------------------------------------------------------------------
@app.route('/update_delivery_status', methods=['POST'])
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
    request_ref.update({
        "delivery_status": new_status,
        "delivery_time": datetime.now(timezone.utc).isoformat()
    })

    return jsonify({"message": "Delivery status updated"}), 200

# ---------------------------------------------------------------------------
# THÊM ROUTE MẶC ĐỊNH ĐỂ PHỤC VỤ TRUY CẬP
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return "API is running", 200

@app.route('/robots.txt')
def robots_txt():
    return "", 200, {"Content-Type": "text/plain"}

@app.route('/favicon.ico')
def favicon():
    return "", 200, {"Content-Type": "image/x-icon"}

# ---------------------------------------------------------------------------
# CHẠY APP
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)