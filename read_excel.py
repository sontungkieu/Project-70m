# # import csv
# # import os
# # import warnings

# # import pandas as pd
# # from openpyxl import load_workbook
# # from openpyxl.utils import get_column_letter
# # from typing import List

# # from config import *
# # from objects.request import Request

# # warnings.filterwarnings("ignore", category=UserWarning)
# # DROP_DOWN_EXT = "_DROP_DOWN_ID"
# # # Ví dụ sử dụng:
# # # result = read_dropdown_info(
# # #     "example.xlsx",
# # #     target_cell="A1",
# # #     dropdown_range="Sheet2!A1:A10",
# # #     sheet1_name="Sheet1"
# # # )
# # #
# # # result = read_dropdown_info(
# # #     "example.xlsx",
# # #     target_cell="A1",
# # #     dropdown_range="A1:A10",  # Không có tên sheet, dùng sheet2_name mặc định
# # #     sheet1_name="Sheet1",
# # #     sheet2_name="Sheet2"
# # # )


# # # Sử dụng hàm
# # # if __name__ == '__main__':
# # #     # read_dropdown_info(excel_file)
# # #     result   = read_dropdown_info(
# # #         "Lenh_Dieu_Xe.xlsx",
# # #         target_cell="B5",
# # #         dropdown_range=DROP_DOWN_RANGE_DIA_CHI,
# # #         sheet1_name=TODAY
# # #     )['index_in_dropdown']


# # def read_dropdown_info(
# #     excel_file,
# #     target_cell,  # Ô cần tra cứu (ví dụ: "A1")
# #     dropdown_range,  # Dãy ô chứa danh sách dropdown (ví dụ: "Sheet2!A1:A10" hoặc "A1:A10")
# #     sheet1_name="Sheet1",  # Tên sheet chứa ô cần tra cứu
# #     sheet2_name="Sheet2",  # Tên sheet mặc định nếu dropdown_range không chỉ định
# # ):
# #     # Load file Excel
# #     wb = load_workbook(excel_file, data_only=True)

# #     # Truy cập Sheet1
# #     if sheet1_name not in wb.sheetnames:
# #         raise ValueError(f"Sheet '{sheet1_name}' không tồn tại trong file {excel_file}")
# #     ws1 = wb[sheet1_name]

# #     # Phân tích dropdown_range
# #     if "!" in dropdown_range:
# #         sheet2_name, range_str = dropdown_range.split("!")
# #     else:
# #         range_str = dropdown_range

# #     # Truy cập Sheet2
# #     if sheet2_name not in wb.sheetnames:
# #         raise ValueError(f"Sheet '{sheet2_name}' không tồn tại trong file {excel_file}")
# #     ws2 = wb[sheet2_name]

# #     # Lấy danh sách giá trị dropdown từ range chỉ định
# #     dropdown_values = []
# #     address_map = {}
# #     for cell in ws2[range_str]:
# #         for c in cell:
# #             if c.value is not None:
# #                 dropdown_values.append(c.value)
# #                 # Giả sử cột bên cạnh chứa địa chỉ (cột kế tiếp)
# #                 col_letter = chr(ord(c.column_letter) + 1)
# #                 address_cell = ws2[f"{col_letter}{c.row}"]
# #                 address_map[c.value] = address_cell.value or "Không có địa chỉ"

# #     # Lấy thông tin từ ô cần tra cứu
# #     target = ws1[target_cell]
# #     current_value = target.value

# #     if current_value in dropdown_values:
# #         index = dropdown_values.index(current_value)
# #         address = address_map.get(current_value, "Không có địa chỉ")
# #     else:
# #         index = -1
# #         address = "N/A"

# #     # Tạo kết quả
# #     result = {
# #         "cell": target.coordinate,
# #         "value": current_value,
# #         "dropdown_list": dropdown_values,
# #         "index_in_dropdown": index,
# #         "address": address,
# #     }

# #     return result


# # def read_dropdown_info(
# #     excel_file,
# #     target_cell,  # Ô cần tra cứu (ví dụ: "A1")
# #     dropdown_range,  # Dãy ô chứa danh sách dropdown (ví dụ: "Sheet2!A1:A10" hoặc "A1:A10")
# #     sheet1_name="Sheet1",  # Tên sheet chứa ô cần tra cứu
# #     sheet2_name="Sheet2",  # Tên sheet mặc định nếu dropdown_range không chỉ định
# # ):
# #     # Load file Excel
# #     wb = load_workbook(excel_file, data_only=True)

