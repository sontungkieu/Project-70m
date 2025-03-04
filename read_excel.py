import csv
import os

import pandas as pd

from config import *
from objects.request import Request


def load_desdict():
    desdict = {}
    file_path = os.path.join("data", "destinations.csv")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert Name to uppercase and strip spaces
                name = row["Name"].strip().upper()
                desdict[name] = int(row["ID"].strip())
                print(f"Loaded destination: {name} -> {desdict[name]}")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return desdict


text2idDestination = load_desdict()
print(text2idDestination)

id = {}

# Đường dẫn đến file Excel (thay đổi nếu cần)
file_path = os.path.join("data", "input", "Lenh_Dieu_Xe.xlsx")

# Đọc file Excel
xls = pd.ExcelFile(file_path)

# Lấy tên của sheet đầu tiên
for sheet_name in xls.sheet_names[:-1]:
    # first_sheet_name = xls.sheet_names[0]
    # Đọc nội dung của sheet đầu tiên
    df = pd.read_excel(xls, sheet_name=sheet_name)
    sheet_name = sheet_name[:-1] + ("00" + sheet_name[-1])[-2:]
    # In hàng thứ 2 (chỉ số 1 trong DataFrame)
    if len(df) > 2:  # Kiểm tra xem có ít nhất 2 hàng không
        # print(f"Hàng thứ 2 trong sheet '{sheet_name}':")
        # print("+-----------------+")
        # for i in range(10):
        #     print(f'"{df.iloc[2,i]}",',end="")
        #     # print("+-----------------+")
        # print()
        col = [
            "STT",
            "TÊN HÀNG",
            "THỂ TÍCH (M3)",
            "LOẠI XE",
            "THỜI GIAN GIAO HÀNG",
            "GHI CHÚ",
            "NƠI BỐC HÀNG",
            "NV KẾ HOẠCH",
            "THU TIỀN LUÔN",
            "XUÁT HÓA ĐƠN",
        ]
        new_header = df.iloc[2, :10]  # Lấy hàng thứ 2 làm tiêu đề cột
        df_new = df.iloc[3:, :10].copy()  # Lấy dữ liệu từ hàng thứ 3 trở đi
        df_new.columns = new_header  # Gán tiêu đề mới
        df_new.reset_index(drop=True, inplace=True)
        # print(df_new.head())
        # print("+-----------------+")
        # for i in range(10):
        #     print(df_new.iloc[2,i])
        #     print("+-----------------+")

        valid_number_of_request = 0
        for index, row in df_new.iterrows():
            if row.isnull().all():
                break
            valid_number_of_request = index
            # valid_data.append(row.to_dict())
            df_new.loc[index, "STT"] = index
            df_new.loc[index, "THU TIỀN LUÔN"] = 0
            df_new.loc[index, "XUÁT HÓA ĐƠN"] = 0

        errors = []
        for index, row in df_new.iterrows():
            if index > valid_number_of_request:
                break
            if row.isnull().sum() > 0:  # Nếu hàng có ít nhất một ô trống
                missing_cols = row[
                    row.isnull()
                ].index.tolist()  # Lấy danh sách cột bị thiếu dữ liệu
                errors.append(f"Đơn {row['STT']} thiếu cột {', '.join(missing_cols)}")
        # In thông báo lỗi nếu có hàng thiếu dữ liệu
        if errors:
            print("\n⚠️ Lỗi dữ liệu:")
            for error in errors:
                print(error)
        else:
            print("\n✅ Dữ liệu hợp lệ, không có lỗi.")
        requests = []
        for index, row in df_new.iterrows():
            if index > valid_number_of_request:
                break
            # print(row['NƠI BỐC HÀNG'])
            # print(row)
            for u in row["NƠI BỐC HÀNG"].upper().split("+"):
                new_request = Request(
                    name=row["TÊN HÀNG"],
                    start_place=[text2idDestination.get(u.strip(), -1)],
                    # print(f"start_place: {start_place}, {row['NƠI BỐC HÀNG'].upper().split('+')[0]}")
                    # exit()
                    end_place="depot",
                    weight=row["THỂ TÍCH (M3)"],
                    date=TODAY,
                    timeframe=[0, 24],
                    note=row["GHI CHÚ"],
                    staff_id=id.get(row["NV KẾ HOẠCH"], 99),
                    split_id=0,
                )
                requests.append(new_request)
        requests = [request.to_list() for request in requests]
        # json dump requests
        import json

        with open(
            os.path.join("data", "intermediate", f"{sheet_name}.2025.json"),
            "w",
        ) as file:
            json.dump(requests, file, separators=(",", ": "))

    # từ các ngày (các sheet) tạo ra file json để thuật toán chạy

    else:
        print("Sheet không có đủ 2 hàng để hiển thị.")
