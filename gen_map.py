import numpy as np

# Set the seed for reproducibility
np.random.seed(42)

# Define the size of the matrix
def gen_map(NUM_OF_NODES = 10):
    n  = NUM_OF_NODES  # You can change this value to any desired size
# Generate an n x n matrix with random values in the range [0.5, 100]
    matrix = np.random.uniform(0.5, 100, (n, n))

    # Print the generated matrix
    print(matrix)

    # Save the matrix to a CSV file
    np.savetxt('distance.csv', matrix, delimiter=',')
gen_map()