# #     # Truy cập Sheet1
# #     if sheet1_name not in wb.sheetnames:
# #         raise ValueError(f"Sheet '{sheet1_name}' không tồn tại trong file {excel_file}")
# #     ws1 = wb[sheet1_name]

# #     # Phân tích dropdown_range
# #     if "!" in dropdown_range:
# #         sheet2_name, range_str = dropdown_range.split("!")
# #     else:
# #         range_str = dropdown_range

# #     # Truy cập Sheet2
# #     if sheet2_name not in wb.sheetnames:
# #         raise ValueError(f"Sheet '{sheet2_name}' không tồn tại trong file {excel_file}")
# #     ws2 = wb[sheet2_name]

# #     # Lấy danh sách giá trị dropdown từ range chỉ định
# #     dropdown_values = []
# #     address_map = {}
# #     for cell in ws2[range_str]:
# #         for c in cell:
# #             if c.value is not None:
# #                 dropdown_values.append(c.value)
# #                 # Lấy cột kế tiếp bằng cách sử dụng openpyxl.utils
# #                 col_num = c.column + 1  # Số cột tiếp theo
# #                 col_letter = get_column_letter(col_num)  # Chuyển sang ký tự cột
# #                 address_cell = ws2[f"{col_letter}{c.row}"]
# #                 address_map[c.value] = address_cell.value or "Không có địa chỉ"

# #     # Lấy thông tin từ ô cần tra cứu
# #     target = ws1[target_cell]
# #     current_value = target.value

# #     if current_value in dropdown_values:
# #         index = dropdown_values.index(current_value)
# #         address = address_map.get(current_value, "Không có địa chỉ")
# #     else:
# #         index = -1
# #         address = "N/A"

# #     # Tạo kết quả
# #     result = {
# #         "cell": target.coordinate,
# #         "value": current_value,
# #         "dropdown_list": dropdown_values,
# #         "index_in_dropdown": index,
# #         "address": address,
# #     }

# #     return result


# # def read_excel_file():
# #     # Đường dẫn đến file Excel
# #     file_path = os.path.join("Lenh_Dieu_Xe.xlsx")

# #     # Load workbook
# #     wb = load_workbook(file_path, data_only=True)
# #     sheet_name = TODAY

# #     # Kiểm tra sheet có tồn tại không
# #     if sheet_name not in wb.sheetnames:
# #         raise ValueError(f"Sheet '{sheet_name}' không tồn tại trong file {file_path}")

# #     # Truy cập sheet
# #     ws = wb[sheet_name]

# #     # Lấy tiêu đề từ A4:K4 (hàng 4, cột 1 đến 11) và trim khoảng trắng
# #     headers = [
# #         cell.value.strip() if isinstance(cell.value, str) else cell.value
# #         for cell in ws["A4":"K4"][0]
# #     ]

# #     # Đọc dữ liệu từ hàng 5 trở đi
# #     data = []
# #     row_index = 5  # Bắt đầu từ hàng 5
# #     while True:
# #         row = [cell.value for cell in ws[f"A{row_index}":f"K{row_index}"][0]]

# #         # Dừng nếu cột B (index 1) trống
# #         if pd.isna(row[1]) or row[1] is None:
# #             break

# #         data.append(row)
# #         row_index += 1

# #     # Tạo DataFrame
# #     df = pd.DataFrame(data, columns=headers)

# #     # Thêm cột mới để lưu index_in_dropdown
# #     dropdown_columns = {
# #         "KHÁCH HÀNG": DROP_DOWN_RANGE_DIA_CHI,  # Giả định từ config
# #         "LOẠI XE": "CONFIG!F1:F6",
# #         "THỜI GIAN GIAO HÀNG": "CONFIG!AA1:AA5",
# #         "NƠI BỐC HÀNG": "Dia_Chi!A1:A6",
# #         "NV KẾ HOẠCH": "CONFIG!B3:B7",
# #         "THU TIỀN LUÔN": "CONFIG!AB1:AB2",
# #         "XUÁT HÓA ĐƠN": "CONFIG!AB1:AB2",
# #         "ĐÃ GIAO": "CONFIG!AB1:AB2",
# #     }

# #     # Khởi tạo các cột dropdown với giá trị None
# #     for column_name in dropdown_columns.keys():
# #         if column_name in df.columns:
# #             df[column_name + DROP_DOWN_EXT] = None

