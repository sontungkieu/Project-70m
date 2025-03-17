from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

# Tạo workbook
wb = Workbook()

# Tạo Sheet2 và điền dữ liệu mẫu
ws2 = wb.create_sheet("Dia_Chi")
ws1 = wb.active  # Sheet1 là sheet mặc định
ws1.title = "Sheet1"

# Dữ liệu mẫu cho Sheet2 (cột A: Tên KCN, cột B: Địa chỉ)
data = [
    ("KCN Hòa Khánh", "Đà Nẵng"),
    ("KCN VSIP", "Quảng Ngãi"),
    ("KCN Long Hậu", "Long An"),
    ("KCN Tân Bình", "TP.HCM"),
    ("KCN Bắc Thăng Long", "Hà Nội"),
]

# Điền dữ liệu vào Sheet2 và tính cột C
for row, (kcn, address) in enumerate(data, start=1):
    ws2[f"A{row}"] = kcn  # Cột A: Tên KCN
    ws2[f"B{row}"] = address  # Cột B: Địa chỉ
    ws2[f"C{row}"] = f"{kcn} - {address}"  # Cột C: KCN + Địa chỉ

# Tạo tiêu đề cho Sheet1
# ws1["A1"] = "Tên Khu Công Nghiệp"
# ws1["B1"] = "Địa chỉ"
ws1["A1"] = "Khách hàng"
# Tạo drop-down list cho cột A ở Sheet1 (dùng cột C từ Dia_Chi)
dv = DataValidation(type="list", formula1="Dia_Chi!$C$1:$C$5", allow_blank=True)
dv.add("A2:A10")  # Áp dụng cho A2:A10

# Thêm data validation vào Sheet1
ws1.add_data_validation(dv)

# Lưu file
wb.save("kcn_dropdown.xlsx")

print("File Excel đã được tạo!")
