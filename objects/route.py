from typing import List

from objects.request import Request


class Route:
    def __init__(self):
        self.route: List[Request] = []
        self.total_distance: float = 0.0
        self.date: str = ""
        self.vehicle_id: str = ""
