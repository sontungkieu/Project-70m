from copy import copy

from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation


def copy_excel_sheet_fully(
    file_path="Lenh_Dieu_Xe.xlsx",
    origin_sheet="Sheet1",
    sheet_name="NewSheet",
    skip_cf=False,
):
    try:
        # Load file Excel
        wb = load_workbook(file_path)

        # Kiểm tra xem origin_sheet có tồn tại không
        if origin_sheet not in wb.sheetnames:
            raise ValueError(f"Sheet '{origin_sheet}' không tồn tại trong file Excel")

        # Lấy sheet gốc
        source_sheet = wb[origin_sheet]

        # Tạo sheet mới
        if sheet_name in wb.sheetnames:
            wb.remove(wb[sheet_name])  # Xóa sheet cũ nếu đã tồn tại
        target_sheet = wb.create_sheet(sheet_name)

        # Copy tất cả các ô giữ nguyên format
        for row in source_sheet.rows:
            for cell in row:
                new_cell = target_sheet[cell.coordinate]
                new_cell.value = cell.value

                # Copy định dạng
                if cell.has_style:
                    new_cell.font = copy(cell.font)
                    new_cell.border = copy(cell.border)
                    new_cell.fill = copy(cell.fill)
                    new_cell.number_format = copy(cell.number_format)
                    new_cell.protection = copy(cell.protection)
                    new_cell.alignment = copy(cell.alignment)

                # Copy comment/note
                if cell.comment:
                    new_cell.comment = copy(cell.comment)

        # Copy chiều rộng cột (đã sửa lỗi cú pháp)
        for col in source_sheet.column_dimensions:
            target_sheet.column_dimensions[col].width = source_sheet.column_dimensions[
                col
            ].width
            target_sheet.column_dimensions[col].hidden = source_sheet.column_dimensions[
                col
            ].hidden

        # Copy chiều cao hàng và trạng thái ẩn
        for row in source_sheet.row_dimensions:
            target_sheet.row_dimensions[row].height = source_sheet.row_dimensions[
                row
            ].height
            target_sheet.row_dimensions[row].hidden = source_sheet.row_dimensions[
                row
            ].hidden

        # Copy merged cells
        for merged_range in source_sheet.merged_cells.ranges:
            target_sheet.merge_cells(str(merged_range))

        # Copy filter
        if source_sheet.auto_filter.ref:
            target_sheet.auto_filter.ref = source_sheet.auto_filter.ref

        # Copy freeze panes
        if source_sheet.freeze_panes:
            target_sheet.freeze_panes = source_sheet.freeze_panes

        # Copy conditional formatting (nếu không skip)
        if not skip_cf:
            from openpyxl.formatting.rule import Rule
            from openpyxl.styles.differential import DifferentialStyle

            for cf in source_sheet.conditional_formatting:
                for cell_range in cf.cells:
                    range_string = str(cell_range)
                    for rule in cf.rules:
                        if hasattr(rule, "dxf") and rule.dxf:
                            dxf = DifferentialStyle(
                                font=copy(rule.dxf.font) if rule.dxf.font else None,
                                border=copy(rule.dxf.border)
                                if rule.dxf.border
                                else None,
                                fill=copy(rule.dxf.fill) if rule.dxf.fill else None,
                                alignment=copy(rule.dxf.alignment)
                                if rule.dxf.alignment
                                else None,
                            )
                        else:
                            dxf = None

                        new_rule = Rule(
                            type=rule.type,
                            dxf=dxf,
                            formula=rule.formula if hasattr(rule, "formula") else None,
                            stopIfTrue=rule.stopIfTrue
                            if hasattr(rule, "stopIfTrue")
                            else None,
                            priority=rule.priority
                            if hasattr(rule, "priority")
                            else None,
                            operator=rule.operator
                            if hasattr(rule, "operator")
                            else None,
                            text=rule.text if hasattr(rule, "text") else None,
                        )
                        target_sheet.conditional_formatting.add(range_string, new_rule)

        # Copy data validation (bao gồm dropdown list) và cô lập tham chiếu
        for dv in source_sheet.data_validations.dataValidation:
            new_dv = DataValidation(
                type=dv.type,
                formula1=dv.formula1,
                formula2=dv.formula2 if dv.formula2 else None,
                allow_blank=dv.allow_blank if hasattr(dv, "allow_blank") else True,
                operator=dv.operator if hasattr(dv, "operator") else None,
            )
            new_dv.ranges = dv.ranges
            if dv.formula1 and isinstance(dv.formula1, str) and "!" in dv.formula1:
                ref_sheet, ref_range = dv.formula1.split("!")
                if ref_sheet.startswith("="):
                    ref_sheet = ref_sheet[1:]
                if ref_sheet in wb.sheetnames:
                    ref_values = []
                    for row in wb[ref_sheet][ref_range]:
                        for cell in row:
                            if cell.value:
                                ref_values.append(str(cell.value))
                    new_dv.formula1 = f'"{",".join(ref_values)}"'
            target_sheet.add_data_validation(new_dv)

        # Copy sheet properties
        target_sheet.sheet_properties.tabColor = source_sheet.sheet_properties.tabColor
        target_sheet.views = source_sheet.views

        # Lưu file
        wb.save(file_path)
        print(
            f"Đã copy sheet '{origin_sheet}' sang sheet mới '{sheet_name}' với mọi thuộc tính!"
        )

    except FileNotFoundError:
        print(f"Không tìm thấy file '{file_path}'")
    except Exception as e:
        print(f"Đã xảy ra lỗi: {str(e)}")


