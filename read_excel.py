import pandas as pd
import os

from objects.request import Request
from config import *
id = {}

# Đường dẫn đến file Excel (thay đổi nếu cần)
file_path = os.path.join("data", "input", "Lenh_Dieu_Xe.xlsx")

# Đọc file Excel
xls = pd.ExcelFile(file_path)

# Lấy tên của sheet đầu tiên
first_sheet = xls.sheet_names[0]

# Đọc nội dung của sheet đầu tiên
df = pd.read_excel(xls, sheet_name=first_sheet)

# In hàng thứ 2 (chỉ số 1 trong DataFrame)
if len(df) > 2:  # Kiểm tra xem có ít nhất 2 hàng không
    print(f"Hàng thứ 2 trong sheet '{first_sheet}':")
    print("+-----------------+")
    for i in range(10):
        print(f'"{df.iloc[2,i]}",',end="")  
        # print("+-----------------+")
    print()
    col = ["STT","TÊN HÀNG","THỂ TÍCH (M3)","LOẠI XE","THỜI GIAN GIAO HÀNG","GHI CHÚ","NƠI BỐC HÀNG","NV KẾ HOẠCH","THU TIỀN LUÔN","XUÁT HÓA ĐƠN"]
    new_header = df.iloc[2,:10]  # Lấy hàng thứ 2 làm tiêu đề cột
    df_new = df.iloc[3:,:10].copy()   # Lấy dữ liệu từ hàng thứ 3 trở đi
    df_new.columns = new_header  # Gán tiêu đề mới
    df_new.reset_index(drop=True, inplace=True)  
    print(df_new.head())
    print("+-----------------+")
    for i in range(10):
        print(df_new.iloc[2,i])  
        print("+-----------------+")
    

    valid_number_of_request = 0
    for index, row in df_new.iterrows():
        if row.isnull().all():
            break
        valid_number_of_request = index
        # valid_data.append(row.to_dict())
        df_new.loc[index, 'STT'] = index
        df_new.loc[index, 'THU TIỀN LUÔN'] = 0
        df_new.loc[index, 'XUÁT HÓA ĐƠN'] = 0

    
    errors = []
    for index, row in df_new.iterrows():
        if index>valid_number_of_request:
            break
        if row.isnull().sum() > 0:  # Nếu hàng có ít nhất một ô trống
            missing_cols = row[row.isnull()].index.tolist()  # Lấy danh sách cột bị thiếu dữ liệu
            errors.append(f"Đơn {row['STT']} thiếu cột {', '.join(missing_cols)}")
    # In thông báo lỗi nếu có hàng thiếu dữ liệu
    if errors:
        print("\n⚠️ Lỗi dữ liệu:")
        for error in errors:
            print(error)
    else:
        print("\n✅ Dữ liệu hợp lệ, không có lỗi.")
    for index,row in df_new.iterrows():
        new_request = Request(
            name = row['TÊN HÀNG'],
            start_place = row['NƠI BỐC HÀNG'],
            end_place = "depot",
            weight = row['THỂ TÍCH (M3)'],
            date = TODAY,
            timeframe = [0, 24],
            note = row['GHI CHÚ'],
            staff_id = id.get(row['NV KẾ HOẠCH'],99),
            split_id = 0
        )

#từ các ngày (các sheet) tạo ra file json để thuật toán chạy 

else:
    print("Sheet không có đủ 2 hàng để hiển thị.")
