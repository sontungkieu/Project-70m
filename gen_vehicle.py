import numpy as np

# Set the seed for reproducibility
np.random.seed(42)
metric = [9.7, 24.2, 26.7, 32, 38.2, 54]
def gen_list_vehicle(NUM_OF_VEHICLES):
    # Generate a list of n random numbers in the range [0, 5]
    # xe_s =
    xe_s = [metric[u] for u in [0]*2+[1]*1+[2]*0+[3]*0+[4]*0+[5]*0] if NUM_OF_VEHICLES ==3 else [metric[u] for u in [0]*3+[1]*2+[2]*2+[3]*1+[4]*1+[5]*1] if NUM_OF_VEHICLES == 10 else  [metric[u] for u in [0]*15+[1]*10+[2]*10+[3]*10+[4]*5+[5]*5]

    # Print the generated list
    print(xe_s)

    # Save the list to a CSV file
    np.savetxt('vehicle.csv', xe_s, delimiter=',', fmt='%.1f')
gen_list_vehicle(3)