# Sử dụng Python 3.10 làm môi trường chính
FROM python:3.10

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép toàn bộ code vào thư mục làm việc
COPY . .

# Cài đặt các thư viện từ file requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Mở cổng 8080 (dùng nếu chạy server Flask)
EXPOSE 8080

# Chạy ứng dụng Flask
CMD ["python", "app.py"]
