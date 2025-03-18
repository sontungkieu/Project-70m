from openpyxl import Workbook
from openpyxl.styles import PatternFill

# Tạo workbook mới
wb = Workbook()
ws = wb.active

# Gộp ô từ A1 đến AX1
ws.merge_cells("A1:AX1")
ws["A1"] = "Dữ liệu gộp từ A1 đến AX1"

# Gộp các ô ở hàng 2
ws.merge_cells("C2:N2")
ws["C2"] = "Gộp 1"

ws.merge_cells("O2:Z2")
ws["O2"] = "Gộp 2"

ws.merge_cells("AA2:AL2")
ws["AA2"] = "Gộp 3"

ws.merge_cells("AM2:AX2")
ws["AM2"] = "Gộp 4"

# Chỉnh độ rộng cột từ C đến AX thành 25
for col in range(3, 51):
    if col <= 26:
        col_letter = chr(64 + col)
    else:
        col_letter = "A" + chr(64 + col - 26)
    ws.column_dimensions[col_letter].width = 2

# Định nghĩa màu
yellow_fill = PatternFill(
    start_color="FFFF00", end_color="FFFF00", fill_type="solid"
)  # Màu vàng
orange_fill = PatternFill(
    start_color="FFA500", end_color="FFA500", fill_type="solid"
)  # Màu cam

# Đặt màu cho các ô ở hàng 2
ws["C2"].fill = yellow_fill  # Cột C
ws["N2"].fill = orange_fill  # Cột N
ws["O2"].fill = yellow_fill  # Cột O
ws["Z2"].fill = orange_fill  # Cột Z
ws["AA2"].fill = yellow_fill  # Cột AA
ws["AL2"].fill = orange_fill  # Cột AL
ws["AM2"].fill = yellow_fill  # Cột AM
ws["AX2"].fill = orange_fill  # Cột AX

# Lưu file
wb.save("merge_a1_ax1.xlsx")
