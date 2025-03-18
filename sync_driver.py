from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill


def initialize_driver_timetable(file_path="Lenh_Dieu_Xe.xlsx"):
    # Kiểm tra file tồn tại hay không
    try:
        wb = load_workbook(file_path)
    except FileNotFoundError:
        wb = Workbook()  # Nếu không có file, tạo mới workbook

    # Kiểm tra sheet "Driver_Timetable" có tồn tại không
    if "Driver_Timetable" not in wb.sheetnames:
        # Nếu không có, tạo mới sheet
        ws = wb.create_sheet("Driver_Timetable")
        # Nếu đây là file mới, xóa sheet mặc định
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])
    else:
        # Nếu có, lấy sheet hiện có
        ws = wb["Driver_Timetable"]

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

    # Chỉnh độ rộng cột
    ws.column_dimensions["A"].width = 20  # Cột A: 20 units
    ws.column_dimensions["B"].width = 15  # Cột B: 15 units
    for col in range(3, 51):  # Từ cột C đến AX
        if col <= 26:
            col_letter = chr(64 + col)
        else:
            col_letter = "A" + chr(64 + col - 26)
        ws.column_dimensions[col_letter].width = 3.5  # Khoảng 25 pixel

    # Định nghĩa màu
    yellow_fill = PatternFill(
        start_color="FFFF00", end_color="FFFF00", fill_type="solid"
    )  # Màu vàng
    orange_fill = PatternFill(
        start_color="FFA500", end_color="FFA500", fill_type="solid"
    )  # Màu cam

    # Tô màu từ hàng 3 trở đi cho các cột C, O, AA, AM (vàng) và N, Z, AL, AX (cam)
    for row in range(3, 101):  # Từ hàng 3 đến hàng 100
        ws[f"C{row}"].fill = yellow_fill  # Cột C
        ws[f"O{row}"].fill = yellow_fill  # Cột O
        ws[f"AA{row}"].fill = yellow_fill  # Cột AA
        ws[f"AM{row}"].fill = yellow_fill  # Cột AM

        ws[f"N{row}"].fill = orange_fill  # Cột N
        ws[f"Z{row}"].fill = orange_fill  # Cột Z
        ws[f"AL{row}"].fill = orange_fill  # Cột AL
        ws[f"AX{row}"].fill = orange_fill  # Cột AX

    # Lưu file
    wb.save(file_path)
    print(f"Đã khởi tạo Driver_Timetable trong {file_path}")


# Gọi hàm với đường dẫn file
if __name__ == "__main__":
    initialize_driver_timetable("Lenh_Dieu_Xe.xlsx")