# #     # Áp dụng .split()[0] cho cột 'STT'
# #     if "STT" in df.columns:
# #         df["STT"] = df["STT"].apply(lambda x: x.split()[1] if isinstance(x, str) else x)

# #     # Báo cáo các trường trống
# #     errors = []
# #     for index, row in df.iterrows():
# #         # Kiểm tra các cột khác cột B (vì cột B đã được kiểm tra để dừng)
# #         missing_cols = [
# #             col for col in df.columns if col != df.columns[1] and pd.isna(row[col])
# #         ]
# #         if missing_cols:
# #             errors.append(
# #                 f"Hàng {index + 5} thiếu dữ liệu ở cột: {', '.join(missing_cols)}"
# #             )

# #     # In báo cáo
# #     if errors:
# #         print("\n⚠️ Các trường trống được phát hiện:")
# #         for error in errors:
# #             print(error)
# #     else:
# #         print("\n✅ Không có trường nào trống ngoài cột B dùng để dừng.")

# #     # Xử lý các cột với dropdown list và lưu index_in_dropdown
# #     column_to_position = {
# #         name: chr(65 + i) for i, name in enumerate(headers)
# #     }  # A=65, B=66,...
# #     for index, row in df.iterrows():
# #         for column_name, dropdown_range in dropdown_columns.items():
# #             if column_name in df.columns and row[column_name]:
# #                 result = read_dropdown_info(
# #                     excel_file=file_path,
# #                     target_cell=f"{column_to_position[column_name]}{index + 5}",  # +5 vì bắt đầu từ hàng 5
# #                     dropdown_range=dropdown_range,
# #                     sheet1_name=sheet_name,
# #                 )
# #                 df.at[index, column_name + DROP_DOWN_EXT] = result["index_in_dropdown"]

# #     return df


# # # # Chạy hàm
# # # if __name__ == "__main__":
# # #     try:
# # #         df = read_excel_file()
# # #         print("\nDữ liệu đã đọc:")
# # #         print(df.head())
# # #         print("\nDanh sách cột:")
# # #         print(df.columns.tolist())
# # #     except Exception as e:
# # #         print(f"Lỗi: {e}")
# # # Chạy hàm
# # # Chạy hàm

# # def convert_to_object(df: pd.DataFrame) -> List[Request]:
# #     DROP_DOWN_EXT = "_DROP_DOWN_ID"
# #     dropdown_columns = [
# #         "KHÁCH HÀNG",
# #         "LOẠI XE",
# #         "THỜI GIAN GIAO HÀNG",
# #         "NƠI BỐC HÀNG",
# #         "NV KẾ HOẠCH",
# #         "THU TIỀN LUÔN",
# #         "XUÁT HÓA ĐƠN",
# #         "ĐÃ GIAO",
# #     ]

# #     print("\nDữ liệu trước khi gán và xóa:")
# #     print(df.head())

# #     for column_name in dropdown_columns:
# #         if column_name in df.columns and column_name + DROP_DOWN_EXT in df.columns:
# #             df[column_name] = df[column_name + DROP_DOWN_EXT]

# #     drop_columns = [col for col in df.columns if DROP_DOWN_EXT in col]
# #     df = df.drop(columns=drop_columns)

# #     print("\nDữ liệu sau khi gán và xóa các cột _DROP_DOWN_ID:")
# #     print(df.head())
# #     print("\nDanh sách cột sau khi xử lý:")
# #     print(df.columns.tolist())

# #     requests = []
# #     for index, row in df.iterrows():
# #         try:
# #             request = Request(
# #                 name=str(row["KHÁCH HÀNG"]) if pd.notna(row["KHÁCH HÀNG"]) else "",
# #                 start_place=[int(row["NƠI BỐC HÀNG"])] if pd.notna(row["NƠI BỐC HÀNG"]) else [0],
# #                 end_place=[int(row["KHÁCH HÀNG"])] if pd.notna(row["KHÁCH HÀNG"]) else [0],
# #                 weight=int(row["THỂ TÍCH (M3)"]) if pd.notna(row["THỂ TÍCH (M3)"]) else 0,
# #                 date=str(TODAY),
# #                 timeframe=[int(row["THỜI GIAN GIAO HÀNG"])] if pd.notna(row["THỜI GIAN GIAO HÀNG"]) else [0],
# #                 note=str(row["GHI CHÚ"]) if pd.notna(row["GHI CHÚ"]) else ".",
# #                 staff_id=int(row["NV KẾ HOẠCH"]) if pd.notna(row["NV KẾ HOẠCH"]) else 0,
# #                 split_id=bool(row["STT"]) if pd.notna(row["STT"]) else True
# #             )
# #             request.delivery_status = int(row["ĐÃ GIAO"]) if pd.notna(row["ĐÃ GIAO"]) else 0
# #             requests.append(request)
# #         except Exception as e:
# #             print(f"Lỗi khi xử lý hàng {index + 5}: {e}")

