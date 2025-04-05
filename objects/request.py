# objects/request.py
import random
from datetime import datetime, timedelta
from typing import List

class Request:
    def __init__(self, name:str, start_place:List[int], end_place:List[int], weight:float, date, timeframe, note=".", staff_id=0, split_id=0, original_request_id=None):
        self.name = name
        self.start_place = start_place  # danh sách các điểm khởi đầu (ví dụ: [depot])
        self.end_place = end_place      # danh sách các điểm đến (1 phần tử)
        self.weight = weight
        self.date = date
        self.timeframe = timeframe
        self.note = note
        self.staff_id = staff_id
        self.split_id = split_id
        self.request_id = self.gen_id()
        self.original_request_id = original_request_id if original_request_id is not None else self.request_id
        self.delivery_time = -1
        self.delivery_status = 0
        # Nếu không có original_request_id, sử dụng request_id hiện tại làm ID gốc


    def gen_id(self):
        # Tạo ID dựa trên date, timeframe, start_place, end_place, weight,...
        return f"{self.date}-F{self.timeframe[0]:02d}-T{self.timeframe[1]:02d}-S{self.start_place[0]:03d}-E{self.end_place[0]:03d}-W{int(self.weight):03d}-{self.staff_id:02d}-{self.split_id:02d}"

    def to_dict(self):
        return {
            "name": self.name,
            "start_place": self.start_place,
            "end_place": self.end_place,
            "weight": self.weight,
            "date": self.date,
            "timeframe": self.timeframe,
            "note": self.note,
            "staff_id": self.staff_id,
            "split_id": self.split_id,
            "request_id": self.request_id,
            "original_request_id": getattr(self, "original_request_id", None),
            "delivery_time": self.delivery_time,
            "delivery_status": self.delivery_status,
        }


    @classmethod
    def from_dict(cls, dict_data):
        # Tạo instance mới từ dictionary
        request = cls(
            name=dict_data["name"],
            start_place=dict_data["start_place"],
            end_place=dict_data["end_place"],
            weight=dict_data["weight"],
            date=dict_data["date"],
            timeframe=dict_data["timeframe"],
            note=dict_data["note"],
            staff_id=dict_data["staff_id"],
            split_id=dict_data["split_id"],
        )
        # Kiểm tra request_id có tồn tại trong dict_data không và có khớp với ID đã tạo không
        if dict_data.get("request_id",None) != request.request_id:
            raise ValueError("request_id không khớp với ID đã tạo.")
        else:
            request.request_id = dict_data["request_id"]
        # Nếu có original_request_id trong dict_data, gán cho instance
        if "original_request_id" in dict_data:
            request.original_request_id = dict_data["original_request_id"]
        else:
            request.original_request_id = request.request_id
        # Gán thêm các thuộc tính không nằm trong __init__
        request.delivery_time = dict_data["delivery_time"]
        request.delivery_status = dict_data["delivery_status"]
        # request_id đã được tạo tự động trong __init__
        return request
    
    @classmethod
    def generate(cls, NUM_OF_NODES=55, start_from_depot=False, small_weight=True, depots=[0,1], forced_depot=None, split_index=0):
        """
        Sinh yêu cầu giao hàng ngẫu nhiên.
          - Nếu start_from_depot=True và forced_depot được cung cấp thì start_place sẽ được ép là [forced_depot].
          - end_place được chọn từ các node không thuộc các depot.
          - split_index có thể được dùng để xử lý các yêu cầu “chia nhỏ” (không bắt buộc trong mẫu này).
        """
        if start_from_depot and forced_depot is not None:
            start_place = [forced_depot]
        else:
            # Nếu không ép buộc, ta lấy mặc định là depot 0 (có thể thay đổi nếu cần)
            start_place = [0]
        valid_end_nodes = [node for node in range(NUM_OF_NODES) if node not in depots]
        if not valid_end_nodes:
            raise ValueError("Không có node kết thúc hợp lệ.")
        end_place = [random.choice(valid_end_nodes)]
        if small_weight:
            weight = round(random.uniform(0.1, 9.7), 1)
        else:
            weight = round(random.uniform(9.7, 54), 1)
        tomorrow = datetime.now() + timedelta(days=random.randint(0, 10))
        date_str = tomorrow.strftime("%d%m%Y")
        hours = random.sample(range(0, 24), 2)
        timeframe = sorted(hours)
        return cls("Request", start_place, end_place, weight, date_str, timeframe)

    @classmethod
    def generate_single_deport(
        cls,
        NUM_OF_NODES=55,
        start_from_0=True,
        single_start=True,
        small_weight=True,
    ):
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
        if small_weight is True:
            weight = random.randint(0, int(9.7 * 10)) / 10
        elif small_weight is False:
            weight = random.randint(54 * 10, 300 * 10) / 10
        else:
            weight = random.randint(24 * 10, 150 * 10) / 10

        # Ngày giao hàng (giá trị ngẫu nhiên từ 0 đến 3)
        now = datetime.now()
        tomorrow = now + timedelta(days=random.randint(0, 10))
        formatted_date = tomorrow.strftime("%d%m%Y")
        # Khung giờ giao hàng: 2 giờ được chọn ngẫu nhiên trong ngày và sắp xếp tăng dần
        gen_timeframe = sorted(random.sample(list(range(0, 24)), k=2))

        # Tạo mã yêu cầu theo định dạng:
        # <ngày giao (ngày mai)>-<giờ1>-<giờ2>-<start_place[0]>-<end_place[0]>-<trọng lượng*10>-<id ngẫu nhiên 2 số>

        return cls(".", start_place, end_place, weight, formatted_date, gen_timeframe)
    def __str__(self):
        return f"Request {self.request_id}: {self.start_place} -> {self.end_place}, weight={self.weight}, date={self.date}, timeframe={self.timeframe}"
