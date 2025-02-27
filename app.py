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
    except Exception:
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
# 5) LƯU KẾT QUẢ VÀO FIRESTORE (GIỮ NGUYÊN CẤU TRÚC OUTPUT)
# ---------------------------------------------------------------------------
def save_to_firestore(job_id, vehicles_data):
    """
    Lưu kết quả tối ưu hóa vào Firestore, 
    GIỮ nguyên trường "distance_of_route" và "list_of_route".
    """
    for vehicle_id, driver_data in vehicles_data.items():
        route_doc_id = f"{vehicle_id}_{job_id}"

        # 🔸 Lưu vào collection "Routes"
        db.collection("Routes").document(route_doc_id).set({
            "vehicle_id": vehicle_id,
            "distance_of_route": driver_data.get("distance_of_route", 0),   # GIỮ NGUYÊN TÊN
            "list_of_route": driver_data.get("list_of_route", []),         # GIỮ NGUYÊN TÊN
            "finished_at": datetime.now(timezone.utc).isoformat()          # Thêm thời gian
        })

        # 🔸 Cập nhật "Drivers"
        driver_ref = db.collection("Drivers").document(vehicle_id)
        driver_ref.set({
            "route_by_day": {job_id: driver_data.get("list_of_route", [])}
        }, merge=True)
        driver_ref.update({
            "available": True,
            "last_update": datetime.now(timezone.utc).isoformat()
        })

# ---------------------------------------------------------------------------
# 6) CHẠY THUẬT TOÁN, THÊM "THỜI GIAN THỰC" VÀ CẬP NHẬT FILE OUTPUT
# ---------------------------------------------------------------------------
def run_optimization(job_id):
    """Chạy thuật toán, giữ nguyên output, thêm thời gian thực, rồi lưu Firestore."""
    tstart = perf_counter()
    if not os.path.exists('data'):
        os.makedirs('data')

    output_file = f"data/output_{job_id}.json"
    
    # 🔸 Chạy file test_bo_doi_cong_nghiep.py, lưu stdout vào output_file
    with open(output_file, 'w', encoding='utf-8') as out_f:
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

    # 🔸 Đọc output gốc (GIỮ NGUYÊN) 
    with open(output_file, 'r', encoding='utf-8') as f:
        full_results = json.load(f)

    # 🔸 Thêm "execution_time" & "finished_at" vào từng day_result
    finished_at = datetime.now(timezone.utc).isoformat()
    for day_result in full_results:
        day_result["execution_time"] = f"{run_time:.2f} s"
        day_result["finished_at"] = finished_at

    # 🔸 Ghi lại file output (đã thêm thời gian) - vẫn giữ nguyên cấu trúc vehicles
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, ensure_ascii=False, indent=2)

    # 🔸 Tạo dict vehicles_data để lưu Firestore
    vehicles_data = {}
    for day_result in full_results:
        vehicles = day_result.get("vehicles", {})
        for drv_id, drv_info in vehicles.items():
            if drv_id not in vehicles_data:
                # GIỮ NGUYÊN: "distance_of_route" & "list_of_route"
                vehicles_data[drv_id] = {
                    "distance_of_route": drv_info.get("distance_of_route", 0),
                    "list_of_route": drv_info.get("list_of_route", [])
                }
            else:
                # Cộng dồn distance_of_route & nối list_of_route
                vehicles_data[drv_id]["distance_of_route"] += drv_info.get("distance_of_route", 0)
                vehicles_data[drv_id]["list_of_route"].extend(drv_info.get("list_of_route", []))

    # 🔸 Lưu vào Firestore
    save_to_firestore(job_id, vehicles_data)
    return run_time, memory_usage

# ---------------------------------------------------------------------------
# 7) API /optimize: GỌI THUẬT TOÁN, GỬI THÔNG BÁO
# ---------------------------------------------------------------------------
@app.route('/optimize', methods=['POST'])
def optimize():
    """Chạy tối ưu hóa, thêm thời gian thực, lưu Firestore, gửi thông báo."""
    data = request.json or {}
    job_id = data.get("job_id", str(datetime.now(timezone.utc).timestamp()))
    run_time, memory_usage = run_optimization(job_id)

    # 🔸 Gửi thông báo FCM
    msg = messaging.Message(
        notification=messaging.Notification(
            title="Optimization Completed",
            body=f"Job {job_id} finished in {run_time:.2f}s."
        ),
        topic="dispatch_updates"
    )
    messaging.send(msg)

    return jsonify({
        "job_id": job_id,
        "status": "completed",
        "execution_time": f"{run_time:.2f} s",
        "memory_usage": memory_usage
    }), 200

# ---------------------------------------------------------------------------
# 8) CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
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
# CHẠY APP
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