# #     return requests

# # if __name__ == "__main__":
# #     try:
# #         df = read_excel_file()
# #         requests = convert_to_object(df)
# #         print("\nDanh sách các đối tượng Request:")
# #         for i, req in enumerate(requests[:5]):
# #             print(f"Request {i + 1}:")
# #             print(f"  Name: {req.name}")
# #             print(f"  Start Place: {req.start_place}")
# #             print(f"  End Place: {req.end_place}")
# #             print(f"  Weight: {req.weight}")
# #             print(f"  Date: {req.date}")
# #             print(f"  Timeframe: {req.timeframe}")
# #             print(f"  Note: {req.note}")
# #             print(f"  Staff ID: {req.staff_id}")
# #             print(f"  Split ID: {req.split_id}")
# #             print(f"  Delivery Status: {req.delivery_status}")
# #             print(f"  Request ID: {req.request_id}")
# #     except Exception as e:
# #         print(f"Lỗi: {e}")

# # # if __name__ == "__main__":
# # #     try:
# # #         df = read_excel_file()
# # #         print("\nDữ liệu trước khi gán và xóa:")
# # #         print(df.head())

# # #         # Định nghĩa hậu tố dropdown
# # #         DROP_DOWN_EXT = "_DROP_DOWN_ID"
# # #         dropdown_columns = [
# # #             "KHÁCH HÀNG",
# # #             "LOẠI XE",
# # #             "THỜI GIAN GIAO HÀNG",
# # #             "NƠI BỐC HÀNG",
# # #             "NV KẾ HOẠCH",
# # #             "THU TIỀN LUÔN",
# # #             "XUÁT HÓA ĐƠN",
# # #             "ĐÃ GIAO",
# # #         ]

# # #         # Gán các cột _DROP_DOWN_ID cho cột chính tương ứng
# # #         for column_name in dropdown_columns:
# # #             if column_name in df.columns and column_name + DROP_DOWN_EXT in df.columns:
# # #                 df[column_name] = df[column_name + DROP_DOWN_EXT]

# # #         # Xóa tất cả các cột _DROP_DOWN_ID
# # #         drop_columns = [col for col in df.columns if DROP_DOWN_EXT in col]
# # #         df = df.drop(columns=drop_columns)

# # #         print("\nDữ liệu sau khi gán và xóa các cột _DROP_DOWN_ID:")
# # #         print(df.head())
# # #         print("\nDanh sách cột sau khi xử lý:")
# # #         print(df.columns.tolist())  # Kiểm tra thứ tự cột
# # #     except Exception as e:
# # #         print(f"Lỗi: {e}")
# import csv
# import os
# import pandas as pd
# from openpyxl import load_workbook
# from openpyxl.utils import get_column_letter
# from typing import List

# from config import *
# from objects.request import Request

# def read_dropdown_info(
#     excel_file,
#     target_cell,
#     dropdown_range,
#     sheet1_name="Sheet1",
#     sheet2_name="Sheet2",
# ):
#     wb = load_workbook(excel_file, data_only=True)
#     if sheet1_name not in wb.sheetnames:
#         raise ValueError(f"Sheet '{sheet1_name}' không tồn tại trong file {excel_file}")
#     ws1 = wb[sheet1_name]
#     if "!" in dropdown_range:
#         sheet2_name, range_str = dropdown_range.split("!")
#     else:
#         range_str = dropdown_range
#     if sheet2_name not in wb.sheetnames:
#         raise ValueError(f"Sheet '{sheet2_name}' không tồn tại trong file {excel_file}")
#     ws2 = wb[sheet2_name]

#     dropdown_values = []
#     address_map = {}
#     for cell in ws2[range_str]:
#         for c in cell:
#             if c.value is not None:
#                 dropdown_values.append(c.value)
#                 col_num = c.column + 1
#                 col_letter = get_column_letter(col_num)
#                 address_cell = ws2[f"{col_letter}{c.row}"]
#                 address_map[c.value] = address_cell.value or "Không có địa chỉ"

