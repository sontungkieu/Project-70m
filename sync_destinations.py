import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.datavalidation import DataValidation


def sync_csv_to_excel(
    csv_file, excel_file, sheet2_name="Dia_Chi", sheet1_range="A2:A12"
):
    # Đọc file CSV
    df = pd.read_csv(csv_file)

    # Load file Excel hiện có
    wb = load_workbook(excel_file)

    # Truy cập Sheet2
    if sheet2_name not in wb.sheetnames:
        ws2 = wb.create_sheet(sheet2_name)
    else:
        ws2 = wb[sheet2_name]

    # Xóa dữ liệu cũ trong Sheet2 (nếu có)
    ws2.delete_rows(1, ws2.max_row)

    # Điền dữ liệu từ CSV vào Sheet2 (cột A: Name, cột B: Address)
    for row, (name, address) in enumerate(zip(df["Name"], df["Address"]), start=1):
        ws2[f"A{row}"] = name
        ws2[f"B{row}"] = address

    # Truy cập Sheet1 để cập nhật drop-down list
    ws1 = wb["Sheet1"]

    if ws1.data_validations is None:
        try:
            from openpyxl.worksheet.datavalidation import DataValidationList

            ws1.data_validations = DataValidationList()
        except ImportError as e:
            print(f"Error importing DataValidationList: {e}")
            return  # Or raise the exception if you want to halt execution

    # Xóa data validation cũ (nếu có)
    ws1.data_validations.dataValidation = []  # Xóa danh sách validation cũ

    # Tạo drop-down list mới dựa trên số dòng trong CSV
    num_rows = len(df)
    dv = DataValidation(
        type="list", formula1=f"{sheet2_name}!$A$1:$A${num_rows}", allow_blank=True
    )
    dv.add(sheet1_range)  # Áp dụng cho vùng A2:A12 (hoặc tùy chỉnh)

    # Thêm data validation vào Sheet1
    ws1.add_data_validation(dv)

    # Lưu file Excel
    wb.save(excel_file)
    print(
        f"Đã đồng bộ dữ liệu từ {csv_file} vào {excel_file}, Sheet2 và cập nhật drop-down list!"
    )


def excel_sheet2_to_csv(excel_file, csv_file, sheet2_name="Dia_Chi"):
    # Load file Excel
    wb = load_workbook(excel_file, read_only=True)

    # Truy cập Sheet2
    if sheet2_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet2_name}' không tồn tại trong file {excel_file}")
    ws2 = wb[sheet2_name]

    # Lấy dữ liệu từ Sheet2
    data = []
    for row in ws2.iter_rows(min_row=1, max_col=2, values_only=True):
        if row[0] is not None:  # Chỉ lấy hàng có dữ liệu ở cột A
            data.append({"Name": row[0], "Address": row[1] if row[1] else ""})

    if not data:
        raise ValueError(f"Sheet2 trong {excel_file} không có dữ liệu!")

    # Tạo DataFrame và thêm cột ID
    df = pd.DataFrame(data)
    df.insert(0, "ID", range(1, len(df) + 1))  # Thêm cột ID từ 1

    # Lưu vào file CSV
    df.to_csv(csv_file, index=False, encoding="utf-8")
    print(f"Đã chuyển dữ liệu từ {excel_file}, Sheet2 sang {csv_file}!")


# # Sử dụng hàm
# excel_file = "kcn_dropdown.xlsx"
# csv_file = "destinations_output.csv"
# excel_sheet2_to_csv(excel_file, csv_file)


# Sử dụng hàm
csv_file = "data/destinations.csv"
excel_file = "kcn_dropdown.xlsx"
sync_csv_to_excel(csv_file, excel_file)
