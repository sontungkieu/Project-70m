import random
import os
import json
from typing import List
from datetime import datetime, timedelta

class Request:
    def __init__(self, request_id:str, start_place:List[int], end_place:List[int], weight: int, date: str, timeframe: List[int],split_id:bool = False):
        self.request_id = request_id
        self.start_place = start_place
        self.end_place = end_place
        self.weight = weight
        self.date = date
        self.timeframe = timeframe
        self.split_id = split_id
        self.delivery_time = -1
        self.delivery_status = 0

    def __init__(self, start_place: List[int], end_place: List[int], weight: int, date: str, timeframe: List[int], split_id:bool = 1):
        self.start_place = start_place
        self.end_place = end_place
        self.weight = weight
        self.date = date
        self.timeframe = timeframe
        self.split_id = split_id
        self.delivery_time = -1
        self.delivery_status = 0
        self.request_id = self.gen_id()

    def gen_id(self):
        request_id = self.date + "-"
        request_id += str(self.timeframe[0]).zfill(2) + "-"
        request_id += str(self.timeframe[1]).zfill(2) + "-"
        request_id += str(self.start_place[0]).zfill(3) + "-"
        request_id += str(self.end_place[0]).zfill(3) + "-"
        request_id += str(int(self.weight * 10)).zfill(3) + "-"
        request_id += str(random.randint(0, 99)).zfill(2) + "-"
        request_id += str(self.split_id).zfill(2)
        return request_id
        
    @classmethod
    def generate(cls, NUM_OF_NODES=55, start_from_0=True, single_start=True, small_weight=True):
        """
        Tạo một yêu cầu giao hàng ngẫu nhiên với thông tin:
          - start_place: danh sách điểm lấy hàng,
          - end_place: điểm giao hàng (danh sách chứa một phần tử),
          - weight: trọng lượng,
          - gen_day: ngày giao hàng (0-3),
          - gen_timeframe: khung giờ giao hàng (hai số giờ trong ngày).
        """
        # Lấy điểm bắt đầu: nếu start_from_0 thì luôn là [0], ngược lại lấy mẫu ngẫu nhiên từ [0,1,2,3]
        if start_from_0:
            start_place = [0]
        else:
            k = 1 if single_start else random.randint(1, 4)
            start_place = random.sample([0, 1, 2, 3], k=k)
        
        # Lấy điểm kết thúc: một phần tử trong khoảng 1 đến NUM_OF_NODES-1
        end_place = random.sample(list(range(1, NUM_OF_NODES)), k=1)
        
        # Tính trọng lượng đơn hàng dựa trên tham số small_weight
        if small_weight == True:
            weight = random.randint(0, int(9.7*10)) / 10
        elif small_weight == False:
            weight = random.randint(54*10, 300*10) / 10
        else:
            weight = random.randint(24*10, 150*10) / 10
        
        # Ngày giao hàng (giá trị ngẫu nhiên từ 0 đến 3)
        now = datetime.now()
        tomorrow = now + timedelta(days=random.randint(0,10))
        formatted_date = tomorrow.strftime("%d%m%Y")
        # Khung giờ giao hàng: 2 giờ được chọn ngẫu nhiên trong ngày và sắp xếp tăng dần
        gen_timeframe = sorted(random.sample(list(range(0, 24)), k=2))
        
        # Tạo mã yêu cầu theo định dạng:
        # <ngày giao (ngày mai)>-<giờ1>-<giờ2>-<start_place[0]>-<end_place[0]>-<trọng lượng*10>-<id ngẫu nhiên 2 số>
        
        
        return cls(start_place, end_place, weight, formatted_date, gen_timeframe)
    
    def to_list(self):
        """Chuyển đổi đối tượng Request về dạng list, giống như hàm gen_request() trả về."""
        return [self.request_id, self.start_place, self.end_place, self.weight, self.date, self.timeframe]
    
    def __repr__(self):
        return f"Request({self.to_list()})"
    @classmethod
    def from_list(cls, req_list):
        """
        Alternative constructor that creates a Request object
        from a list representation.
        Expected format: [request_id, start_place, end_place, weight, date, timeframe]
        """
        # Create a new instance without calling __init__ automatically
        obj = cls.__new__(cls)
        obj.request_id, obj.start_place, obj.end_place, obj.weight, obj.date, obj.timeframe = req_list
        return obj


# Ví dụ sử dụng:
if __name__ == "__main__":
    # Tạo một yêu cầu giao hàng ngẫu nhiên
    req = Request.generate(NUM_OF_NODES=10, start_from_0=True, single_start=True, small_weight=True)
    print(req)
    # Chuyển đổi về list
    print(req.to_list())
    
    # Ví dụ: lưu danh sách các yêu cầu vào file JSON (tương tự hàm gen_requests_and_save)
    num_requests = 5
    random.seed(42)
    requests = [Request.generate(NUM_OF_NODES=10, start_from_0=True) for _ in range(num_requests*2)]
    
    have_request = [0] * 10
    filtered_requests = []
    for r in requests:
        # Giả sử mỗi yêu cầu được nhận dạng bởi start_place[0]
        if have_request[r.start_place[0]]:
            continue
        have_request[r.start_place[0]] = 1
        filtered_requests.append(r.to_list())
    filtered_requests = filtered_requests[:num_requests]
    
    # Xác định đường dẫn hiện tại của file
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_file_dir, '..'))
    data_dir = os.path.join(project_root, 'data')
    
    # Tạo thư mục data nếu chưa tồn tại
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Lưu vào file JSON
    with open(os.path.join(data_dir, 'requests0.json'), 'w') as file:
        json.dump(filtered_requests, file, separators=(',', ': '))
    
    print("Đã lưu danh sách yêu cầu vào file JSON.")
