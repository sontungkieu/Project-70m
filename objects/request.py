# objects/request.py
import random
from datetime import datetime, timedelta

class Request:
    def __init__(self, name, start_place, end_place, weight, date, timeframe, note=".", staff_id=0, split_id=1):
        self.name = name
        self.start_place = start_place  # danh sách các điểm khởi đầu (ví dụ: [depot])
        self.end_place = end_place      # danh sách các điểm đến (1 phần tử)
        self.weight = weight
        self.date = date
        self.timeframe = timeframe
        self.note = note
        self.staff_id = staff_id
        self.split_id = split_id
        self.delivery_time = -1
        self.delivery_status = 0
        self.request_id = self.gen_id()

    def gen_id(self):
        # Tạo ID dựa trên date, timeframe, start_place, end_place, weight,...
        return f"{self.date}-{self.timeframe[0]:02d}-{self.timeframe[1]:02d}-{self.start_place[0]:03d}-{self.end_place[0]:03d}-{int(self.weight*10):03d}-{self.staff_id:02d}-{self.split_id:02d}"

    def to_list(self):
        return [self.name, self.start_place, self.end_place, self.weight, self.date, self.timeframe, self.note, self.staff_id, self.split_id, self.request_id]

    @classmethod
    def from_list(cls, lst):
        # Khôi phục đối tượng từ danh sách đã lưu
        return cls(*lst[:-1])  # Giả sử phần cuối lst là request_id (đã tạo tự động)

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
