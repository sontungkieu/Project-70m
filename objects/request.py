import random
from datetime import datetime, timedelta
from typing import List

class Request:
    def __init__(
        self,
        name: str,
        start_place: List[int],
        end_place: List[int],
        weight: float,
        date: str,
        timeframe: List[int],
        note: str = ".",
        staff_id: int = 0,
        split_id: bool = 1,
    ):
        self.name = name
        self.start_place = start_place
        self.end_place = end_place
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
        return (
            f"{self.date}-"
            f"{str(self.timeframe[0]).zfill(2)}-"
            f"{str(self.timeframe[1]).zfill(2)}-"
            f"{str(self.start_place[0]).zfill(3)}-"
            f"{str(self.end_place[0]).zfill(3)}-"
            f"{str(int(self.weight * 10)).zfill(3)}-"
            f"{str(self.staff_id).zfill(2)}-"
            f"{str(self.split_id).zfill(2)}"
        )

    @classmethod
    def generate(
        cls,
        NUM_OF_NODES: int = 55,
        start_from_depot: bool = True,
        small_weight: bool = True,
        depots: List[int] = [0, 1],
        forced_depot: int = None,
        split_index: int = None,  # tham số phân chia vùng
    ):
        # Xác định depot khởi tạo
        if forced_depot is not None:
            depot = forced_depot
            start_place = [depot]
        elif start_from_depot:
            depot = random.choice(depots)
            start_place = [depot]
        else:
            start_place = [0]
            depot = 0

        # Nếu split_index chưa được truyền, dùng giá trị mặc định: (NUM_OF_NODES + 2)//2
        if split_index is None:
            split_index = (NUM_OF_NODES + 2) // 2

        # Xác định các node hợp lệ cho end_place dựa trên depot
        
        valid_end_nodes = [node for node in range(NUM_OF_NODES) if node not in depots]
        end_place = random.sample(valid_end_nodes, k=1)

        # Sinh trọng lượng
        weight = (random.randint(0, int(9.7 * 10)) / 10.0) if small_weight else (random.randint(54 * 10, 300 * 10) / 10.0)
        now = datetime.now()
        tomorrow = now + timedelta(days=random.randint(0, 10))
        formatted_date = tomorrow.strftime("%d%m%Y")
        gen_timeframe = sorted(random.sample(list(range(0, 24)), k=2))

        return cls(".", start_place, end_place, weight, formatted_date, gen_timeframe)

    def to_list(self):
        return [
            self.name,
            self.start_place,
            self.end_place,
            self.weight,
            self.date,
            self.timeframe,
            self.note,
            self.staff_id,
            self.split_id,
            self.request_id,
        ]

    @classmethod
    def from_list(cls, req_list):
        obj = cls.__new__(cls)
        (
            obj.name,
            obj.start_place,
            obj.end_place,
            obj.weight,
            obj.date,
            obj.timeframe,
            obj.note,
            obj.staff_id,
            obj.split_id,
            obj.request_id,
        ) = req_list
        return obj

    def __repr__(self):
        return f"Request({self.to_list()})"

if __name__ == "__main__":
    # Ví dụ: với NUM_OF_NODES=34 và mong muốn cho mỗi depot có đủ 15 yêu cầu,
    # ta đặt split_index = 2 + 15 = 17.
    req = Request.generate(NUM_OF_NODES=34, start_from_depot=True, small_weight=True, depots=[0, 1], forced_depot=1, split_index=17)
    print("Generated request:", req)
    print("As list:", req.to_list())
