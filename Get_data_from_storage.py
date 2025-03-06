import firebase_admin
from firebase_admin import credentials, storage

# Khởi tạo Firebase Admin SDK với Storage
cred = credentials.Certificate("firebase-key.json")  # Đảm bảo file JSON đúng
firebase_admin.initialize_app(
    cred, {"storageBucket": "logistic-project-30dcd.firebasestorage.app"}
)


def download_file_from_storage(storage_path: str, local_path: str):
    """
    Tải file từ Firebase Storage về máy cục bộ.

    Args:
      storage_path: Đường dẫn file trên Firebase Storage (tên file hoặc có thư mục)
      local_path: Đường dẫn lưu file cục bộ
    """
    bucket = storage.bucket()
    blob = bucket.blob(storage_path)

    if not blob.exists():
        print(f"❌ Lỗi: File '{storage_path}' không tồn tại trong Storage.")
        return

    blob.download_to_filename(local_path)
    print(f"✅ Đã tải file '{storage_path}' từ Storage về '{local_path}'.")


if __name__ == "__main__":
    # 1️⃣ Đường dẫn file trên Storage (Kiểm tra chính xác tên file)
    storage_path = "Lenh_Dieu_Xe.xlsx"  # Đảm bảo đúng với Firebase Storage UI

    # 2️⃣ Đường dẫn lưu file cục bộ
    local_path = r"data\input\Lenh_Dieu_Xe.xlsx"  # Thay đổi nếu cần

    # 3️⃣ Tải file về
    download_file_from_storage(storage_path, local_path)
