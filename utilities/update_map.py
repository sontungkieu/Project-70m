import csv

# try:
#     from map.main_get_distances import get_distances
#     print("Imported from map.main_get_distances")
# except:
from utilities.map.main_get_distances import update_map_helper
try:
    from ..config import INFINITY
except:
    from config import INFINITY

def update_map(requests, mapping, inverse_mapping):
    """
    Update distance matrix and time windows based on the new mapping.
    """
    # Get the list of unique nodes
    nodes = set()
    for request in requests:
        nodes.add(request.start_place[0])
        nodes.add(request.end_place[0])
    nodes = sorted(list(nodes))
    
    # Get the list of unique nodes in the original data
    orig_nodes = set()
    for node in nodes:
        orig_nodes.add(inverse_mapping[node])
    orig_nodes = sorted(list(orig_nodes))
    print(f"update_map:orig_nodes: {orig_nodes}")
    # Get the distance matrix for the original nodes
    orig_distance_matrix = update_map_helper(orig_nodes, orig_nodes)
    
    # Initialize the new distance matrix
    n_new = len(nodes)
    new_distance_matrix = [[0 for _ in range(n_new)] for _ in range(n_new)]
    
    # Update the new distance matrix
    for i in range(n_new):
        for j in range(n_new):
            orig_i = inverse_mapping[nodes[i]]
            orig_j = inverse_mapping[nodes[j]]
            if i == orig_i and j == orig_j:
                new_distance_matrix[i][j] = orig_distance_matrix[orig_i][orig_j]
            elif i == orig_j or j == orig_i:
                new_distance_matrix[i][j] = 0
            else:
                new_distance_matrix[i][j] = INFINITY
    
    return new_distance_matrix