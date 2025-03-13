import hashlib
from pathlib import Path


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
