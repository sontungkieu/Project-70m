from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

# Load file Excel thực tế
excel_file = "Lenh_Dieu_Xe.xlsx"
wb = load_workbook(excel_file)

# Truy cập sheet "Dia_Chi"
ws2 = wb["Dia_Chi"]

# Truy cập sheet "3.3" (Sheet1)
ws1 = wb["3.3"]

# Tính cột C trong sheet "Dia_Chi" (A + B)
max_row = ws2.max_row  # Lấy số dòng tối đa có dữ liệu trong sheet
for row in range(1, max_row + 1):
    kcn = ws2[f"A{row}"].value
    address = ws2[f"B{row}"].value
    if kcn and address:  # Chỉ thêm vào cột C nếu cả A và B có giá trị
        ws2[f"C{row}"] = f"{kcn} - {address}"
    elif kcn:  # Nếu chỉ có A, dùng A
        ws2[f"C{row}"] = kcn

# Tạo drop-down list cho A5:A55 trong sheet "3.3", dùng cột C từ "Dia_Chi"
dv = DataValidation(type="list", formula1="Dia_Chi!$C$1:$C$52", allow_blank=True)
dv.add("B5:B55")  # Áp dụng cho A5:A55

# Thêm data validation vào sheet "3.3"
ws1.add_data_validation(dv)

# Lưu file
wb.save("Lenh_Dieu_Xe_updated.xlsx")
print("File Excel đã được cập nhật với cột C và drop-down list!")
