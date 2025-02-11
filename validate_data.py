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
"""

(70cu) C:\Users\Tung\Project-70m>C:/Users/Tung/.conda/envs/70cu/python.exe c:/Users/Tung/Project-70m/validate_data.py
File: data/distance.csv, SHA-256: d5b5a089c65d6d21c8808ab25e3faee29396f7eaeb54831e8dea45fd56b45739
File: data/requests0.csv, SHA-256: 0061eccb8aace57e3072ec9706d2b2e901c3ea6e190bd8dd33d359f752c9af57
File: data/requests1.csv, SHA-256: 6c20e23c8ee7787f2efe3c456da51ac602924262e476a1d2647a4d69e855c11e
File: data/requests10.csv, SHA-256: 057bd99027e52a5673cc742caa80096a0ac43aede293381906584c723afca2a0
File: data/requests11.csv, SHA-256: 9fb4250b9e85c2ad45f7ead375fd37e6309a2f5a9083e15c285b394e3b195604
File: data/requests12.csv, SHA-256: 4a2de8a9dbc08d8d3da9d88750e1dc4e5443887ed2fd5b902de6c67e3ee350ed
File: data/requests13.csv, SHA-256: 4b9702a970b35490bb58a1bf3868eb01ecb9ca700562c00af64078750c80508a
File: data/requests14.csv, SHA-256: 3c3987fc9d0c6f4cafa04495379a2a4466fee8d867159228bdfe7d2455309c66
File: data/requests15.csv, SHA-256: 203ef26870d54938ba12d2c0df8464d8402430a1968a5d808c9eabf096eeedef
File: data/requests16.csv, SHA-256: 4613521664efd8a83be9787107fd7047ba3a298136b974e1d22234920b8b36bd
File: data/requests17.csv, SHA-256: 31da8933d6f653ffe001375712b012d1ee186c8e2b21190605eb0edac5f6ae1a
File: data/requests18.csv, SHA-256: ebc780b96d7a02f4182c47b583a8efd744418b7bb7dcc55b3caa9dc166f97d94
File: data/requests19.csv, SHA-256: 7487e87220f4cb354c40f1180e312f2fba2f7d4f08027310be3a1759ca14e557
File: data/requests2.csv, SHA-256: 55a738b2d25cf87a483454fec2a2fed60c22d11f14d61990a8a62bfd9190c50c
File: data/requests20.csv, SHA-256: b4e1f755481568ca8a919be9734850d79d62e2c388c704cf80027bfc07cc008d
File: data/requests21.csv, SHA-256: 6fb9e54d5e13c456dc26cd662408a252de70c3800c4859c51dcdb01fd96fa23b
File: data/requests22.csv, SHA-256: 0346fca01cd5aa97ef4389a210185fa39ef2b9f8cd009088d86aca47e6391f1c
File: data/requests23.csv, SHA-256: 31138abcbdf6323a2da90b3471f3622feb3f171d889f2dff11facbee0498b019
File: data/requests24.csv, SHA-256: 65b3012c80d58cd72cafb92e4f6bad77372f3e6771f0533a517ae1816b8d8e8e
File: data/requests25.csv, SHA-256: 551665e89766e29d33c31b33fc3d8248f9095c2b3eb491323df3f9448d0d9ae5
File: data/requests26.csv, SHA-256: 8607638a00631651ad7581c839de53b53864f9aeba720a757e58b4a20d355012
File: data/requests27.csv, SHA-256: a778479e85c29cf0e5ccac5e287c093ae6120e3371bb937d99eaadffe0b36ad1
File: data/requests28.csv, SHA-256: d033fb1c7ae41ac60f93e819869c70c8e3423beb6bbcdd000170e193c7d500d7
File: data/requests29.csv, SHA-256: 362a271dd222ea24bec96605251672298b27e014e6bbb36ae66854ebb91fd4fe
File: data/requests3.csv, SHA-256: d1a64925c9d317cc4881a58794aa1dccc01702860923f92db59c30755f529370
File: data/requests4.csv, SHA-256: 7d133e1b61e5f13a9ca5266d81d0ddb07e1e82dbcd3cc265e6630a5931ac02fa
File: data/requests5.csv, SHA-256: 7c4777aa3c72f12b292bb42b1f4e736817763d9c20681e024e752ba919e6ccb7
File: data/requests6.csv, SHA-256: 309bc20f724b8a1a75757a3609fd272d9abbfcff81376cef4a257660e0050447
File: data/requests7.csv, SHA-256: d35105ca5acf8e5af491811c867e91b151ea39b13b83408e0f4b7e91db7d787c
File: data/requests8.csv, SHA-256: dc36e1fa97bb32cf30e5769fb95984ca1f7e5562bdfb7113b62861a1ca3ae0b1
File: data/requests9.csv, SHA-256: fe990fe5779a2e93a6ee66f93ae806ffe7e1cf61bb0f29805ca0b8d81ac0886c
File: data/vehicle.csv, SHA-256: b531e6b8c558c59e62d4ef90035d8c65b643280150244ba700686e51a234a677

Final SHA-256 hash of concatenated hashes: a0ca20684ed38e152aa498af62d0beab3ec8f45f87c4b6b3fe4c22abda153ea2

"""

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