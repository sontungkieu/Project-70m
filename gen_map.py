import numpy as np
import os
import json

# Define the size of the matrix
def gen_map(NUM_OF_NODES=10, seed=42):
    # Set the seed for reproducibility
    np.random.seed(seed)

    # Generate an n x n matrix with random values in the range [0.5, 100]
    matrix = np.random.uniform(0.5, 100, (NUM_OF_NODES, NUM_OF_NODES))
    matrix = (matrix + matrix.T) / 2

    # Set the diagonal elements to zero
    np.fill_diagonal(matrix, 0)

    # Convert the matrix to a list of lists
    matrix_list = matrix.tolist()

    # Save the matrix to a JSON file using the json library
    # Ensure the 'data' folder exists
    if not os.path.exists('data'):
        os.makedirs('data')
    
    with open('data/distance.json', 'w') as jsonfile:
        json.dump(matrix_list, jsonfile)

gen_map()