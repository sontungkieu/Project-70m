from typing import List

from objects.route import Route


class Driver:
    def __init__(
        self,
        name="Nguyen Van A",
        cccd="001000000000",
        vehicle_id="30A-12345",
        vehicle_load=97,
        route_by_day={"31102025": [0, 1, 2, 0]},
        phone_number="098789JQKA",
    ):
        self.name: str = name
        self.cccd: str = cccd
        self.vehicle_id: str = vehicle_id
        self.route_by_day: List[Route] = route_by_day
        self.phone_number: str = phone_number
        self.vehicle_load: int = vehicle_load
        self.available: bool = True

    def __str__(self):
        return f"{self.name} have id {self.cccd}."
