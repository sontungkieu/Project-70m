import pandas as pd
import json
import os
import random

def generate_time_window():
    """Sinh khoảng thời gian giao hàng ngẫu nhiên từ 6h đến 19h, kéo dài từ 1-3 giờ."""
    start_hour = random.randint(6, 16)
    end_hour = start_hour + random.randint(1, 3)
    return [f"{start_hour}:00", f"{end_hour}:00"]

def generate_delay_days():
    """Sinh số ngày delay ngẫu nhiên trong khoảng từ 0 đến 3 ngày."""
    return random.randint(0, 3)

def load_location_id_map(location_id_file):
    """
    Tải danh sách địa điểm xuất phát và địa điểm giao hàng từ file CSV.

    :param location_id_file: Đường dẫn tới file CSV chứa ID và địa chỉ.
    :return: Dictionary ánh xạ địa điểm với ID.
    """
    location_df = pd.read_csv(location_id_file)
    
    # Chuyển dữ liệu thành dictionary: {address: id}
    location_id_map = dict(zip(location_df["Address"], location_df["ID"]))
    
    return location_id_map

def excel_to_json(input_excel_path, sheet_name, location_id_file, output_json_path):
    """
    Chuyển đổi file Excel thành JSON với định dạng tối ưu, sử dụng ID có sẵn cho cả điểm xuất phát và điểm giao hàng.

    :param input_excel_path: Đường dẫn file Excel đầu vào.
    :param sheet_name: Tên sheet cần đọc.
    :param location_id_file: File CSV chứa ID của các địa điểm.
    :param output_json_path: Đường dẫn file JSON đầu ra.
    """
    try:
        # Kiểm tra file tồn tại
        if not os.path.exists(input_excel_path):
            print(f"❌ Lỗi: File '{input_excel_path}' không tồn tại!")
            return

        # Đọc file Excel
        df = pd.read_excel(input_excel_path, sheet_name=sheet_name)

        # Đổi tên các cột để dễ thao tác
        df = df.rename(columns={
            "TÊN KHÁCH HÀNG": "customer_name",
            "ĐỊA CHỈ GIAO HÀNG": "delivery_address",
            "Khối lượng hàng (m3)": "cargo_volume",
            "Nơi bốc": "pickup_location",
            "Thời gian giao hàng": "delivery_time"
        })

        # Chỉ giữ lại các cột cần thiết
        df = df[["customer_name", "delivery_address", "cargo_volume", "pickup_location", "delivery_time"]]

        # Tải ID của các địa điểm (cả start_point và delivery_point)
        location_id_map = load_location_id_map(location_id_file)

        processed_data = []

        for _, row in df.iterrows():
            start_location = row["pickup_location"]
            delivery_address = row["delivery_address"]

            # Lấy ID cho điểm xuất phát (start_point) và điểm giao hàng (delivery_point)
            start_id = location_id_map.get(start_location, -1)  # -1 nếu không tìm thấy
            delivery_id = location_id_map.get(delivery_address, -1)

            processed_entry = {
                "start_point": start_id,
                "delivery_point": delivery_id,
                "weight": row["cargo_volume"],
                "time_window": generate_time_window(),
                "delay_days": generate_delay_days()
            }
            processed_data.append(processed_entry)

        # Lưu file JSON
        with open(output_json_path, "w", encoding="utf-8") as json_file:
            json.dump(processed_data, json_file, indent=4, ensure_ascii=False)

        print(f"✅ Chuyển đổi thành công! File JSON đã lưu tại: {output_json_path}")

    except Exception as e:
        print(f"❌ Lỗi khi chuyển đổi file Excel sang JSON: {e}")

# ==========================
# 🚀 Chạy chương trình
# ==========================
if __name__ == "__main__":
    # Đường dẫn file Excel đầu vào
    input_excel_path = "DS_cong_ty_va_dia_chi_giao_hang.xlsx"

    # Tên sheet trong file Excel
    sheet_name = "Sheet1"

    # Đường dẫn file CSV chứa ID của các địa điểm (cả nơi bốc và điểm giao hàng)
    location_id_file = "location_ids.csv"

    # Đường dẫn file JSON đầu ra
    output_json_path = "processed_orders.json"

    # Chuyển đổi Excel sang JSON
    excel_to_json(input_excel_path, sheet_name, location_id_file, output_json_path)
