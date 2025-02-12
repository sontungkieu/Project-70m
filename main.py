# # import subprocess
# # from time import perf_counter
# # import psutil
# # from datetime import datetime

# # def run_test_bo_doi_cong_nghiep():
# #     tin = perf_counter()
# #     process = subprocess.Popen(['python', 'test_bo_doi_cong_nghiep.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# #     memory_usage = 0

# #     while process.poll() is None:
# #         memory_info = psutil.Process(process.pid).memory_info()
# #         memory_usage = max(memory_usage, memory_info.rss)  # Get the peak memory usage

# #     stdout, stderr = process.communicate()

# #     # Get current date and time for filenames
# #     current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# #     # Create filenames with current date and time
# #     stdout_filename = f"stdout_output_{current_time}.txt"
# #     stderr_filename = f"stderr_output_{current_time}.txt"

# #     # Save the output to these files
# #     with open(stdout_filename, 'wb') as stdout_file:
# #         stdout_file.write(stdout)
# #     with open(stderr_filename, 'wb') as stderr_file:
# #         stderr_file.write(stderr)

# #     return perf_counter() - tin, memory_usage, stderr

# # def check():
# #     #read config file
# #     import ast
# #     with open('stderr_output.txt', 'r') as file:
# #         config_str = file.read()
# #         config = ast.literal_eval(config_str)
    
# #     print(config)


# #     #read output file
    
# #     #read query files

# #     #check if the output is correct

# # if __name__ == "__main__":
# #     run_time, memory_usage, stderr = run_test_bo_doi_cong_nghiep()
# #     print(f"ORTools run in {run_time:.2f}s")
# #     print(f"Peak memory usage: {memory_usage / (1024 * 1024):.2f} MB")
# #     print(f"Config: {stderr}")
# #     # intel i5-9300H 4 cores - 8 threads, 16GB RAM, 145.43666220002342s


# # """
# import subprocess
# from time import perf_counter

# def run_test_bo_doi_cong_nghiep():
#     tin = perf_counter()
#     # Run the test_bo_doi_cong_nghiep.py script and redirect stdout and stderr to separate files
#     with open('stdout_output.txt', 'w') as stdout_file, open('stderr_output.txt', 'w') as stderr_file:
#         subprocess.run(['python', 'test_bo_doi_cong_nghiep.py'], stdout=stdout_file, stderr=stderr_file)
#     return perf_counter() - tin

# if __name__ == "__main__":
#     run_time = run_test_bo_doi_cong_nghiep()
#     print(f"ORTools run in {run_time:.2f}s") 
#     # intel i5-9300H 4 cores - 8 threads, 16GB RAM, 145.43666220002342s

# # """
import subprocess
from time import perf_counter
import psutil
from datetime import datetime
import ast
import os

config = []
def run_test_bo_doi_cong_nghiep():
    tin = perf_counter()
    
    # Lấy thời gian hiện tại và tạo tên file
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if not os.path.exists('data'):
        os.makedirs('data')
    stdout_filename = f"data/stdout_output_{current_time}.txt"
    config_filename = f"data/config_{current_time}.txt"

    # Chạy process và ghi stdout + config (thay vì stderr)
    with open(stdout_filename, 'wb') as stdout_file, open(config_filename, 'wb') as config_file:
        process = subprocess.Popen(['python', 'test_bo_doi_cong_nghiep.py'], 
                                   stdout=stdout_file, stderr=config_file)
    
        memory_usage = 0

        while process.poll() is None:  # Kiểm tra nếu tiến trình vẫn đang chạy
            try:
                memory_info = psutil.Process(process.pid).memory_info()
                memory_usage = max(memory_usage, memory_info.rss)  # Lưu mức sử dụng bộ nhớ cao nhất
            except psutil.NoSuchProcess:
                break  # Quá trình đã kết thúc, thoát vòng lặp

        process.wait()  # Đảm bảo tiến trình đã kết thúc hoàn toàn

    return perf_counter() - tin, memory_usage, stdout_filename, config_filename

def read_config(config_filename):
    global config
    try:
        # Đọc file config
        with open(config_filename, 'r', encoding='utf-8') as file:
            config_str = file.read()

        # Chuyển đổi nội dung file sang dictionary
        config = ast.literal_eval(config_str)

        print("Config đọc được:", config)
        return config

    except (SyntaxError, ValueError):
        print("Lỗi: Nội dung file config không hợp lệ!")
        return None
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {config_filename}!")
        return None

def read_output(output_filename):
    try:
        with open(output_filename, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {output_filename}!")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc file {output_filename}: {e}")
        return None


def read_requests(config):
    NUM_OF_DAY_REPETION = config['NUM_OF_DAY_REPETION']
    requests_files = []
    for i in range(NUM_OF_DAY_REPETION):
        request_filename = f"data/requests{i}.txt"
        try:
            with open(request_filename, 'r', encoding='utf-8') as file:
                requests_files.append(file.read())
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file {request_filename}!")
        except Exception as e:
            print(f"Lỗi khi đọc file {request_filename}: {e}")
    return requests_files

def check(output, queries, config):
    print(output[:1000])
    

if __name__ == "__main__":
    run_time, memory_usage, stdout_filename, config_filename = run_test_bo_doi_cong_nghiep()

    #sau khi chạy
    config_data = check(config_filename)
    output_data = read_output(stdout_filename)
    requests_data = read_requests(config_data)

    # print(f"""ORTools run in {run_time:.2f}s
    #          with config: 
    #             NUM_OF_VEHICLES {config['NUM_OF_VEHICLES']} days,
    #             NUM_OF_NODES {config['NUM_OF_NODES']} days,
    #             NUM_OF_REQUEST_PER_DAY {config['NUM_OF_REQUEST_PER_DAY']} days,
    #             NUM_OF_DAY_REPETION {config['NUM_OF_DAY_REPETION']} days,
    #             """)
    print(f"""ORTools run in {run_time:.2f}s, with config: {config_data}""")
    print(f"Peak memory usage: {memory_usage / (1024 * 1024):.2f} MB")
    print(f"Output saved to: {stdout_filename}")
    print(f"Config saved to: {config_filename}")

    # Kiểm tra 
    check(output_data, requests_data, config_data)


"""
intel i5-9300H 4 cores - 8 threads, 16GB RAM, 
------------------------------------
ORTools run in 121.94s
Peak memory usage: 105.82 MB
------------------------------------
ORTools run in 111.54s
Peak memory usage: 104.83 MB
Output saved to: stdout_output_2025-02-12_10-31-06.txt, stderr_output_2025-02-12_10-31-06.txt
------------------------------------

"""