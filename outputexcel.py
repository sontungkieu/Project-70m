import json

import pandas as pd


def json_routes_to_excel(input_json_path, output_excel_path):
    """
    Chuyển đổi dữ liệu từ file JSON chứa thông tin vehicles sang file Excel.

    File JSON có cấu trúc dạng danh sách, mỗi phần tử chứa key "vehicles"
    là dictionary mapping vehicle_id -> { "distance_of_route": ..., "list_of_route": [...] }.

    File Excel sẽ có các cột:
      - Day: Số thứ tự nhóm (mỗi phần tử JSON được xem là 1 ngày hoặc 1 nhóm).
      - Vehicle_ID: ID của xe.
      - Distance_of_route: Tổng quãng đường của lộ trình.
      - Route_Order: Thứ tự điểm trong lộ trình.
      - Node: ID của node.
      - Arrival_time: Thời gian đến.
      - Capacity: Sức chứa còn lại.
      - Delivered: Hàng giao tại điểm đó.
    """
    try:
        # Đọc dữ liệu từ file JSON
        with open(input_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rows = []
        # Mỗi phần tử trong danh sách JSON được xem là 1 "day" hoặc 1 nhóm.
        for day_index, group in enumerate(data, start=1):
            vehicles = group.get("vehicles", {})
            # Duyệt qua từng vehicle trong nhóm
            for vehicle_id, vehicle_info in vehicles.items():
                distance = vehicle_info.get("distance_of_route")
                route_list = vehicle_info.get("list_of_route", [])
                # Duyệt qua danh sách các node theo thứ tự
                for route_order, route in enumerate(route_list, start=1):
                    row = {
                        "Day": day_index,
                        "Vehicle_ID": vehicle_id,
                        "Distance_of_route": distance,
                        "Route_Order": route_order,
                        "Node": route.get("node"),
                        "Arrival_time": route.get("arrival_time"),
                        "Capacity": route.get("capacity"),
                        "Delivered": route.get("delivered"),
                    }
                    rows.append(row)

        # Tạo DataFrame từ các dòng dữ liệu
        df = pd.DataFrame(rows)

        # Ghi DataFrame ra file Excel
        df.to_excel(output_excel_path, index=False)
        print(f"✅ File Excel đã được lưu tại: {output_excel_path}")
    except Exception as e:
        print(f"❌ Lỗi khi chuyển đổi từ JSON sang Excel: {e}")


if __name__ == "__main__":
    # Đường dẫn file JSON đầu vào (thay đổi nếu cần)
    input_json_path = r"D:\Project 70\Project-70m-1\data\test\output.json"  # file JSON chứa dữ liệu như bạn cung cấp
    # Đường dẫn file Excel đầu ra
    output_excel_path = "routes.xlsx"
    json_routes_to_excel(input_json_path, output_excel_path)
