import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the Excel file
file_path = 'DS-công-ty-và-địa-chỉ-giao-hàng.xlsx'
df = pd.read_excel(file_path)

# Convert the last column to a list
last_column = df.iloc[:, -1].tolist()
print(last_column)

# Calculate the quartiles
quartiles = np.percentile(last_column, [25, 50, 75])
print("Quartiles:", quartiles)

# Plot the list as a histogram
plt.hist(last_column, bins=10, edgecolor='black')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title('phân phối của khối lượng đơn hàng')

# Save the histogram as an image file
plt.savefig('phân phối đơn hàng theo khối lượng.png')

# Show the plot
# plt.show()
"""
Quartiles: [26.375 33.5   41.   ]
"""