def copy_excel_sheet_with_format_and_filter(
    file_path="Lenh_Dieu_Xe.xlsx", origin_sheet="Sheet1", sheet_name="NewSheet"
):
    try:
        # Load file Excel
        wb = load_workbook(file_path)

        # Kiểm tra xem origin_sheet có tồn tại không
        if origin_sheet not in wb.sheetnames:
            raise ValueError(f"Sheet '{origin_sheet}' không tồn tại trong file Excel")

        # Lấy sheet gốc
        source_sheet = wb[origin_sheet]

        # Tạo sheet mới
        if sheet_name in wb.sheetnames:
            wb.remove(wb[sheet_name])  # Xóa sheet cũ nếu đã tồn tại
        target_sheet = wb.create_sheet(sheet_name)

        # Copy tất cả các ô giữ nguyên format
        for row in source_sheet.rows:
            for cell in row:
                new_cell = target_sheet[cell.coordinate]
                new_cell.value = cell.value

                # Copy định dạng
                if cell.has_style:
                    new_cell.font = copy(cell.font)
                    new_cell.border = copy(cell.border)
                    new_cell.fill = copy(cell.fill)
                    new_cell.number_format = copy(cell.number_format)
                    new_cell.protection = copy(cell.protection)
                    new_cell.alignment = copy(cell.alignment)

        # Copy chiều rộng cột
        for col in source_sheet.column_dimensions:
            target_sheet.column_dimensions[col].width = source_sheet.column_dimensions[
                col
            ].width

        # Copy chiều cao hàng
        for row in source_sheet.row_dimensions:
            target_sheet.row_dimensions[row].height = source_sheet.row_dimensions[
                row
            ].height

        # Copy merged cells
        for merged_range in source_sheet.merged_cells.ranges:
            target_sheet.merge_cells(str(merged_range))

        # Copy filter (bộ lọc)
        if source_sheet.auto_filter.ref:
            target_sheet.auto_filter.ref = source_sheet.auto_filter.ref

        # Lưu file
        wb.save(file_path)
        print(
            f"Đã copy sheet '{origin_sheet}' sang sheet mới '{sheet_name}' với định dạng và filter nguyên vẹn!"
        )

    except FileNotFoundError:
        print(f"Không tìm thấy file '{file_path}'")
    except Exception as e:
        print(f"Đã xảy ra lỗi: {str(e)}")


# Ví dụ sử dụng:
# copy_excel_sheet_with_format_and_filter("Lenh_Dieu_Xe.xlsx", "Sheet1", "CopiedSheet")

# Ví dụ sử dụng:
if __name__ == "__main__":
    copy_excel_sheet_with_format_and_filter("Lenh_Dieu_Xe.xlsx", "Template", "3.4")
    # copy_excel_sheet_with_format_and_filter("Lenh_Dieu_Xe.xlsx", "3.3", "3.11")
    # copy_excel_sheet_with_format_and_filter("Lenh_Dieu_Xe.xlsx", "3.3", "3.12")
