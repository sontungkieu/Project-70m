import numpy as np
import os
import json


def gen_map(NUM_OF_NODES=30, seed=42):
    np.random.seed(seed)

    # 1. Sinh ngẫu nhiên ma trận n x n trong khoảng [0.5, 100]
    matrix = np.random.uniform(0.5, 100, (NUM_OF_NODES, NUM_OF_NODES))
    # Làm cho ma trận đối xứng
    matrix = (matrix + matrix.T) / 2
    # Đặt đường chéo bằng 0 (khoảng cách từ một nút đến chính nó)
    np.fill_diagonal(matrix, 0)


    # Chuyển về list để ghi JSON
    matrix_list = matrix.tolist(    )

    # Tạo thư mục 'data' nếu chưa tồn tại
    if not os.path.exists('data'):
        os.makedirs('data')

    # Ghi kết quả ra file JSON
    with open('data/distance.json', 'w') as jsonfile:
        json.dump(matrix_list, jsonfile)

    # Kiểm chứng nhanh một vài phần tử xem có vi phạm tam giác không
    # (Với 30 nút, bạn có thể chọn vài bộ (i, j, k) bất kỳ để kiểm)
    # Ví dụ với bộ (2, 1, 26):
    # print("Kiểm tra bất đẳng thức tam giác cho (2, 1, 26):",
    #       matrix[2][1] + matrix[1][26] >= matrix[2][26])


# Gọi hàm
gen_map()
