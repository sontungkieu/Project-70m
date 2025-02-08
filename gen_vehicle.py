import numpy as np

# Set the seed for reproducibility
np.random.seed(42)
metric = [9.7, 24.2, 26.7, 32, 38.2, 54]
# Define the size of the list
n = 10  # You can change this value to any desired size

# Generate a list of n random numbers in the range [0, 5]
xe_s = [metric[u] for u in [0]*15+[1]*10+[2]*10+[3]*10+[4]*5+[5]*5]

# Print the generated list
print(xe_s)

# Save the list to a CSV file
np.savetxt('vehicle.csv', xe_s, delimiter=',', fmt='%.1f')