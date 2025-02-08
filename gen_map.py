import numpy as np

# Set the seed for reproducibility
np.random.seed(42)

# Define the size of the matrix
n = 54  # You can change this value to any desired size

# Generate an n x n matrix with random values in the range [0.5, 100]
matrix = np.random.uniform(0.5, 100, (n, n))

# Print the generated matrix
print(matrix)

# Save the matrix to a CSV file
np.savetxt('distance.csv', matrix, delimiter=',')