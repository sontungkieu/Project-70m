import json, os
from typing import List

from objects.request import Request

try:
    from ..config import MIN_CAPACITY
except ImportError:
    from config import MIN_CAPACITY

def split_requests(requests: List[Request], output_file: str = "data/intermediate/mapping.json"):
    """
    Chia nhỏ các request nếu vượt quá MIN_CAPACITY và tạo mapping cho các node.
    Bao gồm validate dữ liệu và in tiến trình xử lý.
    
    Args:
        requests (List[Request]): Danh sách các request cần xử lý.
        output_file (str): Đường dẫn đến file JSON đầu ra để lưu kết quả.
    
    Returns:
        tuple: (mapped_requests, mapping, inverse_mapping)
    
    Raises:
        ValueError: Nếu dữ liệu đầu vào không hợp lệ.
        IOError: Nếu có lỗi khi ghi file.
    """
    # Validate đầu vào
    if not isinstance(requests, list):
        raise ValueError(f"Requests must be a list, got {type(requests)}")
    if not requests:
        print("Warning: Empty request list provided")
    
    print(f"Starting to split {len(requests)} requests...")
    
    # Khởi tạo mapping và inverse_mapping
    new_node = 1
    mapping = {0: [0]}
    inverse_mapping = {0: 0}
    new_requests = []
    
    # Chia nhỏ các request nếu cần
    for i, request in enumerate(requests):
        if not isinstance(request, Request):
            raise ValueError(f"Item at index {i} is not a Request object: {type(request)}")
        if not isinstance(request.weight, (int, float)) or request.weight < 0:
            raise ValueError(f"Invalid weight for request at index {i}: {request.weight}")
        if not isinstance(request.end_place, list):
            raise ValueError(f"end_place must be a list for request at index {i}")
        
        print(f"Processing request {i + 1} with weight {request.weight}")
        split_count = 0
        
        while request.weight > MIN_CAPACITY:
            print(f"  Splitting request with weight {request.weight}")
            new_request = Request(
                name=request.name,
                start_place=request.start_place,
                end_place=request.end_place.copy(),  # Sao chép để tránh thay đổi gốc
                weight=MIN_CAPACITY,
                date=request.date,
                note=request.note,
                timeframe=request.timeframe,
                staff_id=request.staff_id,
                split_id=1,
            )
            new_request.gen_id()
            print(new_request)
            new_requests.append(new_request)
            request.weight -= MIN_CAPACITY
            request.weight = 0
            split_count += 1
        new_requests.append(request)
        if split_count > 0:
            print(f"  Split into {split_count + 1} requests")
    
    print(f"Total requests after splitting: {len(new_requests)}")
    
    # Tạo mapped_requests và cập nhật mapping
    mapped_requests = []
    for i, request in enumerate(new_requests):
        end_place_id = request.end_place[0]
        if not isinstance(end_place_id, (int, str)):
            raise ValueError(f"Invalid end_place[0] type at request {i}: {type(end_place_id)}")
        
        if end_place_id not in mapping:
            mapping[end_place_id] = [new_node]
            print(f"New mapping created: {end_place_id} -> {new_node}")
        else:
            mapping[end_place_id].append(new_node)
            print(f"Added to mapping: {end_place_id} -> {new_node}")
        
        inverse_mapping[new_node] = end_place_id
        request.end_place[0] = new_node
        mapped_requests.append(request)
        new_node += 1
    
    print(f"Mapping size: {len(mapping)}")
    print(f"Inverse mapping size: {len(inverse_mapping)}")
    
    # Tạo dữ liệu JSON
    json_data = {
        "mapped_requests": [vars(req) for req in mapped_requests],  # Chuyển Request thành dict
        "mapping": mapping,
        "inverse_mapping": inverse_mapping,
    }
    
    # Ghi ra file nếu output_file được cung cấp
    if output_file is not None:
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")
        
        print(f"Writing results to: {output_file}")
        try:
            with open(output_file, 'w') as f:
                json.dump(json_data, f, indent=4)
            print("File written successfully")
        except Exception as e:
            raise IOError(f"Error writing to output file: {e}")
    
    print("Request splitting and mapping completed successfully")
    return mapped_requests, mapping, inverse_mapping
import json
import os

