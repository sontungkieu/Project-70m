import numpy as np
import os

# Define the size of the matrix
def gen_map(NUM_OF_NODES = 10,seed = 42):
    # Set the seed for reproducibility
    np.random.seed(seed)

# Generate an n x n matrix with random values in the range [0.5, 100]
    matrix = np.random.uniform(0.5, 100, (NUM_OF_NODES, NUM_OF_NODES))

    # Print the generated matrix
    print(matrix)

    # Save the matrix to a CSV file
    # Ensure the 'data' folder exists
    if not os.path.exists('data'):
        os.makedirs('data')
    np.savetxt('data/distance.csv', matrix, delimiter=',')

gen_map()