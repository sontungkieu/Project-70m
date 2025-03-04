import json
import os
import subprocess  # subprocess: Chạy script Python khác (dùng để chạy thuật toán tối ưu hóa).
from datetime import datetime, timezone
from time import perf_counter  # đo thời gian thực thi của thuật toán

import firebase_admin  # SDK của Firebase
import psutil  # psutil: Đo lường tài nguyên hệ thống (RAM, CPU, Disk).
from firebase_admin import (  # credentials: Xác thực Firebase.
    auth,
    credentials,
    firestore,
    messaging,
)
from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# 1) KHỞI ĐỘNG FIREBASE ADMIN
# ---------------------------------------------------------------------------
cred = credentials.Certificate(
    "firebase-key.json"
)  # Tạo đối tượng chứng chỉ từ file JSON
firebase_admin.initialize_app(cred)  # Khởi tạo Firebase Admin SDK
db = firestore.client()  # Kết nối Firestore để thao tác với cơ sở dữ liệu

app = Flask(__name__)  # Khởi tạo Flask app


# ---------------------------------------------------------------------------
# 2) XÁC THỰC FIREBASE ID TOKEN
# ---------------------------------------------------------------------------
def verify_firebase_token(request):
    """Xác thực Firebase ID Token từ header Authorization"""
    id_token = request.headers.get("Authorization")
    if not id_token:
        return None
    try:
        decoded_token = auth.verify_id_token(
            id_token
        )  # Xác thực token bằng auth.verify_id_token(id_token).
        return decoded_token
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 3) LƯU THÔNG TIN NGƯỜI DÙNG
# ---------------------------------------------------------------------------
@app.route("/save-user-info", methods=["POST"])
def save_user_info():
    """Lưu thông tin bổ sung của user vào Firestore."""
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    uid = user["uid"]  # uid là một chuỗi ID duy nhất của mỗi tài khoản Firebase.
    """
    db.collection("Users").document(uid).set({...}, merge=True):
    Truy cập collection "Users" trong Firestore.
    Lấy document tương ứng với uid (người dùng hiện tại).
    Cập nhật dữ liệu bằng phương thức .set().
    merge=True: Nếu document đã tồn tại, chỉ cập nhật dữ liệu mới mà không ghi đè toàn bộ document.
    data.get("additional_info", {}):
    Lấy giá trị của additional_info từ request JSON.
    Nếu additional_info không tồn tại, mặc định là {} (từ điển rỗng).
    """
    try:
        db.collection("Users").document(uid).set(
            {"additional_info": data.get("additional_info", {})}, merge=True
        )
        return jsonify({"message": "User info saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------------
# 4) GỬI THÔNG BÁO FCM
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
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens,
    )

    response = messaging.send_multicast(message)
    return (
        jsonify({"message": f"Notification sent to {response.success_count} drivers"}),
        200,
    )


# ---------------------------------------------------------------------------
# 5) CHẠY TỐI ƯU HÓA VÀ LƯU KẾT QUẢ THEO CẤU TRÚC MỚI
# ---------------------------------------------------------------------------
def save_to_firestore(job_id, vehicles_data):
    for vehicle_id, driver_data in vehicles_data.items():
        route_doc_id = f"{vehicle_id}_{job_id}"  #

        # Lưu tuyến đường vào collection "Routes"
        db.collection("Routes").document(route_doc_id).set(
            {
                "vehicle_id": vehicle_id,
                "route": driver_data.get("route", []),
                "total_distance": driver_data.get("total_distance", 0),
                "date": datetime.now(timezone.utc).isoformat(),  # ✅ Sửa lỗi utcnow()
            }
        )

        # Cập nhật thông tin lộ trình của tài xế trong collection "Drivers"
        driver_ref = db.collection("Drivers").document(vehicle_id)
        driver_ref.set(
            {"route_by_day": {job_id: driver_data.get("route", [])}},
            merge=True,
        )
        driver_ref.update(
            {
                "available": True,
                "last_update": datetime.now(
                    timezone.utc
                ).isoformat(),  # ✅ Sửa lỗi utcnow()
            }
        )


def run_optimization(job_id):
    """Chạy thuật toán tối ưu hóa và lưu kết quả vào Firestore."""
    tstart = perf_counter()
    if not os.path.exists("data"):
        os.makedirs("data")

    output_file = f"data/output_{job_id}.json"
    with open(output_file, "w") as out_f:
        process = subprocess.Popen(
            ["python", "test_bo_doi_cong_nghiep.py"],
            stdout=out_f,  # chuyển hướng đầu ra (output) của chương trình test_bo_doi_cong_nghiep.py vào file output_file
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

    # Đọc kết quả từ file output
    with open(output_file, "r", encoding="utf-8") as f:
        full_results = json.load(f)

    vehicles_data = {}
    for day_result in full_results:
        vehicles = day_result.get("vehicles", {})
        for drv_id, drv_info in vehicles.items():
            if drv_id in vehicles_data:
                vehicles_data[drv_id]["route"].extend(drv_info.get("route", []))
                vehicles_data[drv_id]["total_distance"] += drv_info.get(
                    "total_distance", 0
                )
            else:
                vehicles_data[drv_id] = drv_info
    save_to_firestore(job_id, vehicles_data)
    return run_time, memory_usage


@app.route("/optimize", methods=["POST"])
def optimize():
    """Chạy tối ưu hóa và gửi thông báo khi hoàn thành."""
    data = request.json or {}
    job_id = data.get(
        "job_id", str(datetime.now(timezone.utc).timestamp())
    )  # ✅ Sửa lỗi utcnow()
    run_time, memory_usage = run_optimization(job_id)

    msg = messaging.Message(
        notification=messaging.Notification(
            title="Optimization Completed",
            body=f"Job {job_id} finished in {run_time:.2f}s.",
        ),
        topic="dispatch_updates",
    )
    messaging.send(msg)

    return jsonify({"job_id": job_id, "status": "completed"}), 200


# ---------------------------------------------------------------------------
# 6) CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
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
            "delivery_time": datetime.now(
                timezone.utc
            ).isoformat(),  # ✅ Sửa lỗi utcnow()
        }
    )

    return jsonify({"message": "Delivery status updated"}), 200


# ---------------------------------------------------------------------------
# CHẠY APP
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
