import csv
import os

import pandas as pd
from openpyxl import load_workbook

from config import *
from objects.request import Request

# DROP_DOWN_RANGE_TAI_XE = "Tai_Xe!"


def read_dropdown_info(
    excel_file,
    target_cell,  # Ô cần tra cứu (ví dụ: "A1")
    dropdown_range,  # Dãy ô chứa danh sách dropdown (ví dụ: "Sheet2!A1:A10" hoặc "A1:A10")
    sheet1_name="Sheet1",  # Tên sheet chứa ô cần tra cứu
    sheet2_name="Sheet2",  # Tên sheet mặc định nếu dropdown_range không chỉ định
):
    # Load file Excel
    wb = load_workbook(excel_file, data_only=True)

    # Truy cập Sheet1
    if sheet1_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet1_name}' không tồn tại trong file {excel_file}")
    ws1 = wb[sheet1_name]

    # Phân tích dropdown_range
    if "!" in dropdown_range:
        sheet2_name, range_str = dropdown_range.split("!")
    else:
        range_str = dropdown_range

    # Truy cập Sheet2
    if sheet2_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet2_name}' không tồn tại trong file {excel_file}")
    ws2 = wb[sheet2_name]

    # Lấy danh sách giá trị dropdown từ range chỉ định
    dropdown_values = []
    address_map = {}
    for cell in ws2[range_str]:
        for c in cell:
            if c.value is not None:
                dropdown_values.append(c.value)
                # Giả sử cột bên cạnh chứa địa chỉ (cột kế tiếp)
                col_letter = chr(ord(c.column_letter) + 1)
                address_cell = ws2[f"{col_letter}{c.row}"]
                address_map[c.value] = address_cell.value or "Không có địa chỉ"

    # Lấy thông tin từ ô cần tra cứu
    target = ws1[target_cell]
    current_value = target.value

    if current_value in dropdown_values:
        index = dropdown_values.index(current_value)
        address = address_map.get(current_value, "Không có địa chỉ")
    else:
        index = -1
        address = "N/A"

    # Tạo kết quả
    result = {
        "cell": target.coordinate,
        "value": current_value,
        "dropdown_list": dropdown_values,
        "index_in_dropdown": index,
        "address": address,
    }

    # # In kết quả
    # print(f"Ô: {result['cell']}")
    # print(f"Giá trị hiện tại: {result['value']}")
    # print(f"Danh sách drop-down: {result['dropdown_list']}")
    # print(f"Số thứ tự trong drop-down: {result['index_in_dropdown']}")
    # print(f"Địa chỉ: {result['address']}")
    # print("-" * 50)

    return result


# Ví dụ sử dụng:
# result = read_dropdown_info(
#     "example.xlsx",
#     target_cell="A1",
#     dropdown_range="Sheet2!A1:A10",
#     sheet1_name="Sheet1"
# )
#
# result = read_dropdown_info(
#     "example.xlsx",
#     target_cell="A1",
#     dropdown_range="A1:A10",  # Không có tên sheet, dùng sheet2_name mặc định
#     sheet1_name="Sheet1",
#     sheet2_name="Sheet2"
# )


# Sử dụng hàm
# if __name__ == '__main__':
#     # read_dropdown_info(excel_file)
#     result   = read_dropdown_info(
#         "Lenh_Dieu_Xe.xlsx",
#         target_cell="B5",
#         dropdown_range=DROP_DOWN_RANGE_DIA_CHI,
#         sheet1_name=TODAY
#     )['index_in_dropdown']


def read_excel_file():
    # Đường dẫn đến file Excel
    file_path = os.path.join("Lenh_Dieu_Xe.xlsx")

    # Load workbook
    wb = load_workbook(file_path, data_only=True)
    sheet_name = TODAY

    # Kiểm tra sheet có tồn tại không
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet_name}' không tồn tại trong file {file_path}")

    # Truy cập sheet
    ws = wb[sheet_name]

    # Lấy tiêu đề từ A4:K4 (hàng 4, cột 1 đến 11)
    headers = [cell.value for cell in ws["A4":"K4"][0]]

    # Đọc dữ liệu từ hàng 5 trở đi
    data = []
    row_index = 5  # Bắt đầu từ hàng 5
    while True:
        row = [cell.value for cell in ws[f"A{row_index}":f"K{row_index}"][0]]

        # Dừng nếu cột B (index 1) trống
        if pd.isna(row[1]) or row[1] is None:
            break

        data.append(row)
        row_index += 1

    # Tạo DataFrame
    df = pd.DataFrame(data, columns=headers)

    # Báo cáo các trường trống
    errors = []
    for index, row in df.iterrows():
        # Kiểm tra các cột khác cột B (vì cột B đã được kiểm tra để dừng)
        missing_cols = [
            col for col in df.columns if col != df.columns[1] and pd.isna(row[col])
        ]
        if missing_cols:
            errors.append(
                f"Hàng {index + 5} thiếu dữ liệu ở cột: {', '.join(missing_cols)}"
            )

    # In báo cáo
    if errors:
        print("\n⚠️ Các trường trống được phát hiện:")
        for error in errors:
            print(error)
    else:
        print("\n✅ Không có trường nào trống ngoài cột B dùng để dừng.")

    # Xử lý cột B (TÊN) với dropdown list
    for index, row in df.iterrows():
        if row[df.columns[1]]:  # Cột B
            result = read_dropdown_info(
                excel_file=file_path,
                target_cell=f"B{index + 5}",  # +5 vì bắt đầu từ hàng 5
                dropdown_range=DROP_DOWN_RANGE_DIA_CHI,  # Giả định range dropdown, thay đổi nếu cần
                sheet1_name=sheet_name,
            )
            # Có thể lưu hoặc xử lý thêm với result ở đây

    return df


# Chạy hàm
if __name__ == "__main__":
    try:
        df = read_excel_file()
        print("\nDữ liệu đã đọc:")
        print(df)
    except Exception as e:
        print(f"Lỗi: {e}")
