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

    # Determine the absolute path of the current file (in utilities)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up one directory to get the project root
    project_root = os.path.abspath(os.path.join(current_file_dir, '..'))
    # Construct the path to the 'data' directory
    data_dir = os.path.join(project_root, 'data')
    
    # Create the 'data' directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Write the generated matrix to 'data/distance.json'
    with open(os.path.join(data_dir, 'distance.json'), 'w') as jsonfile:
        json.dump(matrix_list, jsonfile)


# Gọi hàm
if __name__ == '__main__':
    gen_map()   
