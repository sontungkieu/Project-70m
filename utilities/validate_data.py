import hashlib
from pathlib import Path
import json
from datetime import datetime

def save_dict_and_get_sha256(d):
    # Lấy thời gian hiện tại và tạo tên file theo định dạng 'dict_YYYY_MM_DD_HH_MM_SS.json'
    current_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    file_name = f"dict_{current_time}.json"
    
    # Lưu dictionary vào file JSON
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4, sort_keys=True)
    
    # Tính SHA256 từ file
    sha256_hash = hashlib.sha256()
    with open(file_name, 'rb') as f:
        # Đọc file và cập nhật hash
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    # Trả về mã hash và tên file
    return file_name, sha256_hash.hexdigest()


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_sha256_for_all_files_in_data():
    """Calculate the SHA-256 hash for all files in the 'data' folder and then hash the concatenated string of all hashes."""
    # Determine the directory of the current file and go up one level to get the project root
    current_file_dir = Path(__file__).resolve().parent
    project_root = current_file_dir.parent
    # Construct the path to the 'data' folder relative to the project root
    data_folder = project_root / "data"

    if not data_folder.exists():
        print(f"The folder '{data_folder}' does not exist.")
        return

    concatenated_hashes = ""
    # Use rglob to recursively search for all files within the data folder
    for file_path in sorted(data_folder.rglob("*")):
        if file_path.is_file():
            sha256_hash = calculate_sha256(file_path)
            concatenated_hashes += (
                f"File: {file_path.as_posix()}, SHA-256: {sha256_hash}\n"
            )

    print(concatenated_hashes)
    final_hash = hashlib.sha256(concatenated_hashes.encode()).hexdigest()
    print(f"Final SHA-256 hash of concatenated hashes: {final_hash}")


if __name__ == "__main__":
    calculate_sha256_for_all_files_in_data()