#     target = ws1[target_cell]
#     current_value = target.value
#     if current_value in dropdown_values:
#         index = dropdown_values.index(current_value)
#         address = address_map.get(current_value, "Không có địa chỉ")
#     else:
#         index = -1
#         address = "N/A"

#     return {
#         "cell": target.coordinate,
#         "value": current_value,
#         "dropdown_list": dropdown_values,
#         "index_in_dropdown": index,
#         "address": address,
#     }

# def read_excel_file():
#     file_path = os.path.join("Lenh_Dieu_Xe.xlsx")
#     wb = load_workbook(file_path, data_only=True)
#     sheet_name = TODAY
#     if sheet_name not in wb.sheetnames:
#         raise ValueError(f"Sheet '{sheet_name}' không tồn tại trong file {file_path}")
#     ws = wb[sheet_name]

#     headers = [cell.value.strip() if isinstance(cell.value, str) else cell.value for cell in ws["A4":"K4"][0]]
#     data = []
#     row_index = 5
#     while True:
#         row = [cell.value for cell in ws[f"A{row_index}":f"K{row_index}"][0]]
#         if pd.isna(row[1]) or row[1] is None:
#             break
#         data.append(row)
#         row_index += 1

#     df = pd.DataFrame(data, columns=headers)

#     DROP_DOWN_EXT = "_DROP_DOWN_ID"
#     dropdown_columns = {
#         'KHÁCH HÀNG': DROP_DOWN_RANGE_DIA_CHI,
#         'LOẠI XE': 'CONFIG!F1:F6',
#         'THỜI GIAN GIAO HÀNG': 'CONFIG!AA1:AA5',
#         'NV KẾ HOẠCH': 'CONFIG!B3:B7',
#         'THU TIỀN LUÔN': 'CONFIG!AB1:AB2',
#         'XUÁT HÓA ĐƠN': 'CONFIG!AB1:AB2',
#         'ĐÃ GIAO': 'CONFIG!AB1:AB2',
#         'NƠI BỐC HÀNG': 'Dia_Chi!A1:A6'
#     }

#     for column_name in dropdown_columns.keys():
#         if column_name in df.columns:
#             df[column_name + DROP_DOWN_EXT] = None

#     if 'STT' in df.columns:
#         df['STT'] = df['STT'].apply(lambda x: x.split()[1] if isinstance(x, str) and len(x.split()) > 1 else (x.split()[0] if isinstance(x, str) and len(x.split()) > 0 else x))

#     errors = []
#     for index, row in df.iterrows():
#         missing_cols = [col for col in df.columns if col != df.columns[1] and pd.isna(row[col])]
#         if missing_cols:
#             errors.append(f"Hàng {index + 5} thiếu dữ liệu ở cột: {', '.join(missing_cols)}")

#     if errors:
#         print("\n⚠️ Các trường trống được phát hiện:")
#         for error in errors:
#             print(error)
#     else:
#         print("\n✅ Không có trường nào trống ngoài cột B dùng để dừng.")

#     column_to_position = {name: chr(65 + i) for i, name in enumerate(headers)}
#     for index, row in df.iterrows():
#         for column_name, dropdown_range in dropdown_columns.items():
#             if column_name in df.columns and row[column_name]:
#                 result = read_dropdown_info(
#                     excel_file=file_path,
#                     target_cell=f"{column_to_position[column_name]}{index + 5}",
#                     dropdown_range=dropdown_range,
#                     sheet1_name=sheet_name,
#                 )
#                 df.at[index, column_name + DROP_DOWN_EXT] = result['index_in_dropdown']

#     return df

# def convert_to_object(df: pd.DataFrame) -> List[Request]:
#     DROP_DOWN_EXT = "_DROP_DOWN_ID"
#     dropdown_columns = [
#         "KHÁCH HÀNG",
#         "LOẠI XE",
#         "THỜI GIAN GIAO HÀNG",
#         "NƠI BỐC HÀNG",
#         "NV KẾ HOẠCH",
#         "THU TIỀN LUÔN",
#         "XUÁT HÓA ĐƠN",
#         "ĐÃ GIAO",
#     ]

#     print("\nDữ liệu trước khi gán và xóa:")
#     print(df.head())

