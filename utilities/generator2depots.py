import json
import os
import random
import sys
from datetime import datetime, timedelta
from typing import List

import numpy as np

# --- Lớp Request ---
class Request:
    def __init__(
        self,
        name: str,
        start_place: List[int],
        end_place: List[int],
        weight: int,
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
        request_id = self.date + "-"
        request_id += str(self.timeframe[0]).zfill(2) + "-"
        request_id += str(self.timeframe[1]).zfill(2) + "-"
        request_id += str(self.start_place[0]).zfill(3) + "-"
        request_id += str(self.end_place[0]).zfill(3) + "-"
        request_id += str(int(self.weight * 10)).zfill(3) + "-"
        request_id += str(self.staff_id).zfill(2) + "-"
        request_id += str(self.split_id).zfill(2)
        return request_id

    @classmethod
    def generate(
        cls,
        NUM_OF_NODES=55,
        start_from_0=True,
        single_start=True,
        small_weight=True,
        depots=[0, 1],
    ):
        # Xác định điểm bắt đầu
        if start_from_0:
            start_place = [0]
        else:
            k = 1 if single_start else random.randint(1, 4)
            start_place = random.sample([0, 1, 2, 3], k=k)
        # Chọn điểm kết thúc chỉ từ các nút không thuộc depot
        valid_end_nodes = [node for node in range(1, NUM_OF_NODES) if node not in depots]
        if not valid_end_nodes:
            raise ValueError("Không có node")
