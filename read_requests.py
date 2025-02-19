import subprocess
from time import perf_counter
import psutil
from datetime import datetime
import ast
import os
import json

config = []
def run_test_bo_doi_cong_nghiep():
    current_time = "2025-02-19_10-49-26"
    if not os.path.exists('data'):
        os.makedirs('data')
    stdout_filename = f"data/stdout_output_{current_time}.txt"
    config_filename = f"data/config_{current_time}.txt"

    return stdout_filename, config_filename

def read_config(config_filename):
    global config
    try:
        # Đọc file config
        with open(config_filename, 'r', encoding='utf-8') as file:
            config_str = file.read()

        # Chuyển đổi nội dung file sang dictionary
        config = ast.literal_eval(config_str)

        print("Config đọc được:", config)
        return config

    except (SyntaxError, ValueError):
        print("Lỗi: Nội dung file config không hợp lệ!")
        return None
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {config_filename}!")
        return None

def read_output(output_filename):
    import read_output
    return read_output.read_and_save_json_output(filename=output_filename)


def read_requests(config):
    NUM_OF_DAY_REPETION = config['NUM_OF_DAY_REPETION']
    requests_files = []
    for i in range(NUM_OF_DAY_REPETION):
        request_filename = f"data/requests{i}.json"
        try:
            with open(request_filename, 'r', encoding='utf-8') as file:
                # Load JSON data from file
                data = json.load(file)
                requests_files.append(data)
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file {request_filename}!")
        except Exception as e:
            print(f"Lỗi khi đọc file {request_filename}: {e}")
    return requests_files



def check(outputs, queries, config):
    print("Kiểm tra kết quả...")
    day_id = 0
    for output, query in zip(outputs[1:],queries): #zip by day
        print(f"Day {day_id}")
        day_id += 1
        # init time frame and demand
        time_frame = [(0,24*config['TIME_SCALE']) for _ in range(config['NUM_OF_NODES'])]
        demand = [0 for _ in range(config['NUM_OF_NODES'])]
        delivered_weight = [0 for _ in range(config['NUM_OF_NODES'])]
        for q in query[:config['NUM_OF_REQUEST_PER_DAY']]:
            time_frame[q[1][0]] = (q[-1][0]*config['TIME_SCALE'], q[-1][1]*config['TIME_SCALE'])
            demand[q[1][0]] = int(q[2]*config['CAPACITY_SCALE'])

        output['vehicles'] = {vehicle_id: vehicle for vehicle_id, vehicle in output['vehicles'].items() if vehicle['distance_of_route'] >0}

        for vehicle_id, vehicle in output['vehicles'].items():
            # print(f"vehicle_id: {vehicle_id}")
            precomputed_distance = vehicle['distance_of_route']
            list_of_route = vehicle['list_of_route']
            nodes = [route['node'] for route in list_of_route]
            arrival_time = [route['arrival_time'] for route in list_of_route]
            capacity = [route['capacity'] for route in list_of_route]
            delivered = [route['delivered'] for route in list_of_route]
            # print(f"vehicle_id: {vehicle_id}")
            # print(f"vehicle: {vehicle}")
            # print(f"nodes: {nodes}")
            # for i,_ in enumerate(nodes[:-1]):
                # print(f"from: {nodes[i]} to: {nodes[i+1]} distance: {D(nodes[i],nodes[i+1])/DISTANCE_SCALE}km delivered: {delivered[i]} capacity: {capacity[i]} demand: {demand[nodes[i]]}")
            
            for i,_ in enumerate(nodes[:-1]):
                if delivered[i] > 0:
                    if arrival_time[i] < time_frame[nodes[i]][0] or arrival_time[i] > time_frame[nodes[i]][1]:
                        print(f"Error: arrival time at node {nodes[i]} is not in time frame")
                        raise Exception(f"Error: arrival time at node {nodes[i]} is not in time frame {arrival_time[i]} not in {time_frame[nodes[i]]}")
                    if delivered_weight[nodes[i]] + delivered[i] > demand[nodes[i]]:
                        print(f"Error: delivered weight at node {nodes[i]} is greater than demand {delivered_weight[nodes[i]]} + {delivered[i]} > {demand[nodes[i]]}")
                        raise Exception(f"Error: delivered weight at node {nodes[i]} is greater than demand {delivered_weight[nodes[i]]} + {delivered[i]} > {demand[nodes[i]]}")
                    delivered_weight[nodes[i]] += delivered[i]
            # print(f"precomputed_distance: {precomputed_distance}")

        print(f"demand:           {demand}")
        print(f"delivered_weight: {delivered_weight}")
        # print(f"query len: {len(query)}")
        # print(f"num of request: {config['NUM_OF_REQUEST_PER_DAY']}")
        for i in range(config['NUM_OF_NODES']):
            if delivered_weight[i] != demand[i]:
                print(f"Error: delivered weight at node {i} is not equal to demand: real:{delivered_weight[i]} != {demand[i]}")
                raise Exception(f"Error: delivered weight at node {i} is not equal to demand: real:{delivered_weight[i]} != {demand[i]}")
        print(f"Day {day_id} is correct")
    print("Kết quả đúng!")
            
        
        
        


        # exit()

if __name__ == "__main__":
    stdout_filename, config_filename = run_test_bo_doi_cong_nghiep()

    #sau khi chạy
    config_data = read_config(config_filename)
    output_data = read_output(stdout_filename)
    requests_data = read_requests(config_data)

    # Kiểm tra 
    check(output_data, requests_data, config_data)