#     for column_name in dropdown_columns:
#         if column_name in df.columns and column_name + DROP_DOWN_EXT in df.columns:
#             df[column_name] = df[column_name + DROP_DOWN_EXT]

#     drop_columns = [col for col in df.columns if DROP_DOWN_EXT in col]
#     df = df.drop(columns=drop_columns)

#     print("\nDữ liệu sau khi gán và xóa các cột _DROP_DOWN_ID:")
#     print(df.head())
#     print("\nDanh sách cột sau khi xử lý:")
#     print(df.columns.tolist())

#     requests = []
#     for index, row in df.iterrows():
#         try:
#             # In dữ liệu hàng để kiểm tra
#             print(f"\nHàng {index + 5}:")
#             print(row)
#             # Xử lý an toàn các giá trị
#             name = str(row["KHÁCH HÀNG"]) if pd.notna(row["KHÁCH HÀNG"]) else ""
#             start_place = [int(row["NƠI BỐC HÀNG"])] if pd.notna(row["NƠI BỐC HÀNG"]) and str(row["NƠI BỐC HÀNG"]).isdigit() else [0]
#             end_place = [int(row["KHÁCH HÀNG"])] if pd.notna(row["KHÁCH HÀNG"]) and str(row["KHÁCH HÀNG"]).isdigit() else [0]
#             weight = int(row["THỂ TÍCH (M3)"]) if pd.notna(row["THỂ TÍCH (M3)"]) and str(row["THỂ TÍCH (M3)"]).replace('.', '').isdigit() else 0
#             date = str(TODAY)
#             timeframe = [int(row["THỜI GIAN GIAO HÀNG"])] if pd.notna(row["THỜI GIAN GIAO HÀNG"]) and str(row["THỜI GIAN GIAO HÀNG"]).isdigit() else [0]
#             note = str(row["GHI CHÚ"]) if pd.notna(row["GHI CHÚ"]) else "."
#             staff_id = int(row["NV KẾ HOẠCH"]) if pd.notna(row["NV KẾ HOẠCH"]) and str(row["NV KẾ HOẠCH"]).isdigit() else 0
#             split_id = bool(row["STT"]) if pd.notna(row["STT"]) else True
#             delivery_status = int(row["ĐÃ GIAO"]) if pd.notna(row["ĐÃ GIAO"]) and str(row["ĐÃ GIAO"]).isdigit() else 0

#             request = Request(
#                 name=name,
#                 start_place=start_place,
#                 end_place=end_place,
#                 weight=weight,
#                 date=date,
#                 timeframe=timeframe,
#                 note=note,
#                 staff_id=staff_id,
#                 split_id=split_id
#             )
#             request.delivery_status = delivery_status
#             requests.append(request)
#         except Exception as e:
#             print(f"Lỗi khi xử lý hàng {index + 5}: {e}")

#     return requests

# if __name__ == "__main__":
#     try:
#         df = read_excel_file()
#         requests = convert_to_object(df)
#         print("\nDanh sách các đối tượng Request:")
#         for i, req in enumerate(requests[:5]):
#             print(f"Request {i + 1}:")
#             print(f"  Name: {req.name}")
#             print(f"  Start Place: {req.start_place}")
#             print(f"  End Place: {req.end_place}")
#             print(f"  Weight: {req.weight}")
#             print(f"  Date: {req.date}")
#             print(f"  Timeframe: {req.timeframe}")
#             print(f"  Note: {req.note}")
#             print(f"  Staff ID: {req.staff_id}")
#             print(f"  Split ID: {req.split_id}")
#             print(f"  Delivery Status: {req.delivery_status}")
#             print(f"  Request ID: {req.request_id}")
#     except Exception as e:
#         print(f"Lỗi: {e}")
import csv
import os
from typing import List

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from config import *
from objects.request import Request


