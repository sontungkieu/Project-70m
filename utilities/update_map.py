import csv

# try:
#     from map.main_get_distances import get_distances
#     print("Imported from map.main_get_distances")
# except:
from utilities.map.main_get_distances import update_map_helper
from config import *


def update_map(requests, mapping, inverse_mapping):
    print("update_map.py:update_map:requests: ", requests)
    print("update_map.py:update_map:mapping: ", mapping)
    print("update_map.py:update_map:inverse_mapping: ", inverse_mapping)

    global NUM_OF_NODES
    """
    Update distance matrix and time windows based on the new mapping.
    """
    # Get the list of unique nodes
    print("update_map.py:update_map:len(requests): ", len(requests))
    for r in requests:
        print("update_map.py:update_map:request: ", r)
    nodes = set()
    for request in requests:
        nodes.add(request.start_place[0])
        nodes.add(request.end_place[0])
    nodes = sorted(list(nodes))
    print(f"update_map:nodes: {nodes}")

    # Get the list of unique nodes in the original data
    orig_nodes = set()
    for node in nodes:
        orig_nodes.add(inverse_mapping[node])
    orig_nodes = sorted(list(orig_nodes))
    print(f"update_map:orig_nodes: {orig_nodes}")
    # print(f"update_map:orig_nodes: {orig_nodes}")
    # Get the distance matrix for the original nodes
    orig_distance_matrix = update_map_helper(orig_nodes, orig_nodes)
    orig_distance_matrix_dict = {}
    for i in range(len(orig_nodes)):
        orig_distance_matrix_dict[orig_nodes[i]] = {}
        for j in range(len(orig_nodes)):
            orig_distance_matrix_dict[orig_nodes[i]][orig_nodes[j]] = orig_distance_matrix[i][j]
    orig_distance_matrix = orig_distance_matrix_dict
    print(f"update_map:orig_distance_matrix: {orig_distance_matrix}")

    # Initialize the new distance matrix
    n_new = len(nodes)
    print(f"update_map:n_new: {n_new}")
    new_distance_matrix = [[0 for _ in range(n_new)] for _ in range(n_new)]
    NUM_OF_NODES = n_new
    print(f"update_map:NUM_OF_NODES: {NUM_OF_NODES}")
    # print(f"update_map:orig_distance_matrix: {orig_distance_matrix}")

    # print(f"orig_distance_matrix: len {len(orig_distance_matrix)},{orig_distance_matrix}")
    # Update the new distance matrix
    for i in range(n_new):
        for j in range(n_new):
            orig_i = inverse_mapping[nodes[i]]
            orig_j = inverse_mapping[nodes[j]]
            new_distance_matrix[i][j] = int(float(orig_distance_matrix[orig_i][orig_j])*DISTANCE_SCALE) if orig_i != orig_j else 0
    print(f"update_map:new_distance_matrix: {new_distance_matrix}")
    return new_distance_matrix
