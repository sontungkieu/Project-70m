from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, messaging
import subprocess
from time import perf_counter
import psutil
from datetime import datetime
import ast
import os

# Khởi động Firebase
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# Lưu kết quả vào Firestore
def save_to_firestore(job_id, config, run_time, memory_usage, output_file, status="completed"):
    result_data = {
        "job_id": job_id,
        "config": config,
        "run_time": run_time,
        "memory_usage": memory_usage,
        "output_file": output_file,
        "status": status,
        "timestamp": datetime.utcnow()
    }
    db.collection("JobResults").document(job_id).set(result_data)

# Chạy OR-Tools
def run_optimization(job_id):
    tin = perf_counter()
    
    if not os.path.exists('data'):
        os.makedirs('data')
    output_file = f"data/output_{job_id}.txt"
    config_file = f"data/config_{job_id}.txt"

    with open(output_file, 'wb') as stdout_file, open(config_file, 'wb') as config_file:
        process = subprocess.Popen(['python', 'test_bo_doi_cong_nghiep.py'], 
                                   stdout=stdout_file, stderr=config_file)
    
        memory_usage = 0
        while process.poll() is None:
            try:
                memory_info = psutil.Process(process.pid).memory_info()
                memory_usage = max(memory_usage, memory_info.rss)
            except psutil.NoSuchProcess:
                break  

        process.wait()

    run_time = perf_counter() - tin
    return run_time, memory_usage, output_file, config_file

# API: Nhận yêu cầu tối ưu
@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.json
    job_id = data.get("job_id", str(datetime.utcnow().timestamp()))
    
    run_time, memory_usage, output_file, config_file = run_optimization(job_id)
    
    with open(config_file, 'r', encoding='utf-8') as file:
        config_str = file.read()
    try:
        config = ast.literal_eval(config_str)
    except:
        config = {}

    save_to_firestore(job_id, config, run_time, memory_usage, output_file)

    message = messaging.Message(
        notification=messaging.Notification(
            title="Tối ưu lộ trình hoàn tất",
            body=f"Công việc {job_id} đã chạy xong trong {run_time:.2f}s."
        ),
        topic="dispatch_updates"
    )
    messaging.send(message)

    return jsonify({"job_id": job_id, "status": "completed"}), 200

# API: Lấy kết quả từ Firestore
@app.route('/results/<job_id>', methods=['GET'])
def get_result(job_id):
    doc = db.collection("JobResults").document(job_id).get()
    if doc.exists:
        return jsonify(doc.to_dict())
    return jsonify({"error": "Job not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