def read_dropdown_info(
    excel_file,
    target_cell,
    dropdown_range,
    sheet1_name="Sheet1",
    sheet2_name="Sheet2",
):
    wb = load_workbook(excel_file, data_only=True)
    if sheet1_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet1_name}' không tồn tại trong file {excel_file}")
    ws1 = wb[sheet1_name]
    if "!" in dropdown_range:
        sheet2_name, range_str = dropdown_range.split("!")
    else:
        range_str = dropdown_range
    if sheet2_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet2_name}' không tồn tại trong file {excel_file}")
    ws2 = wb[sheet2_name]

    dropdown_values = []
    address_map = {}
    for cell in ws2[range_str]:
        for c in cell:
            if c.value is not None:
                dropdown_values.append(c.value)
                col_num = c.column + 1
                col_letter = get_column_letter(col_num)
                address_cell = ws2[f"{col_letter}{c.row}"]
                address_map[c.value] = address_cell.value or "Không có địa chỉ"

    target = ws1[target_cell]
    current_value = target.value
    if current_value in dropdown_values:
        index = dropdown_values.index(current_value)
        address = address_map.get(current_value, "Không có địa chỉ")
    else:
        index = -1
        address = "N/A"

    return {
        "cell": target.coordinate,
        "value": current_value,
        "dropdown_list": dropdown_values,
        "index_in_dropdown": index,
        "address": address,
    }


def read_excel_file():
    file_path = os.path.join("Lenh_Dieu_Xe.xlsx")
    wb = load_workbook(file_path, data_only=True)
    sheet_name = TODAY
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet_name}' không tồn tại trong file {file_path}")
    ws = wb[sheet_name]

    headers = [
        cell.value.strip() if isinstance(cell.value, str) else cell.value
        for cell in ws["A4":"K4"][0]
    ]
    data = []
    row_index = 5
    while True:
        row = [cell.value for cell in ws[f"A{row_index}":f"K{row_index}"][0]]
        if pd.isna(row[1]) or row[1] is None:
            break
        data.append(row)
        row_index += 1

    df = pd.DataFrame(data, columns=headers)

    DROP_DOWN_EXT = "_DROP_DOWN_ID"
    dropdown_columns = {
        "KHÁCH HÀNG": DROP_DOWN_RANGE_DIA_CHI,
        "LOẠI XE": "CONFIG!F1:F6",
        "THỜI GIAN GIAO HÀNG": "CONFIG!AA1:AA5",
        "NV KẾ HOẠCH": "CONFIG!B3:B7",
        "THU TIỀN LUÔN": "CONFIG!AB1:AB2",
        "XUÁT HÓA ĐƠN": "CONFIG!AB1:AB2",
        "ĐÃ GIAO": "CONFIG!AB1:AB2",
        "NƠI BỐC HÀNG": "Dia_Chi!A1:A6",
    }

    for column_name in dropdown_columns.keys():
        if column_name in df.columns:
            df[column_name + DROP_DOWN_EXT] = None

    if "STT" in df.columns:
        df["STT"] = df["STT"].apply(
            lambda x: x.split()[1]
            if isinstance(x, str) and len(x.split()) > 1
            else (x.split()[0] if isinstance(x, str) and len(x.split()) > 0 else x)
        )

    errors = []
    for index, row in df.iterrows():
        missing_cols = [
            col for col in df.columns if col != df.columns[1] and pd.isna(row[col])
        ]
        if missing_cols:
            errors.append(
                f"Hàng {index + 5} thiếu dữ liệu ở cột: {', '.join(missing_cols)}"
            )

    if errors:
        print("\n⚠️ Các trường trống được phát hiện:")
        for error in errors:
            print(error)
    else:
        print("\n✅ Không có trường nào trống ngoài cột B dùng để dừng.")

    column_to_position = {name: chr(65 + i) for i, name in enumerate(headers)}
    for index, row in df.iterrows():
        for column_name, dropdown_range in dropdown_columns.items():
            if column_name in df.columns and row[column_name]:
                result = read_dropdown_info(
                    excel_file=file_path,
                    target_cell=f"{column_to_position[column_name]}{index + 5}",
                    dropdown_range=dropdown_range,
                    sheet1_name=sheet_name,
                )
                df.at[index, column_name + DROP_DOWN_EXT] = result["index_in_dropdown"]

    return df


