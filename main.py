import numpy as np

# vì có nhiều đơn hàng
# nhiều xe
# mỗi đơn hàng có thể spread nhiều xe
# việc phân việc sẽ dễ hơn nếu ortool và đặt constraint
# giới hạn trong 1 chuyến xe, thì không ghép quá 3 đơn,
# đi kèm với ghép các constraint khác
# nếu giao hàng vô trong miền nam thì sao? sẽ phải dự tính thời gian giao hàng 

# Read the distance.csv file
distance_matrix = np.loadtxt('distance.csv', delimiter=',')

# Print the distance matrix
print(distance_matrix)