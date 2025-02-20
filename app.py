from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, messaging
import subprocess
from time import perf_counter
import psutil
from datetime import datetime
import json
import os

# -----------------------------------------------------------------------------
# 1) KHỞI ĐỘNG FIREBASE ADMIN
# -----------------------------------------------------------------------------
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# -----------------------------------------------------------------------------
# 2) LƯU THÔNG TIN NGƯỜI DÙNG
# -----------------------------------------------------------------------------
@app.route('/save-user-info', methods=['POST'])
def save_user_info():
    """
    Lưu thông tin bổ sung của user vào Firestore.
    Client (Flutter) sẽ gửi UID và additional_info sau khi đăng nhập thành công.
    """
    data = request.json
    uid = data.get("uid")  # UID do Flutter lấy được từ Firebase Auth
    try:
        db.collection("Users").document(uid).set({
            "additional_info": data.get("additional_info", {})
        }, merge=True)
        return jsonify({"message": "User info saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# -----------------------------------------------------------------------------
# 3) GỬI THÔNG BÁO FCM
# -----------------------------------------------------------------------------
@app.route('/send_notification', methods=['POST'])
def send_notification():
    """
    Endpoint gửi thông báo FCM.
    Client gửi thông tin bao gồm driver_id, title và body.
    """
    data = request.json or {}
    driver_id = data.get('driver_id')
    title = data.get('title', "Notification")
    body = data.get('body', "Hello from system")

    if not driver_id:
        return jsonify({"error": "Missing driver_id"}), 400

    # Lấy fcm_token của user từ Firestore
    driver_doc = db.collection("Users").document(driver_id).get()
    if not driver_doc.exists:
        return jsonify({"error": "User not found"}), 404

    driver_data = driver_doc.to_dict()
    fcm_token = driver_data.get("fcm_token")
    if not fcm_token:
        return jsonify({"error": "FCM token not registered"}), 400

    msg = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=fcm_token
    )
    response = messaging.send(msg)
    return jsonify({"message": "Notification sent", "response": response}), 200

# -----------------------------------------------------------------------------
# 4) CHẠY TỐI ƯU HÓA VÀ LƯU KẾT QUẢ
# -----------------------------------------------------------------------------
def save_to_firestore(job_id, config, run_time, memory_usage, output_file, request_file_path, vehicles_data):
    """
    Lưu kết quả tối ưu hóa:
      - "JobResults": để lưu kết quả tổng hợp.
      - "DriverHistory": mỗi user có lịch sử riêng.
    """
    job_ref = db.collection("JobResults").document(job_id)
    job_ref.set({
        "job_id": job_id,
        "config": config,
        "run_time": run_time,
        "memory_usage": memory_usage,
        "output_file": output_file,
        "request_file": request_file_path,
        "vehicles": vehicles_data,
        "timestamp": datetime.utcnow().isoformat()
    })

    for driver_id, driver_data in vehicles_data.items():
        driver_ref = db.collection("DriverHistory").document(driver_id)
        driver_ref.set({job_id: driver_data}, merge=True)

def run_optimization(job_id):
    tstart = perf_counter()
    if not os.path.exists('data'):
        os.makedirs('data')

    output_file = f"data/output_{job_id}.json"
    config_file = f"data/config_{job_id}.txt"
    request_file_path = f"data/requests_{job_id}.json"

    with open(output_file, 'w') as out_f, open(config_file, 'w') as err_f:
        process = subprocess.Popen(
            ['python', 'test_bo_doi_cong_nghiep.py'],
            stdout=out_f, stderr=err_f
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
        for drv_id, drv_info in day_result.get("vehicles", {}).items():
            vehicles_data.setdefault(drv_id, []).append(drv_info)

    save_to_firestore(job_id, {}, run_time, memory_usage, output_file, request_file_path, vehicles_data)
    return run_time, memory_usage

@app.route('/optimize', methods=['POST'])
def optimize():
    """
    Endpoint chạy tối ưu hóa:
      - Client gửi thông tin cần thiết (có thể bao gồm job_id nếu muốn).
      - Sau khi hoàn thành, gửi thông báo FCM tới topic "dispatch_updates".
    """
    data = request.json or {}
    job_id = data.get("job_id", str(datetime.utcnow().timestamp()))
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

# -----------------------------------------------------------------------------
# CHẠY APP
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