def convert_to_object(df: pd.DataFrame) -> List[Request]:
    DROP_DOWN_EXT = "_DROP_DOWN_ID"
    dropdown_columns = [
        "KHÁCH HÀNG",
        "LOẠI XE",
        "THỜI GIAN GIAO HÀNG",
        "NƠI BỐC HÀNG",
        "NV KẾ HOẠCH",
        "THU TIỀN LUÔN",
        "XUÁT HÓA ĐƠN",
        "ĐÃ GIAO",
    ]

    # Danh sách khung giờ từ full_range_time
    full_range_time = [
        "S(08:00->12:00)",
        "C(13:30->17:30)",
        "T(19:00->23:00)",
        "D(00:30->04:30)",
        "Báo sau",
    ]
    # Ánh xạ chỉ số thành giờ bắt đầu và giờ kết thúc
    time_mapping = {
        0: [8, 12],  # S(08:00->12:00)
        1: [13, 17],  # C(13:30->17:30)
        2: [19, 23],  # T(19:00->23:00)
        3: [0, 4],  # D(00:30->04:30)
        4: [0, 0],  # Báo sau (giả định không có khung giờ cụ thể)
    }

    print("\nDữ liệu trước khi gán và xóa:")
    print(df.head())

    for column_name in dropdown_columns:
        if column_name in df.columns and column_name + DROP_DOWN_EXT in df.columns:
            df[column_name] = df[column_name + DROP_DOWN_EXT]

    drop_columns = [col for col in df.columns if DROP_DOWN_EXT in col]
    df = df.drop(columns=drop_columns)

    print("\nDữ liệu sau khi gán và xóa các cột _DROP_DOWN_ID:")
    print(df.head())
    print("\nDanh sách cột sau khi xử lý:")
    print(df.columns.tolist())

    requests = []
    for index, row in df.iterrows():
        try:
            print(f"\nHàng {index + 5}:")
            print(row)

            name = str(row["KHÁCH HÀNG"]) if pd.notna(row["KHÁCH HÀNG"]) else ""
            start_place = (
                [int(row["NƠI BỐC HÀNG"])]
                if pd.notna(row["NƠI BỐC HÀNG"]) and str(row["NƠI BỐC HÀNG"]).isdigit()
                else [0]
            )
            end_place = (
                [int(row["KHÁCH HÀNG"])]
                if pd.notna(row["KHÁCH HÀNG"]) and str(row["KHÁCH HÀNG"]).isdigit()
                else [0]
            )
            weight = (
                int(row["THỂ TÍCH (M3)"])
                if pd.notna(row["THỂ TÍCH (M3)"])
                and str(row["THỂ TÍCH (M3)"]).replace(".", "").isdigit()
                else 0
            )
            date = str(TODAY)
            # Ánh xạ timeframe từ full_range_time
            timeframe_idx = (
                int(row["THỜI GIAN GIAO HÀNG"])
                if pd.notna(row["THỜI GIAN GIAO HÀNG"])
                and str(row["THỜI GIAN GIAO HÀNG"]).isdigit()
                else 4
            )  # Mặc định là "Báo sau"
            timeframe = time_mapping.get(
                timeframe_idx, [0, 0]
            )  # Lấy khung giờ từ mapping, mặc định [0, 0] nếu không hợp lệ
            note = str(row["GHI CHÚ"]) if pd.notna(row["GHI CHÚ"]) else "."
            staff_id = (
                int(row["NV KẾ HOẠCH"])
                if pd.notna(row["NV KẾ HOẠCH"]) and str(row["NV KẾ HOẠCH"]).isdigit()
                else 0
            )
            split_id = bool(row["STT"]) if pd.notna(row["STT"]) else True
            delivery_status = (
                int(row["ĐÃ GIAO"])
                if pd.notna(row["ĐÃ GIAO"]) and str(row["ĐÃ GIAO"]).isdigit()
                else 0
            )

            request = Request(
                name=name,
                start_place=start_place,
                end_place=end_place,
                weight=weight,
                date=date,
                timeframe=timeframe,
                note=note,
                staff_id=staff_id,
                split_id=split_id,
            )
            request.delivery_status = delivery_status
            requests.append(request)
        except Exception as e:
            print(f"Lỗi khi xử lý hàng {index + 5}: {e}")

    return requests


if __name__ == "__main__":
    try:
        df = read_excel_file()
        requests = convert_to_object(df)
        print("\nDanh sách các đối tượng Request:")
        for i, req in enumerate(requests[:5]):
            print(f"Request {i + 1}:")
            print(f"  Name: {req.name}")
            print(f"  Start Place: {req.start_place}")
            print(f"  End Place: {req.end_place}")
            print(f"  Weight: {req.weight}")
            print(f"  Date: {req.date}")
            print(f"  Timeframe: {req.timeframe}")
            print(f"  Note: {req.note}")
            print(f"  Staff ID: {req.staff_id}")
            print(f"  Split ID: {req.split_id}")
            print(f"  Delivery Status: {req.delivery_status}")
            print(f"  Request ID: {req.request_id}")
    except Exception as e:
        print(f"Lỗi: {e}")
