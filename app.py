from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, messaging, auth
import subprocess
from time import perf_counter
import psutil
from datetime import datetime, timezone
import json
import os

# ---------------------------------------------------------------------------
# 1) KHỞI ĐỘNG FIREBASE ADMIN
# ---------------------------------------------------------------------------
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# 2) XÁC THỰC FIREBASE ID TOKEN
# ---------------------------------------------------------------------------
def verify_firebase_token(request):
    """Xác thực Firebase ID Token từ header Authorization"""
    id_token = request.headers.get("Authorization")
    if not id_token:
        return None
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        return None

# ---------------------------------------------------------------------------
# 3) LƯU THÔNG TIN NGƯỜI DÙNG
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
# 4) GỬI THÔNG BÁO FCM
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

# ---------------------------------------------------------------------------
# 5) CHẠY TỐI ƯU HÓA VÀ LƯU KẾT QUẢ THEO CẤU TRÚC MỚI
# ---------------------------------------------------------------------------
def save_to_firestore(job_id, vehicles_data):
    """
    Lưu kết quả tối ưu hóa vào Firestore:
    - Collection "Routes": Lưu lộ trình hoàn chỉnh của từng tài xế.
    - Collection "Drivers": Cập nhật trường route_by_day của tài xế.
    - Collection "Requests": Cập nhật trạng thái đơn hàng.
    """
    for driver_id, driver_data in vehicles_data.items():
        route_doc_id = f"{driver_id}_{job_id}"

        # Lưu tuyến đường vào collection "Routes"
        db.collection("Routes").document(route_doc_id).set({
            "driver_id": driver_id,
            "vehicle_id": driver_data.get("vehicle_id", ""),
            "route": driver_data.get("route", []),
            "total_distance": driver_data.get("total_distance", 0),
            "date": datetime.now(timezone.utc).isoformat()  # ✅ Sửa lỗi utcnow()
        })

        # Cập nhật thông tin lộ trình của tài xế trong collection "Drivers"
        driver_ref = db.collection("Drivers").document(driver_id)
        driver_ref.set({
            "route_by_day": {job_id: driver_data.get("route", [])}
        }, merge=True)

        # Cập nhật trạng thái đơn hàng trong collection "Requests"
        for req in driver_data.get("route", []):
            request_id = req.get("request_id")
            if request_id:
                request_ref = db.collection("Requests").document(request_id)
                request_ref.update({
                    "delivery_status": 1,  # Đã được lên lịch trình
                    "delivery_time": datetime.now(timezone.utc).isoformat()  # ✅ Sửa lỗi utcnow()
                })

def run_optimization(job_id):
    """Chạy thuật toán tối ưu hóa và lưu kết quả vào Firestore."""
    tstart = perf_counter()
    if not os.path.exists('data'):
        os.makedirs('data')

    output_file = f"data/output_{job_id}.json"
    with open(output_file, 'w') as out_f:
        process = subprocess.Popen(
            ['python', 'test_bo_doi_cong_nghiep.py'],
            stdout=out_f
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
    with open(output_file, 'r', encoding='utf-8') as f:
        full_results = json.load(f)

    vehicles_data = {}
    for day_result in full_results:
        vehicles = day_result.get("vehicles", {})
        for drv_id, drv_info in vehicles.items():
            if drv_id in vehicles_data:
                vehicles_data[drv_id]["route"].extend(drv_info.get("route", []))
                vehicles_data[drv_id]["total_distance"] += drv_info.get("total_distance", 0)
            else:
                vehicles_data[drv_id] = drv_info
    save_to_firestore(job_id, vehicles_data)
    return run_time, memory_usage

@app.route('/optimize', methods=['POST'])
def optimize():
    """Chạy tối ưu hóa và gửi thông báo khi hoàn thành."""
    data = request.json or {}
    job_id = data.get("job_id", str(datetime.now(timezone.utc).timestamp()))  # ✅ Sửa lỗi utcnow()
    run_time, memory_usage = run_optimization(job_id)

    msg = messaging.Message(
        notification=messaging.Notification(
            title="Optimization Completed",
            body=f"Job {job_id} finished in {run_time:.2f}s."
        ),
        topic="dispatch_updates"
    )
    messaging.send(msg)

    return jsonify({"job_id": job_id, "status": "completed"}), 200

# ---------------------------------------------------------------------------
# 6) CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
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
        "delivery_time": datetime.now(timezone.utc).isoformat()  # ✅ Sửa lỗi utcnow()
    })

    return jsonify({"message": "Delivery status updated"}), 200

# ---------------------------------------------------------------------------
# CHẠY APP
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