def read_mapping(file_path: str = "data/intermediate/mapping.json"):
    """
    Đọc file mapping JSON và trả về mapped_requests, mapping và inverse_mapping.
    Bao gồm validate dữ liệu và in tiến trình xử lý.
    
    Args:
        file_path (str): Đường dẫn đến file mapping JSON.
    
    Returns:
        tuple: (mapped_requests, mapping, inverse_mapping) từ dữ liệu JSON.
    
    Raises:
        FileNotFoundError: Nếu file không tồn tại.
        ValueError: Nếu dữ liệu JSON không hợp lệ hoặc thiếu key cần thiết.
    """
    # Validate file existence
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Mapping file not found: {file_path}")
    
    print(f"Starting to read mapping file: {file_path}")
    
    # Đọc file JSON
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print("Successfully loaded JSON data")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in mapping file: {e}")
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")
    
    # Validate cấu trúc dữ liệu
    if not isinstance(data, dict):
        raise ValueError(f"Mapping data must be a dictionary, got {type(data)}")
    
    required_keys = ["mapped_requests", "mapping", "inverse_mapping"]
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise ValueError(f"Missing required keys in mapping data: {missing_keys}")
    
    # Validate kiểu dữ liệu của từng thành phần
    mapped_requests = data["mapped_requests"]
    mapping = data["mapping"]
    inverse_mapping = data["inverse_mapping"]
    
    if not isinstance(mapped_requests, list):
        raise ValueError(f"'mapped_requests' must be a list, got {type(mapped_requests)}")
    if not isinstance(mapping, dict):
        raise ValueError(f"'mapping' must be a dictionary, got {type(mapping)}")
    if not isinstance(inverse_mapping, dict):
        raise ValueError(f"'inverse_mapping' must be a dictionary, got {type(inverse_mapping)}")
    
    # In thông tin cơ bản về dữ liệu
    print(f"Found {len(mapped_requests)} mapped requests")
    print(f"Mapping contains {len(mapping)} entries")
    print(f"Inverse mapping contains {len(inverse_mapping)} entries")
    
    # Kiểm tra tính nhất quán giữa mapping và inverse_mapping (tùy chọn)
    if len(mapping) != len(inverse_mapping):
        print(f"Warning: Mapping size ({len(mapping)}) does not match inverse mapping size ({len(inverse_mapping)})")
    
    print("Mapping file processing completed successfully")
    return mapped_requests, mapping, inverse_mapping

def postprocess_output(output_file: str = "data/test/output_2025-03-20_15-19-42.json", 
                      mapping_file: str = "data/intermediate/mapping.json",
                      processed_output_file: str = "data/test/processed_output_2025-03-20_15-19-42.json"):
    """
    Hàm xử lý hậu kỳ: Đọc file output và inverse mapping, ánh xạ các node trong output về chỉ số gốc,
    sau đó dump kết quả ra file JSON. Bao gồm validate dữ liệu và in tiến trình xử lý.
    
    Args:
        output_file (str): Đường dẫn đến file output JSON.
        mapping_file (str): Đường dẫn đến file mapping JSON.
        processed_output_file (str): Đường dẫn đến file JSON đầu ra sau khi xử lý.
    
    Returns:
        dict: Output đã được ánh xạ lại với các node gốc.
    """
    # Validate file existence
    if not os.path.exists(output_file):
        raise FileNotFoundError(f"Output file not found: {output_file}")
    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"Mapping file not found: {mapping_file}")

    print(f"Starting postprocessing...")
    print(f"Reading output file: {output_file}")
    
    # Đọc file output
    try:
        with open(output_file, 'r') as f:
            output_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in output file: {e}")
    
    print(f"Reading mapping file: {mapping_file}")
    # Đọc inverse mapping từ file mapping
    try:
        _, _, inverse_mapping = read_mapping(mapping_file)
    except Exception as e:
        raise ValueError(f"Error reading mapping file: {e}")
    
    # Validate output_data structure
    if not isinstance(output_data, list):
        raise ValueError("Output data must be a list of day data")
    
    print(f"Found {len(output_data)} days in output data")
    
    # Hàm phụ để ánh xạ lại danh sách tuyến đường
    def remap_route(route_list):
        if not isinstance(route_list, list):
            raise ValueError(f"Route list must be a list, got {type(route_list)}")
        
        for stop in route_list:
            if not isinstance(stop, dict) or "node" not in stop:
                raise ValueError(f"Invalid stop format: {stop}")
            node = stop["node"]
            if node in inverse_mapping:
                stop["node"] = inverse_mapping[node]
            else:
                print(f"Warning: Node {node} not found in inverse mapping")
        return route_list
    
    # Xử lý từng ngày và từng xe trong output
    for i, day_data in enumerate(output_data):
        if not isinstance(day_data, dict):
            raise ValueError(f"Day data at index {i} must be a dictionary")
        
        if "vehicles" in day_data:
            print(f"Processing day {i + 1}: {len(day_data['vehicles'])} vehicles found")
            for vehicle_id, vehicle_data in day_data["vehicles"].items():
                if not isinstance(vehicle_data, dict) or "list_of_route" not in vehicle_data:
                    raise ValueError(f"Invalid vehicle data for vehicle {vehicle_id}")
                
                print(f"Remapping route for vehicle {vehicle_id}")
                vehicle_data["list_of_route"] = remap_route(vehicle_data["list_of_route"])
    
    # Tạo thư mục đầu ra nếu chưa tồn tại
    output_dir = os.path.dirname(processed_output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
    
    # Ghi kết quả ra file JSON
    print(f"Writing processed data to: {processed_output_file}")
    try:
        with open(processed_output_file, 'w') as f:
            json.dump(output_data, f, indent=4)
    except Exception as e:
        raise IOError(f"Error writing to processed output file: {e}")
    
    print("Postprocessing completed successfully")
    return output_data

def split_driver():
    """
    chia driver rảnh nhiều khoảng ra làm nhiều driver
    """
    pass

# Ví dụ sử dụng
if __name__ == "__main__":
    processed_output = postprocess_output()
    print(f"Processed output has been saved to 'data/test/processed_output.json'")
