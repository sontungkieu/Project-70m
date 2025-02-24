import pandas as pd
import os

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
        df_new['STT'][index] = index
        df_new['THU TIỀN LUÔN'][index] = 0
        df_new["XUÁT HÓA ĐƠN"][index] = 0
    
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


else:
    print("Sheet không có đủ 2 hàng để hiển thị.")
