import json
import os
import subprocess
import urllib.parse
from datetime import datetime, timezone
from time import perf_counter

import firebase_admin
import psutil

# Các import liên quan tới firebase và firestore, FCM, v.v.
from firebase_admin import auth, credentials, firestore, messaging

# # ---------------------------------------------------------------------------
# # CHẠY APP
# # ---------------------------------------------------------------------------
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8080)
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

# Import hàm read_output từ file read_output.py để định dạng lại output
from post_process import read_output

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


# 5) HÀM: LƯU KẾT QUẢ VÀO FIRESTORE
# ---------------------------------------------------------------------------
def save_to_firestore(job_id, requests_list):
    """
    Lưu kết quả tối ưu hóa (danh sách các request) vào Firestore.
    - Mỗi request được lưu vào collection "Requests" với document id là request_id.
    - Các request được nhóm theo staff_id và cập nhật vào collection "Drivers" dưới trường "route_by_day".
    """
    finished_at = datetime.now(timezone.utc).isoformat()
    # Dictionary để gom các request_id theo từng driver (staff_id)
    driver_routes = {}
    
    for req in requests_list:
        # Thêm thông tin job_id và finished_at vào mỗi request
        req["job_id"] = job_id
        req["finished_at"] = finished_at

        # Lưu request vào collection "Requests" (dùng request_id làm document id)
        request_id = req.get("request_id")
        if not request_id:
            raise ValueError("Mỗi request phải có trường 'request_id'")
        db.collection("Requests").document(request_id).set(req)

        # Gom nhóm các request theo driver (staff_id)
        staff_id = req.get("staff_id")
        if staff_id is not None:
            # Chuyển staff_id sang chuỗi để dùng làm document id
            driver_routes.setdefault(str(staff_id), []).append(request_id)
    
    # Cập nhật thông tin cho từng driver trong collection "Drivers"
    for staff_id, request_ids in driver_routes.items():
        driver_ref = db.collection("Drivers").document(staff_id)
        # Sử dụng set với merge=True để cập nhật hoặc tạo mới
        driver_ref.set({
            "route_by_day": { job_id: request_ids },
            "available": True,
            "last_update": finished_at
        }, merge=True)



# ---------------------------------------------------------------------------
# 6) HÀM: CHẠY PIPELINE (tải Excel → chuyển Excel thành JSON → chạy thuật toán)
# ---------------------------------------------------------------------------
def run_pipeline(job_id):
    """
    Pipeline thực hiện các bước:
    
      1. Tải file Excel xuống (script Get_data_from_storage.py sẽ đọc file data/excel_info.json)
      2. Chuyển Excel thành JSON qua read_excel.py.
      3. Chạy thuật toán OR-Tools qua engine1_lean.py.
      4. Định dạng lại output, bổ sung execution_time và finished_at.
      5. Chuyển json thành file excel
      6. Đẩy lên storage
      7. Lấy file excel đã sửa bởi nhân viên điều xe
      8. chuyển file excel sang json
      9a. accept_accumulated_distance
      9b. lưu vào firestore
    
    """
    # Bước 1: Tải file Excel xuống
    subprocess.run(["python", "Get_data_from_storage.py"], check=True)

    # Bước 2: Chuyển đổi Excel sang JSON
    subprocess.run(["python", "read_excel.py"], check=True)

    # Bước 3: Chạy thuật toán OR-Tools và ghi kết quả vào file output_{job_id}.json
    tstart = perf_counter()
    output_file = f"data/output_{job_id}.json"
    with open(output_file, "w", encoding="utf-8") as out_f:
        process = subprocess.Popen(
            ["python", "engine1_lean.py"], stdout=out_f
        )
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

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(full_results, f, ensure_ascii=False, indent=2)

    # Bước 5: Tạo dict vehicles_data từ full_results
    vehicles_data = {}
    for day_result in full_results:
        vehicles = day_result.get("vehicles", {})
        for drv_id, drv_info in vehicles.items():
            if drv_id not in vehicles_data:
                vehicles_data[drv_id] = {
                    "distance_of_route": drv_info.get("distance_of_route", 0),
                    "list_of_route": drv_info.get("list_of_route", []),
                }
            else:
                vehicles_data[drv_id]["distance_of_route"] += drv_info.get(
                    "distance_of_route", 0
                )
                vehicles_data[drv_id]["list_of_route"].extend(
                    drv_info.get("list_of_route", [])
                )

    # Bước 6: Lưu kết quả vào Firestore
    save_to_firestore(job_id, vehicles_data)
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
def push_excel_to_storage(file_name):
    """Đẩy file Excel lên Firebase Storage."""
    # Đường dẫn tới file Excel
    local_file_path = os.path.join("data", file_name)

    # Đường dẫn tới Firebase Storage
    bucket = firebase_admin.storage.bucket()
    blob = bucket.blob(f"excel/{file_name}")

    # Đẩy file lên Firebase Storage
    blob.upload_from_filename(local_file_path, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    print(f"File {file_name} uploaded to Firebase Storage.")
@app.route("/create_excel", methods=["POST", "OPTIONS"])
def create_excel():
    # Xử lý preflight request cho CORS
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        return response, 200

    # (Tùy chọn) Xác thực người dùng
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    # Lấy các tham số nếu có: day và is_recreate
    
    day = data.get("day")  # nếu không cung cấp, init_excel sẽ dùng giá trị mặc định
    is_recreate = data.get("is_recreate", False)

    try:
        # Gọi hàm init_excel để tạo file Excel
        if day:
            result_message = init_excel(day=day, is_recreate=is_recreate)
        else:
            for i in range(len(DATES)):
                result_message = init_excel(day=DATES[i], is_recreate= bool(i==0))
            push_excel_to_storage("data\input\Lenh_Dieu_xe.xlsx")
        return jsonify({"message": result_message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 

    


# ---------------------------------------------------------------------------
# THÊM ROUTE MẶC ĐỊNH ĐỂ PHỤC VỤ TRUY CẬP
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return "API is running", 200


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
