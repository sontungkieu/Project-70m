import hashlib
import os
from pathlib import Path

def calculate_sha256(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_sha256_for_all_files_in_data():
    """Calculate the SHA-256 hash for all files in the 'data' folder and then hash the concatenated string of all hashes."""
    data_folder = Path("data")  # Sử dụng pathlib để tương thích hệ điều hành
    if not data_folder.exists():
        print(f"The folder '{data_folder}' does not exist.")
        return

    concatenated_hashes = ""
    for file_path in sorted(data_folder.rglob('*')):  # Duyệt qua tất cả file trong thư mục
        if file_path.is_file():  # Chỉ xử lý file, bỏ qua thư mục
            sha256_hash = calculate_sha256(file_path)
            concatenated_hashes += f"File: {file_path.as_posix()}, SHA-256: {sha256_hash}\n"
    
    print(concatenated_hashes)
    final_hash = hashlib.sha256(concatenated_hashes.encode()).hexdigest()
    print(f"Final SHA-256 hash of concatenated hashes: {final_hash}")

if __name__ == "__main__":
    calculate_sha256_for_all_files_in_data()


# 
# import hashlib
# import os

# def calculate_sha256(file_path):
#     """Calculate the SHA-256 hash of a file."""
#     sha256_hash = hashlib.sha256()
#     with open(file_path, 'rb') as f:
#         for byte_block in iter(lambda: f.read(4096), b''):
#             sha256_hash.update(byte_block)
#     return sha256_hash.hexdigest()

# def calculate_sha256_for_all_files_in_data():
#     """Calculate the SHA-256 hash for all files in the 'data' folder and then hash the concatenated string of all hashes."""
#     data_folder = 'data'
#     if not os.path.exists(data_folder):
#         print(f"The folder '{data_folder}' does not exist.")
#         return

#     concatenated_hashes = ""
#     for root, dirs, files in os.walk(data_folder):
#         for file in sorted(files):
#             file_path = os.path.join(root, file)
#             sha256_hash = calculate_sha256(file_path)
#             concatenated_hashes += f"File: {file_path}, SHA-256: {sha256_hash}\n"
#     print(concatenated_hashes)
#     final_hash = hashlib.sha256(concatenated_hashes.encode()).hexdigest()
#     print(f"Final SHA-256 hash of concatenated hashes: {final_hash}")

# if __name__ == "__main__":
#     calculate_sha256_for_all_files_in_data()    

# """
# Final SHA-256 hash of concatenated hashes: 7908649147398a608a8507625b16c6d413213d6eeeb044396fbaa15632bb5da4
# nếu chạy file ra dòng trên thì lỗi ở ortools
# """