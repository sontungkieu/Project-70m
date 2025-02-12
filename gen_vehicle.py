import numpy as np
import os
import json

def gen_list_vehicle(NUM_OF_VEHICLES, seed=42):
    # Given value
    metric = [9.7, 24.2, 26.7, 32, 38.2, 54]
    # Set the seed for reproducibility
    np.random.seed(seed)
    # Generate a list of n random numbers in the range [0, 5]
    if NUM_OF_VEHICLES <= 3:
        xe_s = [metric[u] for u in [0]*2+[1]*1+[2]*0+[3]*0+[4]*0+[5]*0][:NUM_OF_VEHICLES]
    elif NUM_OF_VEHICLES <= 10:
        xe_s = [metric[u] for u in [0]*3+[1]*2+[2]*2+[3]*1+[4]*1+[5]*1][:NUM_OF_VEHICLES]
    else:
        xe_s = [metric[u] for u in [0]*0+[1]*4+[2]*14+[3]*0+[4]*3+[5]*20][:NUM_OF_VEHICLES]

    # Ensure the 'data' folder exists
    if not os.path.exists('data'):
        os.makedirs('data')

    # Save the list to a JSON file using the json library
    with open('data/vehicle.json', 'w') as jsonfile:
        json.dump(xe_s, jsonfile, separators=(',', ':'))

gen_list_vehicle(5)

