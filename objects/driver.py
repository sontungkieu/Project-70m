class Driver:
    def __init__(
        self,
        name="Nguyen Van A",
        cccd="001000000000",
        vehicle_id="30A-12345",
        vehicle_load=97,
        route_by_day=None,
        phone_number="098789JQKA",
        available_times=None,
    ):
        self.name: str = name
        self.cccd: str = cccd
        self.vehicle_id: str = vehicle_id
        self.route_by_day = route_by_day if route_by_day is not None else {}
        self.routes_today = None
        self.phone_number: str = phone_number
        self.vehicle_load: int = vehicle_load
        self.available_times: dict = available_times if available_times is not None else {}

    def update_available_times(self, day: str, times: list):
        if day in self.available_times:
            if self.available_times[day] == times:
                print(f"No change in available times for {day}. Times remain: {times}")
            else:
                print(f"Updating available times for {day}.")
                print(f"Old times: {self.available_times[day]}")
                print(f"New times: {times}")
                self.available_times[day] = times
        else:
            print(f"Adding new available times for {day}.")
            print(f"Times: {times}")
            self.available_times[day] = times

    def to_dict(self):
        return {
            "name": self.name,
            "cccd": self.cccd,
            "vehicle_id": self.vehicle_id,
            "vehicle_load": self.vehicle_load,
            "route_by_day": self.route_by_day,
            "phone_number": self.phone_number,
            "available_times": self.available_times,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data.get("name", "Nguyen Van A"),
            cccd=data.get("cccd", "001000000000"),
            vehicle_id=data.get("vehicle_id", "30A-12345"),
            vehicle_load=data.get("vehicle_load", 97),
            route_by_day=data.get("route_by_day", {}),
            phone_number=data.get("phone_number", "098789JQKA"),
            available_times=data.get("available_times", {}),
        )

    def __str__(self):
        return f"{self.name} have id {self.cccd}."
